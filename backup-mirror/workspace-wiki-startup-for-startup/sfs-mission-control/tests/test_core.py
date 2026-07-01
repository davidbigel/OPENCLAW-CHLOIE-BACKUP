from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from mission_control.config import Config, load_config
from mission_control.db import Store
from mission_control.service import MissionControlService
from mission_control.security import make_auth_token, verify_auth_token
from mission_control.snoracle_adapter import _build_openclaw_command, _build_prompt, _routes_to_current_agent
from mission_control.util import ms_to_timecode, tokenize
from mission_control.workers import load_raw_segments, run_obsidian_worker, run_raw_worker, run_wikillm_worker


def temp_config(root: Path) -> Config:
    app_root = APP_ROOT
    return Config(
        app_root=app_root,
        workspace_root=root,
        public_host="127.0.0.1",
        public_port=40006,
        public_scheme="http",
        public_tls_cert=None,
        public_tls_key=None,
        private_host="127.0.0.1",
        private_port=40007,
        public_password="3d20",
        cookie_secret="test-cookie-secret",
        internal_secret="test-internal-secret",
        snoracle_mode="local",
        snoracle_agent_id="wiki-startup-for-startup",
        snoracle_session_id=None,
        snoracle_route_label="agent:wiki-startup-for-startup:main",
        allowed_origins=("http://127.0.0.1:40006",),
        db_path=root / "kb" / "mission-control" / "mission-control.sqlite3",
        log_dir=root / "kb" / "mission-control" / "logs",
        answers_dir=root / "kb" / "mission-control" / "answers",
        static_dir=app_root / "static",
        wikillm_dir=root / "kb" / "wikillm",
        raw_dir=root / "kb" / "sources" / "raw",
        source_lists_dir=root / "kb" / "sources" / "lists",
    )


class CoreTests(unittest.TestCase):
    def test_tokenize_and_timecode(self) -> None:
        self.assertIn("gtm", tokenize("מה הקורפוס אומר על GTM ו-AI agents?"))
        self.assertEqual(ms_to_timecode(3723000), "01:02:03")

    def test_store_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("מה אומרים על AI?", {"wikillm": True, "obsidian": False, "raw": True})
            self.assertTrue(question_id.startswith("q_"))
            candidate_id = store.create_wiki_update_candidate(question_id, "test", {"page": "concepts/AI.md"})
            self.assertGreater(candidate_id, 0)
            job_id = store.create_wiki_patch_job(question_id, "test", {"page": "concepts/AI.md"})
            self.assertGreater(job_id, 0)
            response = store.get_question_response(question_id)
            self.assertIsNotNone(response)
            self.assertEqual(response["status"], "queued")
            self.assertIn("wikillm", response["sources_selected"])

    def test_recover_incomplete_questions_marks_orphans_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("recover me", {"wikillm": True})
            self.assertTrue(store.mark_question_running(question_id))
            run_id = store.create_source_run(question_id, "wikillm")
            recovered = store.recover_incomplete_questions()
            self.assertEqual(recovered, 1)
            response = store.get_question_response(question_id)
            self.assertEqual(response["status"], "failed")
            self.assertIn("restarted", response["error"])

    def test_snoracle_session_key_env_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(
                "os.environ",
                {
                    "MC_WORKSPACE_ROOT": tmp,
                    "MC_SNORACLE_SESSION_KEY": "agent:custom-agent:main",
                },
                clear=False,
            ):
                config = load_config()
                self.assertEqual(config.snoracle_agent_id, "custom-agent")
                self.assertEqual(config.snoracle_route_label, "agent:custom-agent:main")

    def test_runtime_secret_generation_and_default_openclaw_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"MC_WORKSPACE_ROOT": tmp}, clear=True):
                config = load_config()
                self.assertEqual(config.snoracle_mode, "openclaw")
                self.assertEqual(config.snoracle_agent_id, "main")
                self.assertEqual(config.snoracle_route_label, "agent:main:main")
                self.assertEqual(config.public_scheme, "http")
                self.assertNotEqual(config.cookie_secret, "sfs-mission-control-v1-cookie-secret")
                self.assertTrue((Path(tmp) / "kb" / "mission-control" / ".secrets.json").exists())

    def test_https_is_enabled_when_runtime_cert_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tls_dir = Path(tmp) / "kb" / "mission-control" / "tls"
            tls_dir.mkdir(parents=True)
            (tls_dir / "public.crt").write_text("crt", encoding="utf-8")
            (tls_dir / "public.key").write_text("key", encoding="utf-8")
            with patch.dict("os.environ", {"MC_WORKSPACE_ROOT": tmp}, clear=True):
                config = load_config()
                self.assertEqual(config.public_scheme, "https")
                self.assertEqual(config.public_tls_cert, tls_dir / "public.crt")
                self.assertEqual(config.public_tls_key, tls_dir / "public.key")
                self.assertIn("https://127.0.0.1:40006", config.allowed_origins)

    def test_runtime_session_uuid_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session_id = "513c0c28-605d-44a8-b5fb-1138341b98eb"
            with patch.dict(
                "os.environ",
                {"MC_WORKSPACE_ROOT": tmp, "MC_SNORACLE_SESSION_ID": session_id},
                clear=True,
            ):
                config = load_config()
                self.assertEqual(config.snoracle_session_id, session_id)
                self.assertEqual(config.snoracle_route_label, f"session-id:{session_id}")

    def test_auth_token_expiry(self) -> None:
        token = make_auth_token("3d20", "secret", issued_at=1000)
        self.assertTrue(verify_auth_token(token, "3d20", "secret", now=1200, max_age_seconds=500))
        self.assertFalse(verify_auth_token(token, "3d20", "secret", now=2000, max_age_seconds=500))
        self.assertFalse(verify_auth_token("v1:" + "0" * 64, "3d20", "secret", now=1200))

    def test_cancelled_question_cannot_be_finished(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("cancel me", {"wikillm": True})
            self.assertTrue(store.mark_question_running(question_id))
            self.assertTrue(store.request_cancel(question_id))
            finished = store.finish_question(
                question_id,
                {"summary_answer_markdown": "should not write", "boxes": {}, "labels": []},
                meaningful=False,
            )
            self.assertFalse(finished)
            self.assertEqual(store.get_question_response(question_id)["status"], "cancelled")

    def test_final_json_does_not_drop_sqlite_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("AI?", {"wikillm": True})
            store.mark_question_running(question_id)
            run_id = store.create_source_run(question_id, "wikillm")
            store.insert_evidence(
                question_id,
                run_id,
                [{"source_type": "wikillm", "title": "AI", "path": "kb/wikillm/concepts/AI.md", "excerpt": "AI", "rank": 1}],
            )
            store.finish_source_run(run_id, question_id, "wikillm", "used", "source answer")
            store.finish_question(
                question_id,
                {
                    "summary_answer_markdown": "summary",
                    "boxes": {"wikillm": {"selected": True, "status": "used", "answer_markdown": "final box", "evidence": []}},
                    "labels": ["Corpus"],
                },
                meaningful=True,
            )
            response = store.get_question_response(question_id)
            self.assertEqual(response["boxes"]["wikillm"]["answer_markdown"], "final box")
            self.assertEqual(len(response["boxes"]["wikillm"]["evidence"]), 1)

    def test_service_requires_at_least_one_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            service = MissionControlService(config, store)
            result = service.ask("מה קורה?", {})
            self.assertEqual(result["status"], "error")
            self.assertIn("source", result["message"])

    def test_empty_wiki_patch_payload_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            service = MissionControlService(config, store)
            question_id = store.create_question("patch", {"wikillm": True})
            job_id = store.create_wiki_patch_job(question_id, "test", {})
            claimed = store.claim_next_wiki_patch_job()
            self.assertIsNotNone(claimed)
            changed = service._write_wiki_patch_candidate(claimed)
            self.assertIsNone(changed)
            store.finish_wiki_patch_job(job_id, question_id, "skipped", "no actionable wiki patch payload", [])
            row = store.get_question_response(question_id)
            self.assertEqual(row["status"], "queued")

    def test_openclaw_command_uses_agent_route_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            command = _build_openclaw_command(config, "{}")
            self.assertIn("--agent", command)
            self.assertIn("wiki-startup-for-startup", command)
            self.assertNotIn("--session-id", command)

    def test_self_route_detection_matches_current_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            with patch.dict(
                "os.environ",
                {"CODEX_HOME": "/root/.openclaw/agents/wiki-startup-for-startup/agent/codex-home"},
                clear=False,
            ):
                self.assertTrue(_routes_to_current_agent(config))

    def test_self_route_detection_ignores_explicit_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            config = Config(**{**config.__dict__, "snoracle_session_id": "513c0c28-605d-44a8-b5fb-1138341b98eb"})
            with patch.dict(
                "os.environ",
                {"CODEX_HOME": "/root/.openclaw/agents/wiki-startup-for-startup/agent/codex-home"},
                clear=False,
            ):
                self.assertFalse(_routes_to_current_agent(config))

    def test_prompt_compaction_caps_large_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            large_text = "AI " * 5000
            result = run_wikillm_worker(config, "AI")
            result.answer_markdown = large_text
            result.evidence = [{"source_type": "raw", "title": "t", "excerpt": large_text, "rank": i} for i in range(80)]
            result.citations = list(result.evidence)
            prompt, meta = _build_prompt("q_1", "AI?", [result], {"boxes": {}, "labels": []})
            self.assertIn("worker_results", prompt)
            self.assertLess(meta["answer_char_limit"], 2401)
            self.assertLess(meta["evidence_sample_limit"], 25)

    def test_workers_on_temp_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = temp_config(root)
            (config.wikillm_dir / "concepts").mkdir(parents=True)
            (config.raw_dir).mkdir(parents=True)
            (config.source_lists_dir).mkdir(parents=True)
            (config.wikillm_dir / "concepts" / "AI.md").write_text("# AI agents\n\nCorpus: AI agents improve workflow.", encoding="utf-8")
            (config.source_lists_dir / "list.md").write_text(
                "# List\n\n### 1. Episode AI\n- Video ID: abc123\n",
                encoding="utf-8",
            )
            (config.raw_dir / "abc123.md").write_text(
                "# Raw\n\n## Raw Supadata Result\n\n{\n  \"content\": [\n    {\"text\": \"AI agents help teams\", \"offset\": 1000, \"duration\": 1000, \"lang\": \"iw\"}\n  ]\n}\n",
                encoding="utf-8",
            )
            self.assertEqual(len(load_raw_segments(config.raw_dir / "abc123.md")), 1)
            wiki = run_wikillm_worker(config, "AI agents")
            raw = run_raw_worker(config, "AI agents")
            obsidian = run_obsidian_worker(config, "AI agents")
            self.assertEqual(wiki.status, "used")
            self.assertEqual(raw.status, "used")
            self.assertEqual(obsidian.status, "unavailable")
            self.assertEqual(raw.evidence[0]["timecode"], "00:00:01")


if __name__ == "__main__":
    unittest.main()
