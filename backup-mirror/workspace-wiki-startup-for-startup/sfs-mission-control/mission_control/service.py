from __future__ import annotations

import subprocess
import threading
from typing import Any

from .config import Config
from .db import Store
from .snoracle_adapter import cancel_openclaw_lookup, kill_process_group, synthesize_answer


class MissionControlService:
    def __init__(self, config: Config, store: Store):
        self.config = config
        self.store = store
        self._busy_lock = threading.Lock()
        self._current_question_id: str | None = None
        self._process_lock = threading.Lock()
        self._active_processes: dict[str, subprocess.Popen[str]] = {}

    def ask(self, question: str, sources: dict[str, bool]) -> dict[str, Any]:
        question = question.strip()
        if not question:
            return {"status": "error", "message": "question is required"}
        selected = {
            "wikillm": bool((sources or {}).get("wikillm")),
            "obsidian": bool((sources or {}).get("obsidian")),
            "raw": bool((sources or {}).get("raw")),
        }
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
        local_kill = self._kill_active_process(question_id)
        row = self.store.get_question_row(question_id) or {}
        cancel_result = self._attempt_openclaw_cancel(question_id, row)
        return {
            "status": "cancelled",
            "question_id": question_id,
            "local_kill": local_kill,
            "openclaw_cancel": cancel_result,
        }

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
            selected = {
                "wikillm": bool(row.get("selected_wikillm")),
                "obsidian": bool(row.get("selected_obsidian")),
                "raw": bool(row.get("selected_raw")),
            }
            self.store.log(question_id, "info", "Snoracle OpenClaw turn requested", {"mode": self.config.snoracle_mode, "agent_id": self.config.snoracle_agent_id})
            final_payload = synthesize_answer(
                self.config,
                self.store,
                question_id,
                row["question"],
                selected,
                register_process=self._register_process,
                is_cancelled=lambda: self.store.is_cancelled(question_id),
            )
            adapter_meta = final_payload.pop("_adapter_meta", {})
            if adapter_meta:
                self.store.log(question_id, "info", "Snoracle adapter completed", adapter_meta)
            if self.store.is_cancelled(question_id):
                self.store.log(question_id, "warning", "Snoracle result ignored because question was cancelled", {})
                return
            candidate = bool(final_payload.get("candidate"))
            self.store.log(question_id, "info", "final answer received", {"candidate": candidate, "status": final_payload.get("status")})
            self.store.finish_question(question_id, final_payload, candidate, None)
        except Exception as exc:
            self.store.fail_question(question_id, str(exc))
        finally:
            self._register_process(question_id, None)
            self._current_question_id = None
            self._busy_lock.release()

    def _register_process(self, question_id: str, process: subprocess.Popen[str] | None) -> None:
        with self._process_lock:
            if process is None:
                self._active_processes.pop(question_id, None)
            else:
                self._active_processes[question_id] = process

    def _kill_active_process(self, question_id: str) -> dict[str, Any]:
        with self._process_lock:
            process = self._active_processes.get(question_id)
        if process is None:
            result = {"status": "no_local_process"}
            self.store.log(question_id, "warning", "cancel requested with no active local subprocess", result)
            return result
        result = kill_process_group(process)
        self.store.log(question_id, "warning", "local OpenClaw subprocess cancellation attempted", result)
        self._register_process(question_id, None)
        return result

    def _attempt_openclaw_cancel(self, question_id: str, row: dict[str, Any]) -> dict[str, Any]:
        lookups = [
            row.get("openclaw_task_id"),
            row.get("openclaw_run_id"),
            row.get("openclaw_session_key"),
        ]
        for lookup in lookups:
            if not lookup:
                continue
            result = cancel_openclaw_lookup(self.config, str(lookup))
            self.store.log(question_id, "warning", "OpenClaw cancellation path attempted", {"lookup": lookup, "result": result})
            if result.get("status") == "attempted" and result.get("exit_code") == 0:
                return {"lookup": lookup, "result": result}
        result = {"status": "unavailable", "reason": "no successful task/run/session-key cancellation path"}
        self.store.log(question_id, "warning", "OpenClaw cancellation path unavailable", result)
        return result
