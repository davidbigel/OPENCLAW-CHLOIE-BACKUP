from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "notebooklm"


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    return env


def upstream_bin() -> str:
    override = os.environ.get("NOTEBOOKLM_BIN")
    if override:
        return override
    if DEFAULT_BIN.exists():
        return str(DEFAULT_BIN)
    return "notebooklm"


def active_profile() -> str:
    return os.environ.get("NOTEBOOKLM_PROFILE", "default")


def notebooklm_home() -> Path:
    override = os.environ.get("NOTEBOOKLM_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".notebooklm"


def profile_dir() -> Path:
    return notebooklm_home() / "profiles" / active_profile()


def storage_state_path() -> Path:
    return profile_dir() / "storage_state.json"


def run_upstream(
    args: Sequence[str],
    capture: bool = False,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [upstream_bin(), *args]
    env = build_env()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        cmd,
        env=env,
        text=True,
        capture_output=capture,
        check=False,
    )


def print_capabilities() -> int:
    data = {
        "notebooks": ["list", "create", "use", "rename", "delete", "summary", "metadata"],
        "sources": [
            "add",
            "add-drive",
            "add-research",
            "list",
            "get",
            "fulltext",
            "guide",
            "refresh",
            "rename",
            "delete",
            "clean",
            "stale",
            "wait",
        ],
        "chat": ["ask", "configure", "history"],
        "notes": ["list", "create", "get", "save", "rename", "delete"],
        "artifacts": {
            "generate": [
                "audio",
                "cinematic-video",
                "data-table",
                "flashcards",
                "infographic",
                "mind-map",
                "quiz",
                "report",
                "revise-slide",
                "slide-deck",
                "video",
            ],
            "manage": ["list", "get", "rename", "delete", "export", "poll", "wait", "retry", "suggestions"],
            "download": [
                "audio",
                "cinematic-video",
                "data-table",
                "flashcards",
                "infographic",
                "mind-map",
                "quiz",
                "report",
                "slide-deck",
                "video",
            ],
        },
        "sharing": ["status", "view-level", "add", "update", "remove", "public"],
        "profiles": ["list", "create", "switch", "rename", "delete"],
        "auth": ["login", "auth check", "auth inspect", "auth logout", "auth refresh"],
        "local_helpers": ["auth-bootstrap", "access-account", "doctor", "raw"],
    }
    print(json.dumps(data, indent=2))
    return 0


def load_json_file(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def persist_storage_state(source: Path) -> Path:
    payload = load_json_file(source)
    if not isinstance(payload, dict):
        raise ValueError("storage state must be a JSON object")
    if "cookies" not in payload or not isinstance(payload["cookies"], list):
        raise ValueError("storage state must contain a cookies array")

    target = storage_state_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    os.chmod(target, 0o600)
    return target


def print_result(payload: dict[str, object], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2))
        return int(payload.get("exit_code", 0))

    print(str(payload.get("message", "")))
    details = payload.get("details")
    if isinstance(details, str) and details:
        print(details)
    next_step = payload.get("next_step")
    if isinstance(next_step, str) and next_step:
        print(next_step)
    return int(payload.get("exit_code", 0))


def validate_auth(expected_email: str | None = None) -> dict[str, object]:
    auth = run_upstream(["auth", "check", "--json"], capture=True)

    try:
        auth_payload = json.loads(auth.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "exit_code": auth.returncode or 1,
            "message": "Auth validation failed.",
            "details": (auth.stderr or auth.stdout).strip(),
        }

    if auth_payload.get("status") != "ok":
        return {
            "ok": False,
            "exit_code": 1,
            "message": "NotebookLM auth is still not usable.",
            "details": json.dumps(auth_payload, indent=2),
        }

    notebooks = run_upstream(["list", "--json"], capture=True)
    notebook_payload: object | None = None
    if notebooks.stdout.strip():
        try:
            notebook_payload = json.loads(notebooks.stdout)
        except json.JSONDecodeError:
            notebook_payload = notebooks.stdout.strip()

    payload: dict[str, object] = {
        "ok": notebooks.returncode == 0,
        "exit_code": notebooks.returncode,
        "message": "NotebookLM auth is ready.",
        "auth": auth_payload,
        "notebooks": notebook_payload,
        "storage_path": str(storage_state_path()),
    }
    if expected_email:
        payload["expected_email"] = expected_email
    if notebooks.returncode != 0:
        payload["message"] = "NotebookLM auth exists, but listing notebooks failed."
        payload["details"] = (notebooks.stderr or notebooks.stdout).strip()
    return payload


def auth_bootstrap(
    email: str | None,
    browser_cookies: str | None,
    storage_state: str | None,
    auth_json_file: str | None,
    interactive: bool,
    as_json: bool,
) -> int:
    modes = [bool(browser_cookies), bool(storage_state), bool(auth_json_file), bool(interactive)]
    if sum(modes) != 1:
        return print_result(
            {
                "ok": False,
                "exit_code": 2,
                "message": "Choose exactly one auth bootstrap mode.",
                "next_step": "Use one of: --browser-cookies, --storage-state, --auth-json-file, or --interactive.",
            },
            as_json,
        )

    if browser_cookies:
        args = ["login", "--browser-cookies", browser_cookies]
        if email:
            args.extend(["--account", email])
        result = run_upstream(args, capture=True)
        if result.returncode != 0:
            return print_result(
                {
                    "ok": False,
                    "exit_code": result.returncode or 1,
                    "message": "Browser-cookie auth bootstrap failed.",
                    "details": (result.stderr or result.stdout).strip(),
                },
                as_json,
            )
        return print_result(validate_auth(email), as_json)

    if storage_state:
        source = Path(storage_state).expanduser().resolve()
        try:
            target = persist_storage_state(source)
        except Exception as exc:
            return print_result(
                {
                    "ok": False,
                    "exit_code": 1,
                    "message": "Storage-state import failed.",
                    "details": f"{type(exc).__name__}: {exc}",
                },
                as_json,
            )
        payload = validate_auth(email)
        payload["imported_storage_state"] = str(target)
        return print_result(payload, as_json)

    if auth_json_file:
        source = Path(auth_json_file).expanduser().resolve()
        try:
            payload_obj = load_json_file(source)
        except Exception as exc:
            return print_result(
                {
                    "ok": False,
                    "exit_code": 1,
                    "message": "Auth JSON load failed.",
                    "details": f"{type(exc).__name__}: {exc}",
                },
                as_json,
            )

        inline_env = {"NOTEBOOKLM_AUTH_JSON": json.dumps(payload_obj)}
        auth = run_upstream(["auth", "check", "--json"], capture=True, extra_env=inline_env)
        try:
            auth_payload = json.loads(auth.stdout)
        except json.JSONDecodeError:
            return print_result(
                {
                    "ok": False,
                    "exit_code": auth.returncode or 1,
                    "message": "Inline auth JSON validation failed.",
                    "details": (auth.stderr or auth.stdout).strip(),
                },
                as_json,
            )

        notebooks = run_upstream(["list", "--json"], capture=True, extra_env=inline_env)
        payload = {
            "ok": auth_payload.get("status") == "ok" and notebooks.returncode == 0,
            "exit_code": notebooks.returncode if auth_payload.get("status") == "ok" else 1,
            "message": "Inline auth JSON is ready." if auth_payload.get("status") == "ok" else "Inline auth JSON is not usable.",
            "auth": auth_payload,
            "notebooks": json.loads(notebooks.stdout) if notebooks.returncode == 0 and notebooks.stdout.strip() else None,
            "auth_json_file": str(source),
        }
        if email:
            payload["expected_email"] = email
        if auth_payload.get("status") != "ok":
            payload["details"] = json.dumps(auth_payload, indent=2)
        elif notebooks.returncode != 0:
            payload["details"] = (notebooks.stderr or notebooks.stdout).strip()
        return print_result(payload, as_json)

    result = run_upstream(["login"])
    if result.returncode != 0:
        return print_result(
            {
                "ok": False,
                "exit_code": result.returncode or 1,
                "message": "Interactive login failed.",
                "next_step": "Run nblm-all raw login in a desktop session where you can complete Google sign-in.",
            },
            as_json,
        )
    return print_result(validate_auth(email), as_json)


def access_account(email: str, as_json: bool) -> int:
    auth = run_upstream(["auth", "check", "--json"], capture=True)

    try:
        auth_payload = json.loads(auth.stdout)
    except json.JSONDecodeError:
        sys.stderr.write(auth.stderr or auth.stdout)
        return auth.returncode or 1

    if auth_payload.get("status") != "ok":
        inspect = run_upstream(["auth", "inspect", "--browser", "chrome", "--json"], capture=True)
        result = {
            "ok": False,
            "email": email,
            "reason": "not_authenticated",
            "auth": auth_payload,
            "browser_inspect": inspect.stdout.strip() or inspect.stderr.strip(),
            "next_step": (
                "Authenticate first. If this machine has Chrome cookies for the account, run "
                "nblm-all raw login --browser-cookies chrome --account " + email + ". "
                "Otherwise run nblm-all raw login in an interactive desktop session."
            ),
        }
        if as_json:
            print(json.dumps(result, indent=2))
        else:
            print("NotebookLM is not authenticated for " + email + ".")
            print(result["next_step"])
            if result["browser_inspect"]:
                print(result["browser_inspect"])
        return 1

    notebooks = run_upstream(["list", "--json"], capture=True)
    if as_json:
        payload = {
            "ok": notebooks.returncode == 0,
            "email": email,
            "auth": auth_payload,
            "notebooks": json.loads(notebooks.stdout) if notebooks.returncode == 0 and notebooks.stdout.strip() else None,
            "stderr": (notebooks.stderr or "").strip(),
        }
        print(json.dumps(payload, indent=2))
    else:
        if notebooks.returncode != 0:
            sys.stderr.write(notebooks.stderr or notebooks.stdout)
            return notebooks.returncode
        print(notebooks.stdout.rstrip())
    return notebooks.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nblm-all",
        description="Workspace-local wrapper around the full notebooklm CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("capabilities", help="Print the supported NotebookLM capability surface.")
    subparsers.add_parser("doctor", help="Run notebooklm doctor.")

    bootstrap = subparsers.add_parser("auth-bootstrap", help="Bootstrap NotebookLM auth for a specific account.")
    bootstrap.add_argument("--email", help="Expected Google account email.")
    bootstrap.add_argument("--browser-cookies", help="Import auth from an installed browser profile, such as chrome.")
    bootstrap.add_argument("--storage-state", help="Import a Playwright storage_state.json file into the active NotebookLM profile.")
    bootstrap.add_argument("--auth-json-file", help="Use a JSON file as NOTEBOOKLM_AUTH_JSON for validation and notebook access.")
    bootstrap.add_argument("--interactive", action="store_true", help="Launch the upstream interactive login flow.")
    bootstrap.add_argument("--json", action="store_true", help="Emit machine-readable output.")

    access = subparsers.add_parser("access-account", help="Check auth and list notebooks for an account.")
    access.add_argument("--email", required=True, help="Expected Google account email.")
    access.add_argument("--json", action="store_true", help="Emit machine-readable output.")

    raw = subparsers.add_parser("raw", help="Pass arguments through to the upstream notebooklm CLI.")
    raw.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for notebooklm.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "capabilities":
        return print_capabilities()
    if args.command == "doctor":
        result = run_upstream(["doctor"])
        return result.returncode
    if args.command == "auth-bootstrap":
        return auth_bootstrap(
            email=args.email,
            browser_cookies=args.browser_cookies,
            storage_state=args.storage_state,
            auth_json_file=args.auth_json_file,
            interactive=args.interactive,
            as_json=args.json,
        )
    if args.command == "access-account":
        return access_account(args.email, args.json)
    if args.command == "raw":
        forwarded = list(args.args)
        if forwarded and forwarded[0] == "--":
            forwarded = forwarded[1:]
        if not forwarded:
            parser.error("raw requires notebooklm arguments after -- or directly after raw.")
        result = run_upstream(forwarded)
        return result.returncode

    parser.error("unknown command: " + str(args.command))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
