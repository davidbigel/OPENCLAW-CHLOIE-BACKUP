from __future__ import annotations

import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from mission_control.config import Config, load_config
from mission_control.db import Store
from mission_control.security import make_auth_token, verify_auth_token
from mission_control.service import MissionControlService
from mission_control.snoracle_adapter import (
    _build_action_prompt,
    _build_openclaw_command,
    _extract_json_payload,
    synthesize_answer,
)
from mission_control.util import ms_to_timecode, tokenize
from mission_control.workers import load_raw_segments, run_obsidian_worker, run_raw_worker, run_wikillm_worker


def temp_config(root: Path) -> Config:
    app_root = APP_ROOT
    return Config(
        app_root=app_root,
        workspace_root=root,
        public_host="127.0.0.1",
        public_port=40006,
        public_scheme="https",
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
        snoracle_route_label="agent:wiki-startup-for-startup:per-question",
        snoracle_timeout_seconds=300,
        allowed_origins=("https://127.0.0.1:40006",),
        db_path=root / "kb" / "mission-control" / "mission-control.sqlite3",
        log_dir=root / "kb" / "mission-control" / "logs",
        answers_dir=root / "kb" / "mission-control" / "answers",
        runs_dir=root / "kb" / "mission-control" / "runs",
        static_dir=app_root / "static",
        wikillm_dir=root / "kb" / "wikillm",
        raw_dir=root / "kb" / "sources" / "raw",
        source_lists_dir=root / "kb" / "sources" / "lists",
    )


def wait_for_question(store: Store, question_id: str, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        payload = store.get_question_response(question_id)
        if payload and payload["status"] in {"done", "failed", "cancelled"}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"question {question_id} did not finish")


class CoreTests(unittest.TestCase):
    def test_tokenize_and_timecode(self) -> None:
        self.assertIn("gtm", tokenize("מה הקורפוס אומר על GTM ו-AI agents?"))
        self.assertEqual(ms_to_timecode(3723000), "01:02:03")

    def test_store_lifecycle_and_agent_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("מה אומרים על AI?", {"wikillm": True, "obsidian": False, "raw": True})
            store.prepare_agent_run(
                question_id,
                agent_id="wiki-startup-for-startup",
                session_id="mc-test",
                session_key="agent:wiki-startup-for-startup:mission-control:q",
                stdout_path="/tmp/stdout",
                stderr_path="/tmp/stderr",
                raw_response_path="/tmp/raw",
            )
            store.finish_agent_run(question_id, exit_code=0, parse_status="parsed", raw_response_text='{"ok": true}')
            self.assertTrue(store.mark_question_running(question_id))
            finished = store.finish_question(
                question_id,
                {
                    "summary_answer_markdown": "summary",
                    "boxes": {"wikillm": {"selected": True, "status": "used", "answer_markdown": "box"}},
                    "labels": ["Corpus"],
                    "candidate": True,
                },
                meaningful=True,
            )
            self.assertTrue(finished)
            response = store.get_question_response(question_id)
            self.assertEqual(response["status"], "done")
            self.assertTrue(response["candidate"])
            self.assertFalse(response["digested"])
            self.assertEqual(response["parse_status"], "parsed")
            self.assertEqual(response["openclaw"]["session_id"], "mc-test")
            self.assertEqual(response["raw_response_text"], '{"ok": true}')

    def test_recover_incomplete_questions_marks_orphans_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("recover me", {"wikillm": True})
            self.assertTrue(store.mark_question_running(question_id))
            run_id = store.create_source_run(question_id, "wikillm")
            self.assertGreater(run_id, 0)
            recovered = store.recover_incomplete_questions()
            self.assertEqual(recovered, 1)
            response = store.get_question_response(question_id)
            self.assertEqual(response["status"], "failed")
            self.assertIn("restarted", response["error"])

    def test_runtime_secret_generation_and_default_openclaw_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"MC_WORKSPACE_ROOT": tmp}, clear=True):
                config = load_config()
                self.assertEqual(config.snoracle_mode, "openclaw")
                self.assertEqual(config.snoracle_agent_id, "wiki-startup-for-startup")
                self.assertEqual(config.snoracle_route_label, "agent:wiki-startup-for-startup:per-question")
                self.assertEqual(config.public_scheme, "https")
                self.assertNotIn("http://127.0.0.1:40006", config.allowed_origins)
                self.assertIn("https://127.0.0.1:40006", config.allowed_origins)
                self.assertTrue((Path(tmp) / "kb" / "mission-control" / ".secrets.json").exists())

    def test_runtime_agent_and_session_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(
                "os.environ",
                {
                    "MC_WORKSPACE_ROOT": tmp,
                    "MC_SNORACLE_AGENT_ID": "custom-agent",
                    "MC_SNORACLE_TIMEOUT_SECONDS": "123",
                },
                clear=True,
            ):
                config = load_config()
                self.assertEqual(config.snoracle_agent_id, "custom-agent")
                self.assertIsNone(config.snoracle_session_id)
                self.assertEqual(config.snoracle_route_label, "agent:custom-agent:per-question")
                self.assertEqual(config.snoracle_timeout_seconds, 123)

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

    def test_openclaw_command_uses_agent_and_per_question_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            command = _build_openclaw_command(config, "mc-session", "prompt")
            self.assertIn("--agent", command)
            self.assertIn("wiki-startup-for-startup", command)
            self.assertIn("--session-id", command)
            self.assertIn("mc-session", command)
            timeout_index = command.index("--timeout")
            self.assertEqual(command[timeout_index + 1], "300")
            self.assertEqual(command[-1], "--json")

    def test_action_prompt_is_short_and_delegates_contract_to_tools(self) -> None:
        prompt = _build_action_prompt(
            "q_1",
            "מה הקורפוס אומר על AI agents?",
            {"wikillm": True, "obsidian": False, "raw": True},
        )
        self.assertIn("TOOLS.md", prompt)
        self.assertIn("q_1", prompt)
        self.assertIn("wikillm: selected", prompt)
        self.assertLess(len(prompt), 1500)

    def test_extract_json_payload_handles_openclaw_wrappers(self) -> None:
        inner = {
            "question_id": "q_1",
            "status": "done",
            "summary_answer_markdown": "answer",
            "boxes": {},
        }
        wrapped = json_dumps_for_test({"payloads": [{"text": json_dumps_for_test(inner)}]})
        self.assertEqual(_extract_json_payload(wrapped)["summary_answer_markdown"], "answer")

    def test_adapter_local_mode_persists_raw_output_and_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            question_id = store.create_question("AI?", {"wikillm": True, "raw": False, "obsidian": False})
            payload = synthesize_answer(config, store, question_id, "AI?", {"wikillm": True, "raw": False, "obsidian": False})
            self.assertEqual(payload["status"], "done")
            response = store.get_question_response(question_id)
            self.assertEqual(response["parse_status"], "parsed")
            self.assertTrue(response["openclaw"]["session_id"].startswith("mc-q_"))
            self.assertIn(":explicit:", response["openclaw"]["session_key"])
            self.assertTrue(Path(response["raw_response_path"]).exists())
            self.assertIn("local-dev", response["raw_response_text"])

    def test_service_finishes_local_run_without_wiki_patch_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            service = MissionControlService(config, store)
            result = service.ask("מה קורה?", {"wikillm": True})
            self.assertEqual(result["status"], "running")
            response = wait_for_question(store, result["question_id"])
            self.assertEqual(response["status"], "done")
            self.assertFalse(response["candidate"])
            with sqlite3.connect(config.db_path) as con:
                count = con.execute("SELECT COUNT(*) FROM wiki_patch_jobs").fetchone()[0]
            self.assertEqual(count, 0)

    def test_service_requires_at_least_one_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = temp_config(Path(tmp))
            store = Store(config)
            store.init()
            service = MissionControlService(config, store)
            result = service.ask("מה קורה?", {})
            self.assertEqual(result["status"], "error")
            self.assertIn("source", result["message"])

    def test_static_assets_do_not_expose_gate_value(self) -> None:
        static_text = (APP_ROOT / "static" / "index.html").read_text(encoding="utf-8")
        static_text += (APP_ROOT / "static" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("?p=", static_text)
        self.assertNotIn("3d20", static_text)

    def test_workers_on_temp_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = temp_config(root)
            (config.wikillm_dir / "concepts").mkdir(parents=True)
            config.raw_dir.mkdir(parents=True)
            config.source_lists_dir.mkdir(parents=True)
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
            self.assertEqual(obsidian.answer_markdown, "")
            self.assertEqual(raw.evidence[0]["timecode"], "00:00:01")


def json_dumps_for_test(payload: dict) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
