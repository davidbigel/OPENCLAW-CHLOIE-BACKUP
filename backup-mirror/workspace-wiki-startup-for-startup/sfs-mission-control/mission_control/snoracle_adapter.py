from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .config import Config
from .workers import WorkerResult


OPENCLAW_PROMPT_SOFT_LIMIT = 180_000


def synthesize_answer(config: Config, question_id: str, question: str, worker_results: list[WorkerResult]) -> dict[str, Any]:
    local_payload = _local_synthesis(question_id, question, worker_results)
    if config.snoracle_mode != "openclaw":
        local_payload["_adapter_meta"] = {
            "mode": config.snoracle_mode,
            "route": config.snoracle_route_label,
            "fallback_used": True,
            "reason": "openclaw mode disabled",
        }
        return local_payload
    if _routes_to_current_agent(config):
        local_payload["labels"].append("Snoracle adapter fallback")
        local_payload["summary_answer_markdown"] += (
            "\n\nSnoracle thinks: OpenClaw synthesis was routed to this same busy agent, so Mission Control "
            "used the local synthesis fallback instead of deadlocking."
        )
        local_payload["_adapter_meta"] = {
            "mode": config.snoracle_mode,
            "route": config.snoracle_route_label,
            "fallback_used": True,
            "reason": "self-route blocked to avoid deadlock",
        }
        return local_payload
    try:
        payload, meta = _openclaw_synthesis(config, question_id, question, worker_results, local_payload)
        payload["_adapter_meta"] = meta
        return payload
    except Exception as exc:
        local_payload["labels"].append("Snoracle adapter fallback")
        local_payload["summary_answer_markdown"] += (
            "\n\nSnoracle thinks: OpenClaw dispatch failed, so this answer used the local synthesis fallback. "
            f"Adapter error: {exc}"
        )
        local_payload["_adapter_meta"] = {
            "mode": config.snoracle_mode,
            "route": config.snoracle_route_label,
            "fallback_used": True,
            "reason": str(exc),
        }
        return local_payload


def _local_synthesis(question_id: str, question: str, worker_results: list[WorkerResult]) -> dict[str, Any]:
    boxes: dict[str, Any] = {}
    sources_used: list[str] = []
    labels: list[str] = []
    evidence_count = 0
    for result in worker_results:
        boxes[result.source] = {
            "selected": True,
            "status": result.status,
            "answer_markdown": result.answer_markdown,
            "citations": result.citations,
            "evidence": result.evidence,
            "errors": result.errors,
        }
        evidence_count += len(result.evidence)
        if result.status == "used":
            sources_used.append(result.source)
            if result.source == "wikillm":
                labels.append("Corpus")
            if result.source == "raw":
                labels.append("Raw")
            if result.source == "obsidian":
                labels.append("Obsidian")
    for source in ("wikillm", "obsidian", "raw"):
        boxes.setdefault(
            source,
            {
                "selected": False,
                "status": "not_selected",
                "answer_markdown": "not selected",
                "citations": [],
                "evidence": [],
                "errors": [],
            },
        )
    if sources_used:
        summary = [
            f"Corpus: לשאלה הזו נמצאו מקורות ב-{', '.join(sources_used)}.",
            "Snoracle thinks: זה מספיק לתשובה ראשונית, אבל זו סינתזה מקומית. אם מפעילים MC_SNORACLE_MODE=openclaw, אותה חבילת ראיות תישלח לסנורקל דרך OpenClaw.",
        ]
    else:
        summary = [
            "No KB evidence: לא מצאתי מידע תומך ב-KB או בתמלולים שנבחרו.",
            "Snoracle thinks: אפשר לענות מבחוץ רק אם מסמנים זאת במפורש כידע חיצוני; כרגע אין בסיס קורפוס מספיק.",
        ]
    labels.append("Snoracle thinks")
    return {
        "question_id": question_id,
        "status": "done",
        "summary_answer_markdown": "\n\n".join(summary),
        "boxes": boxes,
        "disagreements": [],
        "wiki_update_candidates": [],
        "sources_used_footer": f"Sources Used: {', '.join(sources_used) if sources_used else 'none'} | Evidence items: {evidence_count}",
        "labels": list(dict.fromkeys(labels)),
    }


def _openclaw_synthesis(
    config: Config,
    question_id: str,
    question: str,
    worker_results: list[WorkerResult],
    fallback_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt, compact_meta = _build_prompt(question_id, question, worker_results, fallback_payload)
    command = _build_openclaw_command(config, json.dumps(prompt, ensure_ascii=False))
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
        timeout=960,
    )
    payload = _extract_json_payload(completed.stdout)
    meta = {
        "mode": config.snoracle_mode,
        "route": config.snoracle_route_label,
        "fallback_used": False,
    }
    meta.update(compact_meta)
    return payload, meta


def _build_prompt(
    question_id: str,
    question: str,
    worker_results: list[WorkerResult],
    fallback_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    answer_limit = 2400
    evidence_limit = 24
    citation_limit = 24
    prompt = {
        "instruction": (
            "You are Snoracle. Return JSON only in the Mission Control answer shape. "
            "Answer in Hebrew. Cite or label every paragraph. Preserve the three source boxes."
        ),
        "question_id": question_id,
        "question": question,
        "worker_results": [_compact_worker_result(item, answer_limit, evidence_limit, citation_limit) for item in worker_results],
        "full_evidence_note": (
            "The UI and SQLite retain the complete evidence lists. This prompt contains compacted evidence "
            "to avoid CLI payload limits; mention if more raw evidence is needed."
        ),
        "fallback_payload_shape": {
            "question_id": fallback_payload.get("question_id"),
            "status": fallback_payload.get("status"),
            "summary_answer_markdown": fallback_payload.get("summary_answer_markdown"),
            "boxes": {
                source: {
                    "selected": box.get("selected"),
                    "status": box.get("status"),
                    "answer_markdown": box.get("answer_markdown"),
                    "evidence_count": len(box.get("evidence") or []),
                }
                for source, box in (fallback_payload.get("boxes") or {}).items()
            },
            "sources_used_footer": fallback_payload.get("sources_used_footer"),
            "labels": fallback_payload.get("labels"),
        },
    }
    while _json_size(prompt) > OPENCLAW_PROMPT_SOFT_LIMIT and evidence_limit > 4:
        evidence_limit = max(4, evidence_limit // 2)
        citation_limit = max(4, citation_limit // 2)
        prompt["worker_results"] = [_compact_worker_result(item, answer_limit, evidence_limit, citation_limit) for item in worker_results]
    while _json_size(prompt) > OPENCLAW_PROMPT_SOFT_LIMIT and answer_limit > 600:
        answer_limit = max(600, answer_limit // 2)
        prompt["worker_results"] = [_compact_worker_result(item, answer_limit, evidence_limit, citation_limit) for item in worker_results]
    compact_meta = {
        "prompt_bytes": _json_size(prompt),
        "worker_count": len(worker_results),
        "answer_char_limit": answer_limit,
        "evidence_sample_limit": evidence_limit,
        "citation_sample_limit": citation_limit,
        "truncated_prompt": _json_size(prompt) > OPENCLAW_PROMPT_SOFT_LIMIT,
    }
    return prompt, compact_meta


def _build_openclaw_command(config: Config, prompt_json: str) -> list[str]:
    command = [
        "openclaw",
        "agent",
        "--thinking",
        "xhigh",
        "--json",
        "--timeout",
        "900",
    ]
    if config.snoracle_session_id:
        command.extend(["--session-id", config.snoracle_session_id])
    else:
        command.extend(["--agent", config.snoracle_agent_id])
    command.extend(["--message", prompt_json])
    return command


def _routes_to_current_agent(config: Config) -> bool:
    if config.snoracle_session_id:
        return False
    current_agent_id = _discover_current_agent_id()
    return bool(current_agent_id and current_agent_id == config.snoracle_agent_id)


def _discover_current_agent_id() -> str | None:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if not codex_home:
        return None
    parts = Path(codex_home).resolve().parts
    try:
        agents_index = parts.index("agents")
    except ValueError:
        return None
    if agents_index + 1 >= len(parts):
        return None
    agent_id = parts[agents_index + 1].strip()
    return agent_id or None


def _compact_worker_result(
    item: WorkerResult,
    answer_limit: int,
    evidence_limit: int,
    citation_limit: int,
) -> dict[str, Any]:
    evidence = item.evidence or []
    citations = item.citations or []
    return {
        "source": item.source,
        "status": item.status,
        "answer_markdown": _truncate_text(item.answer_markdown, answer_limit),
        "evidence_count": len(evidence),
        "evidence_sample": evidence[:evidence_limit],
        "citations_sample": citations[:citation_limit],
        "errors": item.errors,
    }


def _extract_json_payload(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            for key in ("message", "reply", "response", "text", "content"):
                value = parsed.get(key)
                if isinstance(value, str) and "{" in value:
                    return _extract_json_payload(value)
            if "summary_answer_markdown" in parsed:
                return parsed
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("OpenClaw output did not contain JSON")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("OpenClaw JSON payload is not an object")
    return parsed


def _json_size(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _truncate_text(value: str, limit: int) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    trimmed = text[: max(0, limit - 1)].rstrip()
    return trimmed + "…"
