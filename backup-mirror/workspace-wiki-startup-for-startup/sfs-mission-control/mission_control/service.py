from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .config import Config
from .db import Store
from .snoracle_adapter import synthesize_answer
from .util import utc_now
from .workers import WorkerResult, run_obsidian_worker, run_raw_worker, run_wikillm_worker


class MissionControlService:
    def __init__(self, config: Config, store: Store):
        self.config = config
        self.store = store
        self._busy_lock = threading.Lock()
        self._current_question_id: str | None = None
        self._patch_thread = threading.Thread(target=self._patch_loop, name="wiki-patch-loop", daemon=True)
        self._patch_thread.start()

    def ask(self, question: str, sources: dict[str, bool]) -> dict[str, Any]:
        question = question.strip()
        if not question:
            return {"status": "error", "message": "question is required"}
        selected = {name: bool(value) for name, value in (sources or {}).items()}
        if not any(selected.values()):
            return {"status": "error", "message": "at least one source must be selected"}
        running = self.store.has_running_question()
        if running or self._current_question_id:
            return {
                "status": "busy",
                "message": "Snoracle is busy with another question. Try again in a few minutes.",
                "running_question_id": running or self._current_question_id,
            }
        question_id = self.store.create_question(question, selected)
        self.store.log(question_id, "info", "question accepted by mission control", {"question_chars": len(question), "sources": selected})
        thread = threading.Thread(target=self._process_question, args=(question_id,), name=f"question-{question_id}", daemon=True)
        thread.start()
        return {"question_id": question_id, "status": "running"}

    def rerun(self, question_id: str, sources: dict[str, bool] | None = None) -> dict[str, Any]:
        row = self.store.get_question_row(question_id)
        if not row:
            return {"status": "not_found", "message": "question not found"}
        selected = sources or {
            "wikillm": bool(row.get("selected_wikillm")),
            "obsidian": bool(row.get("selected_obsidian")),
            "raw": bool(row.get("selected_raw")),
        }
        return self.ask(row["question"], selected)

    def cancel(self, question_id: str) -> dict[str, Any]:
        ok = self.store.request_cancel(question_id)
        if not ok:
            return {"status": "not_found"}
        return {"status": "cancelled", "question_id": question_id}

    def toggle_thread(self, question_id: str) -> dict[str, Any]:
        result = self.store.toggle_thread_for_question(question_id)
        if result is None:
            return {"status": "not_found"}
        return result

    def list_questions(self) -> dict[str, Any]:
        return {"questions": self.store.list_questions()}

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        return self.store.get_question_response(question_id)

    def _process_question(self, question_id: str) -> None:
        if not self._busy_lock.acquire(blocking=False):
            self.store.fail_question(question_id, "Snoracle became busy before processing could start")
            return
        self._current_question_id = question_id
        try:
            row = self.store.get_question_row(question_id)
            if not row:
                return
            if not self.store.mark_question_running(question_id):
                return
            if self.store.is_cancelled(question_id):
                return
            question = row["question"]
            selected = {
                "wikillm": bool(row.get("selected_wikillm")),
                "obsidian": bool(row.get("selected_obsidian")),
                "raw": bool(row.get("selected_raw")),
            }
            results = self._run_source_workers(question_id, question, selected)
            if self.store.is_cancelled(question_id):
                return
            self.store.log(question_id, "info", "Snoracle synthesizing final answer", {"mode": self.config.snoracle_mode})
            final_payload = synthesize_answer(self.config, question_id, question, results)
            adapter_meta = final_payload.pop("_adapter_meta", {})
            if adapter_meta:
                self.store.log(question_id, "info", "Snoracle adapter completed", adapter_meta)
            if self.store.is_cancelled(question_id):
                self.store.log(question_id, "warning", "synthesis result ignored because question was cancelled", {})
                return
            meaningful, reason = self._is_meaningful(final_payload)
            self.store.log(
                question_id,
                "info",
                "final answer evaluated",
                {
                    "meaningful": meaningful,
                    "reason": reason,
                    "wiki_update_candidates": len(final_payload.get("wiki_update_candidates", []) or []),
                },
            )
            snapshot_path = None
            if meaningful:
                snapshot_path = self.store.create_answer_snapshot(question_id, self._snapshot_markdown(question, final_payload, reason), reason)
            if self.store.is_cancelled(question_id):
                self.store.log(question_id, "warning", "final write skipped because question was cancelled after snapshot", {})
                return
            for candidate in final_payload.get("wiki_update_candidates", []) or []:
                self.store.create_wiki_update_candidate(question_id, "snoracle candidate", candidate)
                self.store.create_wiki_patch_job(question_id, "snoracle candidate", candidate)
            self.store.finish_question(question_id, final_payload, meaningful, snapshot_path)
        except Exception as exc:
            self.store.fail_question(question_id, str(exc))
        finally:
            self._current_question_id = None
            self._busy_lock.release()

    def _run_source_workers(self, question_id: str, question: str, selected: dict[str, bool]) -> list[WorkerResult]:
        jobs = []
        if selected.get("wikillm"):
            jobs.append(("wikillm", run_wikillm_worker))
        if selected.get("obsidian"):
            jobs.append(("obsidian", run_obsidian_worker))
        if selected.get("raw"):
            jobs.append(("raw", run_raw_worker))
        results: list[WorkerResult] = []
        with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as executor:
            future_map = {}
            for source, worker in jobs:
                run_id = self.store.create_source_run(question_id, source)
                self.store.log(question_id, "info", f"{source} worker searching", {"source_run_id": run_id})
                future = executor.submit(worker, self.config, question)
                future_map[future] = (source, run_id)
            for future in as_completed(future_map):
                source, run_id = future_map[future]
                if self.store.is_cancelled(question_id):
                    self.store.finish_source_run(run_id, question_id, source, "cancelled", "cancelled")
                    continue
                try:
                    result = future.result()
                except Exception as exc:
                    result = WorkerResult(source=source, status="failed", answer_markdown=f"{source} worker failed", errors=[str(exc)])
                self.store.log(
                    question_id,
                    "info" if result.status != "failed" else "error",
                    f"{source} worker found {len(result.evidence)} evidence items",
                    {"source_run_id": run_id, "status": result.status},
                )
                self.store.log(question_id, "info", f"{source} worker interpreting complete", {"source_run_id": run_id})
                self.store.insert_evidence(question_id, run_id, result.evidence)
                self.store.finish_source_run(
                    run_id,
                    question_id,
                    source,
                    result.status,
                    result.answer_markdown,
                    "; ".join(result.errors) if result.errors else None,
                )
                results.append(result)
        self.store.log(
            question_id,
            "info",
            "all selected source workers completed",
            {
                "selected_sources": [source for source, enabled in selected.items() if enabled],
                "result_statuses": {item.source: item.status for item in results},
                "evidence_total": sum(len(item.evidence) for item in results),
            },
        )
        return results

    def _is_meaningful(self, payload: dict[str, Any]) -> tuple[bool, str]:
        evidence_count = 0
        for box in (payload.get("boxes") or {}).values():
            evidence_count += len(box.get("evidence") or [])
        if payload.get("wiki_update_candidates"):
            return True, "wiki update candidate"
        if evidence_count >= 3:
            return True, f"{evidence_count} evidence items"
        return False, "low evidence volume"

    def _snapshot_markdown(self, question: str, payload: dict[str, Any], reason: str) -> str:
        lines = [
            "---",
            "type: mission-control-answer",
            f"question_id: {payload.get('question_id')}",
            f"created_at: {utc_now()}",
            f"reason: {reason}",
            "---",
            "",
            f"# {question}",
            "",
            "## Summary",
            "",
            payload.get("summary_answer_markdown", ""),
            "",
            "## Source Boxes",
            "",
        ]
        for source, box in (payload.get("boxes") or {}).items():
            lines.extend(
                [
                    f"### {source}",
                    "",
                    f"Status: {box.get('status')}",
                    "",
                    box.get("answer_markdown") or "",
                    "",
                ]
            )
        lines.extend(["## Sources Used", "", payload.get("sources_used_footer", "")])
        return "\n".join(lines).strip() + "\n"

    def _patch_loop(self) -> None:
        while True:
            try:
                job = self.store.claim_next_wiki_patch_job()
                if not job:
                    time.sleep(2)
                    continue
                question_id = job["question_id"]
                changed_file = self._write_wiki_patch_candidate(job)
                if changed_file:
                    self.store.finish_wiki_patch_job(job["id"], question_id, "drafted", None, [changed_file])
                else:
                    self.store.finish_wiki_patch_job(job["id"], question_id, "skipped", "no actionable wiki patch payload", [])
            except Exception as exc:
                if 'job' in locals() and job:
                    self.store.finish_wiki_patch_job(job["id"], job["question_id"], "failed", str(exc), [])
                time.sleep(2)

    def _write_wiki_patch_candidate(self, job: dict[str, Any]) -> str | None:
        question_id = job["question_id"]
        payload = {}
        try:
            payload = json.loads(job.get("payload_json") or "{}")
        except json.JSONDecodeError:
            payload = {"raw_payload": job.get("payload_json")}
        if not _has_actionable_patch_payload(payload):
            return None
        question = self.store.get_question_row(question_id) or {}
        target_dir = self.config.wikillm_dir / "questions"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"mission-control-update-{job['id']}.md"
        markdown = [
            "---",
            "type: mission-control-wiki-update",
            f"question_id: {question_id}",
            f"patch_job_id: {job['id']}",
            "status: drafted-auto",
            f"created_at: {utc_now()}",
            "---",
            "",
            f"# Mission Control Wiki Update {job['id']}",
            "",
            "## Trigger Question",
            "",
            str(question.get("question") or ""),
            "",
            "## Reason",
            "",
            str(job.get("reason") or ""),
            "",
            "## Candidate Payload",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Review Notes",
            "",
            "- Auto-created by Mission Control's serialized wiki patch queue.",
            "- Review before promoting this into a concept, claim, playbook, or episode page.",
        ]
        target.write_text("\n".join(markdown).strip() + "\n", encoding="utf-8")
        return str(target.relative_to(self.config.workspace_root))


def _has_actionable_patch_payload(payload: Any) -> bool:
    if payload is None:
        return False
    if isinstance(payload, str):
        return bool(payload.strip())
    if isinstance(payload, (int, float, bool)):
        return True
    if isinstance(payload, list):
        return any(_has_actionable_patch_payload(item) for item in payload)
    if isinstance(payload, dict):
        return any(_has_actionable_patch_payload(value) for value in payload.values())
    return False
