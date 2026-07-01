from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from .config import Config
from .util import compact_id, json_dumps, utc_now


class Store:
    def __init__(self, config: Config):
        self.config = config
        self._lock = threading.RLock()

    def init(self) -> None:
        self.config.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        self.config.answers_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.executescript(SCHEMA)
            con.execute("PRAGMA journal_mode=WAL")
            con.execute(
                "INSERT OR IGNORE INTO settings(key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
                ("snoracle_session_key", self.config.snoracle_route_label, utc_now(), utc_now()),
            )
            con.execute(
                "INSERT OR IGNORE INTO settings(key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
                ("public_auth_hint", "static query gate", utc_now(), utc_now()),
            )

    def recover_incomplete_questions(self) -> int:
        with self._lock, self._connect() as con:
            rows = con.execute(
                "SELECT id, status FROM questions WHERE status IN ('queued', 'running') ORDER BY created_at"
            ).fetchall()
            if not rows:
                return 0
            finished_at = utc_now()
            error = "mission control restarted before question completion"
            for row in rows:
                question_id = row["id"]
                con.execute(
                    """
                    UPDATE questions
                    SET status = 'failed', finished_at = COALESCE(finished_at, ?), error = COALESCE(error, ?)
                    WHERE id = ? AND status IN ('queued', 'running')
                    """,
                    (finished_at, error, question_id),
                )
                con.execute(
                    """
                    UPDATE source_runs
                    SET status = 'failed', finished_at = COALESCE(finished_at, ?), error = COALESCE(error, ?)
                    WHERE question_id = ? AND status = 'running'
                    """,
                    (finished_at, error, question_id),
                )
                self._log(
                    con,
                    question_id,
                    "warning",
                    "question recovered as failed after mission control restart",
                    {"previous_status": row["status"]},
                )
        return len(rows)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.config.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def create_question(self, question: str, sources: dict[str, bool], thread_id: str | None = None) -> str:
        question_id = compact_id("q")
        now = utc_now()
        with self._lock, self._connect() as con:
            con.execute(
                """
                INSERT INTO questions(
                    id, thread_id, question, status,
                    selected_wikillm, selected_obsidian, selected_raw,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    question_id,
                    thread_id,
                    question,
                    "queued",
                    int(bool(sources.get("wikillm"))),
                    int(bool(sources.get("obsidian"))),
                    int(bool(sources.get("raw"))),
                    now,
                ),
            )
            self._log(con, question_id, "info", "question queued", {"sources": sources})
        return question_id

    def list_questions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT id, thread_id, question, status, selected_wikillm, selected_obsidian,
                       selected_raw, created_at, started_at, finished_at, cancelled_at, error
                FROM questions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_question_row(self, question_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
        return dict(row) if row else None

    def get_question_response(self, question_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            question = con.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
            if not question:
                return None
            source_runs = con.execute(
                "SELECT * FROM source_runs WHERE question_id = ? ORDER BY id",
                (question_id,),
            ).fetchall()
            evidence_rows = con.execute(
                "SELECT * FROM evidence_items WHERE question_id = ? ORDER BY rank, id",
                (question_id,),
            ).fetchall()
            logs = con.execute(
                "SELECT level, message, created_at, data_json FROM answer_logs WHERE question_id = ? ORDER BY id",
                (question_id,),
            ).fetchall()

        q = dict(question)
        final_json = _safe_load_json(q.get("final_json"))
        selected = {
            "wikillm": bool(q.get("selected_wikillm")),
            "obsidian": bool(q.get("selected_obsidian")),
            "raw": bool(q.get("selected_raw")),
        }
        boxes = {
            "wikillm": _empty_box(selected["wikillm"]),
            "obsidian": _empty_box(selected["obsidian"]),
            "raw": _empty_box(selected["raw"]),
        }
        source_run_by_id: dict[int, dict[str, Any]] = {}
        for row in source_runs:
            run = dict(row)
            source_run_by_id[run["id"]] = run
            source = run["source"]
            boxes[source] = {
                "selected": bool(selected.get(source)),
                "status": run["status"],
                "answer_markdown": run.get("answer_markdown") or "",
                "citations": [],
                "evidence": [],
                "errors": [run["error"]] if run.get("error") else [],
            }
        for row in evidence_rows:
            item = dict(row)
            run = source_run_by_id.get(item["source_run_id"])
            source = run["source"] if run else item["source_type"]
            payload = {
                "title": item.get("title"),
                "video_id": item.get("video_id"),
                "timecode": item.get("timecode"),
                "url": item.get("url"),
                "path": item.get("path"),
                "quote": item.get("quote"),
                "excerpt": item.get("excerpt"),
                "source_type": item.get("source_type"),
                "rank": item.get("rank"),
            }
            if source in boxes:
                boxes[source]["evidence"].append(payload)
                boxes[source]["citations"].append(payload)

        response = {
            "question_id": question_id,
            "status": q["status"],
            "question": q["question"],
            "thread_id": q.get("thread_id"),
            "created_at": q.get("created_at"),
            "started_at": q.get("started_at"),
            "finished_at": q.get("finished_at"),
            "cancelled_at": q.get("cancelled_at"),
            "sources_selected": [name for name, enabled in selected.items() if enabled],
            "sources_used": [name for name, box in boxes.items() if box["status"] == "used"],
            "summary_answer_markdown": q.get("summary_answer_markdown") or "",
            "boxes": boxes,
            "disagreements": _safe_load_json(q.get("disagreements_json")) or [],
            "wiki_update_candidates": _safe_load_json(q.get("wiki_update_candidates_json")) or [],
            "sources_used_footer": q.get("sources_used_footer") or "",
            "labels": _safe_load_json(q.get("labels_json")) or [],
            "meaningful": bool(q.get("meaningful")),
            "snapshot_path": q.get("snapshot_path"),
            "error": q.get("error"),
            "logs": [_log_row_to_dict(row) for row in logs],
        }
        if final_json:
            for key in (
                "summary_answer_markdown",
                "disagreements",
                "wiki_update_candidates",
                "sources_used_footer",
                "labels",
            ):
                if key in final_json:
                    response[key] = final_json[key]
            for source, final_box in (final_json.get("boxes") or {}).items():
                if source not in response["boxes"] or not isinstance(final_box, dict):
                    continue
                box = response["boxes"][source]
                for key in ("selected", "status", "answer_markdown", "errors"):
                    if key in final_box:
                        box[key] = final_box[key]
                if not box["evidence"] and final_box.get("evidence"):
                    box["evidence"] = final_box["evidence"]
                if not box["citations"] and final_box.get("citations"):
                    box["citations"] = final_box["citations"]
            response["sources_used"] = [
                name for name, box in response["boxes"].items() if box["status"] == "used"
            ]
            response["status"] = q["status"]
        return response

    def toggle_thread_for_question(self, question_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as con:
            row = con.execute("SELECT id, thread_id, question FROM questions WHERE id = ?", (question_id,)).fetchone()
            if not row:
                return None
            if row["thread_id"]:
                con.execute("UPDATE questions SET thread_id = NULL WHERE id = ?", (question_id,))
                self._log(con, question_id, "info", "question removed from saved thread", {"thread_id": row["thread_id"]})
                return {"status": "unsaved", "thread_id": None}
            thread_id = compact_id("t")
            title = row["question"][:90]
            now = utc_now()
            con.execute(
                "INSERT INTO saved_threads(id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (thread_id, title, now, now),
            )
            con.execute("UPDATE questions SET thread_id = ? WHERE id = ?", (thread_id, question_id))
            self._log(con, question_id, "info", "question saved as thread", {"thread_id": thread_id})
            return {"status": "saved", "thread_id": thread_id}

    def mark_question_running(self, question_id: str) -> bool:
        with self._lock, self._connect() as con:
            cur = con.execute(
                "UPDATE questions SET status = ?, started_at = ? WHERE id = ? AND status != 'cancelled'",
                ("running", utc_now(), question_id),
            )
            if cur.rowcount == 0:
                self._log(con, question_id, "warning", "question start skipped because it was already cancelled", {})
                return False
            self._log(con, question_id, "info", "question started", {})
        return True

    def finish_question(self, question_id: str, final_payload: dict[str, Any], meaningful: bool, snapshot_path: str | None = None) -> bool:
        now = utc_now()
        with self._lock, self._connect() as con:
            cur = con.execute(
                """
                UPDATE questions
                SET status = ?, finished_at = ?, summary_answer_markdown = ?, final_json = ?,
                    sources_used_footer = ?, disagreements_json = ?, wiki_update_candidates_json = ?,
                    labels_json = ?, meaningful = ?, snapshot_path = ?
                WHERE id = ? AND status != 'cancelled'
                """,
                (
                    "done",
                    now,
                    final_payload.get("summary_answer_markdown", ""),
                    json_dumps(final_payload),
                    final_payload.get("sources_used_footer", ""),
                    json_dumps(final_payload.get("disagreements", [])),
                    json_dumps(final_payload.get("wiki_update_candidates", [])),
                    json_dumps(final_payload.get("labels", [])),
                    int(meaningful),
                    snapshot_path,
                    question_id,
                ),
            )
            if cur.rowcount == 0:
                self._log(con, question_id, "warning", "question finish ignored because it was cancelled", {})
                return False
            self._log(con, question_id, "info", "question finished", {"meaningful": meaningful, "snapshot_path": snapshot_path})
        return True

    def fail_question(self, question_id: str, error: str) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                "UPDATE questions SET status = ?, finished_at = ?, error = ? WHERE id = ? AND status != 'cancelled'",
                ("failed", utc_now(), error, question_id),
            )
            self._log(con, question_id, "error", "question failed", {"error": error})

    def request_cancel(self, question_id: str) -> bool:
        with self._lock, self._connect() as con:
            row = con.execute("SELECT status FROM questions WHERE id = ?", (question_id,)).fetchone()
            if not row:
                return False
            if row["status"] not in {"queued", "running"}:
                return True
            con.execute(
                "UPDATE questions SET status = ?, cancelled_at = ? WHERE id = ?",
                ("cancelled", utc_now(), question_id),
            )
            self._log(con, question_id, "warning", "question cancelled", {})
        return True

    def is_cancelled(self, question_id: str) -> bool:
        row = self.get_question_row(question_id)
        return bool(row and row.get("status") == "cancelled")

    def has_running_question(self) -> str | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT id FROM questions WHERE status IN ('queued', 'running') ORDER BY created_at LIMIT 1"
            ).fetchone()
        return row["id"] if row else None

    def create_source_run(self, question_id: str, source: str) -> int:
        with self._lock, self._connect() as con:
            cur = con.execute(
                "INSERT INTO source_runs(question_id, source, status, started_at) VALUES (?, ?, ?, ?)",
                (question_id, source, "running", utc_now()),
            )
            run_id = int(cur.lastrowid)
            self._log(con, question_id, "info", f"{source} worker started", {"source_run_id": run_id})
        return run_id

    def finish_source_run(self, run_id: int, question_id: str, source: str, status: str, answer_markdown: str, error: str | None = None) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                "UPDATE source_runs SET status = ?, finished_at = ?, answer_markdown = ?, error = ? WHERE id = ?",
                (status, utc_now(), answer_markdown, error, run_id),
            )
            level = "error" if status == "failed" else "info"
            self._log(con, question_id, level, f"{source} worker {status}", {"source_run_id": run_id, "error": error})

    def insert_evidence(self, question_id: str, source_run_id: int, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        with self._lock, self._connect() as con:
            con.executemany(
                """
                INSERT INTO evidence_items(
                    question_id, source_run_id, source_type, title, video_id,
                    timecode, url, path, quote, excerpt, rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        question_id,
                        source_run_id,
                        item.get("source_type"),
                        item.get("title"),
                        item.get("video_id"),
                        item.get("timecode"),
                        item.get("url"),
                        item.get("path"),
                        item.get("quote"),
                        item.get("excerpt"),
                        int(item.get("rank") or idx),
                    )
                    for idx, item in enumerate(items, start=1)
                ],
            )
            self._log(con, question_id, "info", "evidence stored", {"source_run_id": source_run_id, "count": len(items)})

    def log(self, question_id: str | None, level: str, message: str, data: dict[str, Any] | None = None) -> None:
        with self._lock, self._connect() as con:
            self._log(con, question_id, level, message, data or {})

    def _log(self, con: sqlite3.Connection, question_id: str | None, level: str, message: str, data: dict[str, Any]) -> None:
        con.execute(
            "INSERT INTO answer_logs(question_id, level, message, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (question_id, level, message, json_dumps(data), utc_now()),
        )

    def create_answer_snapshot(self, question_id: str, markdown: str, reason: str) -> str:
        self.config.answers_dir.mkdir(parents=True, exist_ok=True)
        path = self.config.answers_dir / f"{question_id}.md"
        path.write_text(markdown, encoding="utf-8")
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO answer_snapshots(question_id, path, reason, created_at) VALUES (?, ?, ?, ?)",
                (question_id, str(path), reason, utc_now()),
            )
            self._log(con, question_id, "info", "answer snapshot exported", {"path": str(path), "reason": reason})
        return str(path)

    def create_wiki_update_candidate(self, question_id: str, reason: str, payload: dict[str, Any]) -> int:
        with self._lock, self._connect() as con:
            cur = con.execute(
                """
                INSERT INTO wiki_update_candidates(question_id, reason, payload_json, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (question_id, reason, json_dumps(payload), "candidate", utc_now()),
            )
            candidate_id = int(cur.lastrowid)
            self._log(
                con,
                question_id,
                "info",
                "wiki update candidate stored",
                {"candidate_id": candidate_id, "reason": reason},
            )
        return candidate_id

    def create_wiki_patch_job(self, question_id: str, reason: str, payload: dict[str, Any]) -> int:
        with self._lock, self._connect() as con:
            cur = con.execute(
                """
                INSERT INTO wiki_patch_jobs(question_id, status, reason, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (question_id, "waiting", reason, json_dumps(payload), utc_now()),
            )
            job_id = int(cur.lastrowid)
            self._log(con, question_id, "warning", "wiki patch job queued", {"job_id": job_id, "reason": reason})
        return job_id

    def claim_next_wiki_patch_job(self) -> dict[str, Any] | None:
        with self._lock, self._connect() as con:
            running = con.execute("SELECT id FROM wiki_patch_jobs WHERE status = 'running' LIMIT 1").fetchone()
            if running:
                return None
            row = con.execute(
                "SELECT * FROM wiki_patch_jobs WHERE status = 'waiting' ORDER BY id LIMIT 1"
            ).fetchone()
            if not row:
                return None
            con.execute(
                "UPDATE wiki_patch_jobs SET status = ?, started_at = ? WHERE id = ?",
                ("running", utc_now(), row["id"]),
            )
            self._log(con, row["question_id"], "info", "wiki patch job started", {"job_id": row["id"]})
        return dict(row)

    def finish_wiki_patch_job(self, job_id: int, question_id: str, status: str, error: str | None = None, changed_files: list[str] | None = None) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                "UPDATE wiki_patch_jobs SET status = ?, finished_at = ?, error = ?, changed_files_json = ? WHERE id = ?",
                (status, utc_now(), error, json_dumps(changed_files or []), job_id),
            )
            level = "error" if status == "failed" else "info"
            self._log(con, question_id, level, f"wiki patch job {status}", {"job_id": job_id, "error": error, "changed_files": changed_files or []})

    def defer_wiki_patch_job(self, job_id: int, question_id: str, reason: str) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                "UPDATE wiki_patch_jobs SET status = ?, error = ? WHERE id = ?",
                ("waiting_manual_patch", reason, job_id),
            )
            self._log(con, question_id, "warning", "wiki patch job waiting for manual/OpenClaw patch worker", {"job_id": job_id, "reason": reason})


def _empty_box(selected: bool) -> dict[str, Any]:
    return {
        "selected": selected,
        "status": "queued" if selected else "not_selected",
        "answer_markdown": "",
        "citations": [],
        "evidence": [],
        "errors": [],
    }


def _safe_load_json(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _log_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = _safe_load_json(row["data_json"]) or {}
    return {
        "level": row["level"],
        "message": row["message"],
        "created_at": row["created_at"],
        "data": data,
    }


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    question TEXT NOT NULL,
    status TEXT NOT NULL,
    selected_wikillm INTEGER NOT NULL DEFAULT 0,
    selected_obsidian INTEGER NOT NULL DEFAULT 0,
    selected_raw INTEGER NOT NULL DEFAULT 0,
    summary_answer_markdown TEXT,
    final_json TEXT,
    sources_used_footer TEXT,
    disagreements_json TEXT,
    wiki_update_candidates_json TEXT,
    labels_json TEXT,
    meaningful INTEGER NOT NULL DEFAULT 0,
    snapshot_path TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    cancelled_at TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    answer_markdown TEXT,
    error TEXT,
    log_path TEXT,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    source_run_id INTEGER NOT NULL,
    source_type TEXT,
    title TEXT,
    video_id TEXT,
    timecode TEXT,
    url TEXT,
    path TEXT,
    quote TEXT,
    excerpt TEXT,
    rank INTEGER,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY(source_run_id) REFERENCES source_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    source_run_id INTEGER,
    citation_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS answer_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    data_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wiki_update_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TEXT NOT NULL,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS answer_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    path TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wiki_patch_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    payload_json TEXT,
    changed_files_json TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_threads (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""
