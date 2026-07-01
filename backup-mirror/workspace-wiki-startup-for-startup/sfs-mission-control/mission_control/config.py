from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True)
class Config:
    app_root: Path
    workspace_root: Path
    public_host: str
    public_port: int
    public_scheme: str
    public_tls_cert: Path | None
    public_tls_key: Path | None
    private_host: str
    private_port: int
    public_password: str
    cookie_secret: str
    internal_secret: str
    snoracle_mode: str
    snoracle_agent_id: str
    snoracle_session_id: str | None
    snoracle_route_label: str
    allowed_origins: tuple[str, ...]
    db_path: Path
    log_dir: Path
    answers_dir: Path
    static_dir: Path
    wikillm_dir: Path
    raw_dir: Path
    source_lists_dir: Path


def load_config() -> Config:
    app_root = Path(__file__).resolve().parents[1]
    workspace_root = Path(os.environ.get("MC_WORKSPACE_ROOT", app_root.parent)).resolve()
    runtime_root = workspace_root / "kb" / "mission-control"
    tls_root = runtime_root / "tls"
    public_port = int(os.environ.get("MC_PUBLIC_PORT", "40006"))
    private_port = int(os.environ.get("MC_PRIVATE_PORT", "40007"))
    public_host = os.environ.get("MC_PUBLIC_HOST", "0.0.0.0")
    private_host = os.environ.get("MC_PRIVATE_HOST", "127.0.0.1")
    public_tls_cert = _optional_runtime_path(
        os.environ.get("MC_PUBLIC_TLS_CERT"),
        tls_root / "public.crt",
    )
    public_tls_key = _optional_runtime_path(
        os.environ.get("MC_PUBLIC_TLS_KEY"),
        tls_root / "public.key",
    )
    public_scheme = "https" if public_tls_cert and public_tls_key else "http"
    public_password = os.environ.get("MC_PUBLIC_PASSWORD", "3d20")
    cookie_secret = os.environ.get("MC_COOKIE_SECRET") or _runtime_secret(runtime_root, "cookie_secret")
    internal_secret = os.environ.get("MC_INTERNAL_SECRET") or _runtime_secret(runtime_root, "internal_secret")
    snoracle_mode = os.environ.get("MC_SNORACLE_MODE", "openclaw").strip().lower()
    snoracle_agent_id = (
        os.environ.get("MC_SNORACLE_AGENT_ID", "").strip()
        or _agent_id_from_session_key(os.environ.get("MC_SNORACLE_SESSION_KEY"))
        or _discover_current_agent_id(workspace_root)
    )
    snoracle_session_id = _resolve_session_id(
        os.environ.get("MC_SNORACLE_SESSION_ID") or os.environ.get("MC_SNORACLE_SESSION_KEY")
    )
    if snoracle_session_id:
        snoracle_route_label = f"session-id:{snoracle_session_id}"
    else:
        snoracle_route_label = f"agent:{snoracle_agent_id}:main"

    allowed = set()
    for scheme in {"http", "https"}:
        allowed.update(
            {
                f"{scheme}://187.124.10.241:{public_port}",
                f"{scheme}://localhost:{public_port}",
                f"{scheme}://127.0.0.1:{public_port}",
            }
        )
    extra_origins = os.environ.get("MC_ALLOWED_ORIGINS", "")
    for item in extra_origins.split(","):
        item = item.strip()
        if item:
            allowed.add(item)

    return Config(
        app_root=app_root,
        workspace_root=workspace_root,
        public_host=public_host,
        public_port=public_port,
        public_scheme=public_scheme,
        public_tls_cert=public_tls_cert,
        public_tls_key=public_tls_key,
        private_host=private_host,
        private_port=private_port,
        public_password=public_password,
        cookie_secret=cookie_secret,
        internal_secret=internal_secret,
        snoracle_mode=snoracle_mode,
        snoracle_agent_id=snoracle_agent_id,
        snoracle_session_id=snoracle_session_id,
        snoracle_route_label=snoracle_route_label,
        allowed_origins=tuple(sorted(allowed)),
        db_path=runtime_root / "mission-control.sqlite3",
        log_dir=runtime_root / "logs",
        answers_dir=runtime_root / "answers",
        static_dir=app_root / "static",
        wikillm_dir=workspace_root / "kb" / "wikillm",
        raw_dir=workspace_root / "kb" / "sources" / "raw",
        source_lists_dir=workspace_root / "kb" / "sources" / "lists",
    )


def _runtime_secret(runtime_root: Path, key: str) -> str:
    runtime_root.mkdir(parents=True, exist_ok=True)
    path = runtime_root / ".secrets.json"
    data: dict[str, str] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = {str(k): str(v) for k, v in loaded.items()}
        except json.JSONDecodeError:
            data = {}
    if not data.get(key):
        data[key] = secrets.token_urlsafe(48)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return data[key]


def _optional_runtime_path(value: str | None, default_path: Path) -> Path | None:
    text = str(value or "").strip()
    if text:
        path = Path(text).expanduser().resolve()
        return path if path.exists() else None
    return default_path if default_path.exists() else None


def _discover_current_agent_id(workspace_root: Path) -> str:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        parts = Path(codex_home).resolve().parts
        try:
            agents_index = parts.index("agents")
        except ValueError:
            agents_index = -1
        if agents_index >= 0 and agents_index + 1 < len(parts):
            return parts[agents_index + 1]
    name = workspace_root.name
    if name.startswith("workspace-") and len(name) > len("workspace-"):
        return name.removeprefix("workspace-")
    return "main"


def _resolve_session_id(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        UUID(text)
    except ValueError:
        return None
    return text


def _agent_id_from_session_key(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text.startswith("agent:"):
        return None
    parts = text.split(":")
    if len(parts) < 3 or not parts[1].strip():
        return None
    return parts[1].strip()
