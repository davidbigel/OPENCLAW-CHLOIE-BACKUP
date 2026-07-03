from __future__ import annotations

import json
import os
import signal
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable

from .config import Config
from .db import Store


ProcessRegistrar = Callable[[str, subprocess.Popen[str] | None], None]
CancelCheck = Callable[[], bool]


def synthesize_answer(
    config: Config,
    store: Store,
    question_id: str,
    question: str,
    selected_sources: dict[str, bool],
    *,
    register_process: ProcessRegistrar | None = None,
    is_cancelled: CancelCheck | None = None,
) -> dict[str, Any]:
    run_dir = config.runs_dir / question_id
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    raw_response_path = run_dir / "raw-response.txt"
    session_id = _session_id_for_question(question_id)
    session_key = f"agent:{config.snoracle_agent_id}:explicit:{session_id}"
    store.prepare_agent_run(
        question_id,
        agent_id=config.snoracle_agent_id,
        session_id=session_id,
        session_key=session_key,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        raw_response_path=str(raw_response_path),
    )
    prompt = _build_action_prompt(question_id, question, selected_sources)
    if config.snoracle_mode != "openclaw":
        raw = _local_dev_response(question_id, question, selected_sources)
        _write_run_files(stdout_path, stderr_path, raw_response_path, raw, "")
        payload, parse_status = _payload_from_raw(question_id, raw, selected_sources, 0, "")
        store.finish_agent_run(
            question_id,
            exit_code=0,
            parse_status=parse_status,
            raw_response_text=raw,
        )
        payload["_adapter_meta"] = {
            "mode": config.snoracle_mode,
            "agent_id": config.snoracle_agent_id,
            "session_id": session_id,
            "session_key": session_key,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "raw_response_path": str(raw_response_path),
            "fallback_used": True,
        }
        return payload

    command = _build_openclaw_command(config, session_id, prompt)
    store.log(
        question_id,
        "info",
        "OpenClaw agent dispatch starting",
        {
            "agent_id": config.snoracle_agent_id,
            "session_id": session_id,
            "timeout_seconds": config.snoracle_timeout_seconds,
            "selected_sources": [name for name, enabled in selected_sources.items() if enabled],
        },
    )
    if is_cancelled and is_cancelled():
        return _fallback_payload(question_id, "cancelled before dispatch", selected_sources, "failed", "cancelled")

    process: subprocess.Popen[str] | None = None
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    timeout_hit = False
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        store.mark_agent_process_started(question_id, process.pid, command)
        if register_process:
            register_process(question_id, process)
        try:
            stdout, stderr = process.communicate(timeout=config.snoracle_timeout_seconds + 15)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            timeout_hit = True
            _terminate_process_group(process)
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                stdout = stdout or ""
                stderr = (stderr or "") + "\nMission Control could not collect process output after timeout."
            exit_code = process.returncode if process.returncode is not None else -9
            stderr = (stderr or "") + "\nMission Control local timeout expired."
    except FileNotFoundError as exc:
        exit_code = 127
        stderr = str(exc)
    finally:
        if register_process:
            register_process(question_id, None)

    raw_response = _raw_response(stdout, stderr)
    _write_run_files(stdout_path, stderr_path, raw_response_path, stdout, stderr, raw_response)
    payload, parse_status = _payload_from_raw(question_id, raw_response, selected_sources, exit_code, stderr)
    if timeout_hit:
        payload["status"] = "failed"
        payload["error"] = "OpenClaw turn timed out after 300 seconds"
        parse_status = "timeout"
    run_id, task_id = _extract_openclaw_ids(stdout, stderr)
    store.finish_agent_run(
        question_id,
        exit_code=exit_code,
        parse_status=parse_status,
        raw_response_text=raw_response,
        run_id=run_id,
        task_id=task_id,
    )
    payload["_adapter_meta"] = {
        "mode": config.snoracle_mode,
        "agent_id": config.snoracle_agent_id,
        "session_id": session_id,
        "session_key": session_key,
        "exit_code": exit_code,
        "parse_status": parse_status,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "raw_response_path": str(raw_response_path),
        "fallback_used": False,
        "run_id": run_id,
        "task_id": task_id,
    }
    return payload


def cancel_openclaw_lookup(config: Config, lookup: str) -> dict[str, Any]:
    if not lookup:
        return {"status": "skipped", "reason": "missing lookup"}
    command = ["openclaw", "tasks", "cancel", lookup]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"status": "unavailable", "reason": str(exc)}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    return {
        "status": "attempted",
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def kill_process_group(process: subprocess.Popen[str]) -> dict[str, Any]:
    return _terminate_process_group(process)


def _build_action_prompt(question_id: str, question: str, selected_sources: dict[str, bool]) -> str:
    selected = ", ".join(name for name, enabled in selected_sources.items() if enabled) or "none"
    flags = "\n".join(
        f"- {name}: {'selected' if selected_sources.get(name) else 'not selected'}"
        for name in ("wikillm", "obsidian", "raw")
    )
    return (
        "Mission Control request.\n"
        "Return Mission Control JSON only as described in TOOLS.md.\n"
        "Answer in Hebrew unless the user explicitly asks otherwise.\n"
        "Preserve the three source boxes. Obsidian does not exist yet; if it is used accidentally, return an empty Obsidian answer with no evidence.\n"
        "Snoracle/subagents own source-query reasoning; do not rely on the API to prefetch evidence.\n"
        f"Question ID: {question_id}\n"
        f"Selected sources: {selected}\n"
        f"Source flags:\n{flags}\n"
        "User question:\n"
        f"{question.strip()}\n"
    )


def _build_openclaw_command(config: Config, session_id: str, prompt: str) -> list[str]:
    return [
        "openclaw",
        "agent",
        "--agent",
        config.snoracle_agent_id,
        "--session-id",
        session_id,
        "--message",
        prompt,
        "--thinking",
        "xhigh",
        "--timeout",
        str(config.snoracle_timeout_seconds),
        "--json",
    ]


def _session_id_for_question(question_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in question_id)
    return f"mc-{safe}-{uuid.uuid4().hex[:8]}"


def _write_run_files(
    stdout_path: Path,
    stderr_path: Path,
    raw_response_path: Path,
    stdout: str,
    stderr: str,
    raw_response: str | None = None,
) -> None:
    stdout_path.write_text(stdout or "", encoding="utf-8")
    stderr_path.write_text(stderr or "", encoding="utf-8")
    raw_response_path.write_text(raw_response if raw_response is not None else stdout or "", encoding="utf-8")


def _raw_response(stdout: str, stderr: str) -> str:
    if stdout.strip():
        return stdout.strip()
    if stderr.strip():
        return stderr.strip()
    return ""


def _payload_from_raw(
    question_id: str,
    raw_response: str,
    selected_sources: dict[str, bool],
    exit_code: int | None,
    stderr: str,
) -> tuple[dict[str, Any], str]:
    try:
        parsed = _extract_json_payload(raw_response)
    except Exception as exc:
        status = "failed" if exit_code not in (0, None) and not raw_response.strip() else "done"
        return (
            _fallback_payload(
                question_id,
                raw_response or stderr or str(exc),
                selected_sources,
                status,
                f"structured JSON parse failed: {exc}",
            ),
            "raw",
        )
    payload = _normalize_payload(parsed, question_id, selected_sources)
    if exit_code not in (0, None):
        payload.setdefault("error", stderr.strip() or f"OpenClaw exited with {exit_code}")
        payload["status"] = "failed"
    return payload, "parsed"


def _extract_json_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty OpenClaw output")
    for candidate in _json_candidates(stripped):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        found = _find_mission_control_payload(parsed)
        if found is not None:
            return found
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("OpenClaw output did not contain JSON")
    parsed = json.loads(stripped[start : end + 1])
    found = _find_mission_control_payload(parsed)
    if found is None:
        raise ValueError("OpenClaw JSON did not contain a Mission Control payload")
    return found


def _json_candidates(text: str) -> list[str]:
    candidates = [text]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates.extend(reversed(lines))
    return candidates


def _find_mission_control_payload(value: Any, depth: int = 0) -> dict[str, Any] | None:
    if depth > 8:
        return None
    if isinstance(value, dict):
        if "summary_answer_markdown" in value and "boxes" in value:
            return value
        for key in ("message", "reply", "response", "text", "content", "output", "result", "final"):
            found = _find_mission_control_payload(value.get(key), depth + 1)
            if found is not None:
                return found
        for key in ("messages", "items", "payloads", "content"):
            found = _find_mission_control_payload(value.get(key), depth + 1)
            if found is not None:
                return found
        for child in value.values():
            if isinstance(child, (dict, list)):
                found = _find_mission_control_payload(child, depth + 1)
                if found is not None:
                    return found
            elif isinstance(child, str) and "{" in child:
                try:
                    found = _extract_json_payload(child)
                except Exception:
                    found = None
                if found is not None:
                    return found
    if isinstance(value, list):
        for item in value:
            found = _find_mission_control_payload(item, depth + 1)
            if found is not None:
                return found
    if isinstance(value, str) and "{" in value:
        try:
            return _extract_json_payload(value)
        except Exception:
            return None
    return None


def _normalize_payload(payload: dict[str, Any], question_id: str, selected_sources: dict[str, bool]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["question_id"] = str(normalized.get("question_id") or question_id)
    normalized["status"] = str(normalized.get("status") or "done")
    normalized["summary_answer_markdown"] = str(normalized.get("summary_answer_markdown") or "")
    normalized["boxes"] = _normalize_boxes(normalized.get("boxes"), selected_sources)
    normalized["disagreements"] = _ensure_list(normalized.get("disagreements"))
    normalized["wiki_update_candidates"] = _ensure_list(normalized.get("wiki_update_candidates"))
    normalized["sources_used_footer"] = str(normalized.get("sources_used_footer") or "")
    normalized["labels"] = _ensure_list(normalized.get("labels"))
    normalized["candidate"] = bool(normalized.get("candidate", False))
    return normalized


def _normalize_boxes(boxes: Any, selected_sources: dict[str, bool]) -> dict[str, Any]:
    incoming = boxes if isinstance(boxes, dict) else {}
    result: dict[str, Any] = {}
    for source in ("wikillm", "obsidian", "raw"):
        box = incoming.get(source) if isinstance(incoming.get(source), dict) else {}
        selected = bool(selected_sources.get(source))
        status = str(box.get("status") or ("not_selected" if not selected else "no_useful_evidence"))
        result[source] = {
            "selected": selected,
            "status": status,
            "answer_markdown": str(box.get("answer_markdown") or ""),
            "citations": _ensure_list(box.get("citations")),
            "evidence": _ensure_list(box.get("evidence")),
            "errors": _ensure_list(box.get("errors")),
        }
    return result


def _fallback_payload(
    question_id: str,
    raw_response: str,
    selected_sources: dict[str, bool],
    status: str,
    error: str,
) -> dict[str, Any]:
    boxes = {}
    for source in ("wikillm", "obsidian", "raw"):
        selected = bool(selected_sources.get(source))
        boxes[source] = {
            "selected": selected,
            "status": "failed" if selected else "not_selected",
            "answer_markdown": "" if not selected else "Raw OpenClaw output is shown in the main answer area.",
            "citations": [],
            "evidence": [],
            "errors": [error] if selected else [],
        }
    return {
        "question_id": question_id,
        "status": status,
        "summary_answer_markdown": raw_response,
        "boxes": boxes,
        "disagreements": [],
        "wiki_update_candidates": [],
        "sources_used_footer": "Sources Used: raw OpenClaw output | Evidence items: unknown",
        "labels": ["Raw OpenClaw output"],
        "candidate": False,
        "error": error if status == "failed" else None,
    }


def _local_dev_response(question_id: str, question: str, selected_sources: dict[str, bool]) -> str:
    payload = {
        "question_id": question_id,
        "status": "done",
        "summary_answer_markdown": (
            "Snoracle local-dev: OpenClaw dispatch is disabled for this process. "
            "The production path calls the wiki-startup-for-startup agent directly."
        ),
        "boxes": _normalize_boxes({}, selected_sources),
        "disagreements": [],
        "wiki_update_candidates": [],
        "sources_used_footer": "Sources Used: local-dev | Evidence items: 0",
        "labels": ["Snoracle local-dev"],
        "candidate": False,
    }
    return json.dumps(payload, ensure_ascii=False)


def _ensure_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _terminate_process_group(process: subprocess.Popen[str]) -> dict[str, Any]:
    if process.poll() is not None:
        return {"status": "already_exited", "pid": process.pid, "returncode": process.returncode}
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return {"status": "missing", "pid": process.pid}
    except Exception as exc:
        return {"status": "failed", "pid": process.pid, "error": str(exc)}
    try:
        process.wait(timeout=5)
        return {"status": "terminated", "pid": process.pid, "returncode": process.returncode}
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except Exception as exc:
            return {"status": "kill_failed", "pid": process.pid, "error": str(exc)}
        process.wait(timeout=5)
        return {"status": "killed", "pid": process.pid, "returncode": process.returncode}


def _extract_openclaw_ids(stdout: str, stderr: str) -> tuple[str | None, str | None]:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    run_id = None
    task_id = None
    for candidate in _json_candidates(combined):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        run_id = run_id or _find_key(parsed, {"run_id", "runId"})
        task_id = task_id or _find_key(parsed, {"task_id", "taskId"})
    return run_id, task_id


def _find_key(value: Any, names: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in names and isinstance(item, (str, int)):
                return str(item)
        for item in value.values():
            found = _find_key(item, names)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _find_key(item, names)
            if found:
                return found
    return None
