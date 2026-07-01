from __future__ import annotations

import argparse
import http.client
import json
import logging
import mimetypes
import ssl
import time
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import Config, load_config
from .db import Store
from .logging_setup import configure_logging
from .security import (
    AUTH_COOKIE,
    CSRF_COOKIE,
    AUTH_MAX_AGE_SECONDS,
    csrf_valid,
    make_auth_token,
    make_cookie_header,
    make_csrf_token,
    origin_allowed,
    parse_cookies,
    verify_auth_token,
)
from .service import MissionControlService


LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="SFS Mission Control")
    parser.add_argument("--public-port", type=int)
    parser.add_argument("--private-port", type=int)
    args = parser.parse_args()

    config = load_config()
    if args.public_port:
        object.__setattr__(config, "public_port", args.public_port)
    if args.private_port:
        object.__setattr__(config, "private_port", args.private_port)
    configure_logging(config)
    store = Store(config)
    store.init()
    recovered = store.recover_incomplete_questions()
    if recovered:
        LOGGER.warning("recovered %s incomplete question(s) left by a previous mission-control process", recovered)
    service = MissionControlService(config, store)

    private_server = ThreadingHTTPServer(
        (config.private_host, config.private_port),
        partial(PrivateHandler, config=config, service=service),
    )
    public_server = ThreadingHTTPServer(
        (config.public_host, config.public_port),
        partial(PublicHandler, config=config, service=service),
    )
    if config.public_scheme == "https":
        if not config.public_tls_cert or not config.public_tls_key:
            raise RuntimeError("HTTPS requested without both TLS cert and key paths")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(config.public_tls_cert), str(config.public_tls_key))
        public_server.socket = context.wrap_socket(public_server.socket, server_side=True)

    import threading

    private_thread = threading.Thread(target=private_server.serve_forever, name="private-server", daemon=True)
    private_thread.start()
    LOGGER.info("private server listening on %s:%s", config.private_host, config.private_port)
    LOGGER.info("%s public server listening on %s:%s", config.public_scheme.upper(), config.public_host, config.public_port)
    try:
        public_server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("shutting down")
    finally:
        public_server.shutdown()
        private_server.shutdown()


class HandlerBase(BaseHTTPRequestHandler):
    server_version = "SFS-Mission-Control/1.0"

    def __init__(self, *args: Any, config: Config, service: MissionControlService, **kwargs: Any):
        self.config = config
        self.service = service
        super().__init__(*args, **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.address_string(), fmt % args)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length > 2_000_000:
            raise ValueError("request body too large")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, status: int, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class PublicHandler(HandlerBase):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if query.get("p", [""])[0] == self.config.public_password:
            auth = make_auth_token(self.config.public_password, self.config.cookie_secret)
            csrf = make_csrf_token()
            self.send_response(302)
            self.send_header(
                "Set-Cookie",
                make_cookie_header(
                    AUTH_COOKIE,
                    auth,
                    http_only=True,
                    max_age=AUTH_MAX_AGE_SECONDS,
                    secure=self.config.public_scheme == "https",
                ),
            )
            self.send_header(
                "Set-Cookie",
                make_cookie_header(
                    CSRF_COOKIE,
                    csrf,
                    http_only=False,
                    max_age=AUTH_MAX_AGE_SECONDS,
                    secure=self.config.public_scheme == "https",
                ),
            )
            self.send_header("Location", "/")
            self.end_headers()
            return

        if parsed.path == "/health":
            self.send_json(200, {"status": "ok", "public": True})
            return

        if parsed.path.startswith("/api/questions/") and parsed.path.endswith("/events"):
            if not self._authenticated():
                self.send_json(401, {"status": "unauthorized"})
                return
            question_id = parsed.path.split("/")[3]
            self._send_events(question_id)
            return

        if parsed.path.startswith("/api/"):
            if not self._authenticated():
                self.send_json(401, {"status": "unauthorized"})
                return
            self._proxy_to_private("GET", parsed.path, None)
            return

        if not self._authenticated():
            self._send_login()
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            self.send_json(404, {"status": "not_found"})
            return
        cookies = parse_cookies(self.headers.get("Cookie"))
        if not self._authenticated(cookies):
            self.send_json(401, {"status": "unauthorized"})
            return
        if not origin_allowed(self.headers, self.config.allowed_origins):
            self.send_json(403, {"status": "forbidden", "message": "bad origin"})
            return
        if not csrf_valid(self.headers, cookies):
            self.send_json(403, {"status": "forbidden", "message": "bad csrf"})
            return
        try:
            body = self.read_json()
        except Exception as exc:
            self.send_json(400, {"status": "bad_request", "message": str(exc)})
            return
        self._proxy_to_private("POST", parsed.path, body)

    def _authenticated(self, cookie_values: dict[str, str] | None = None) -> bool:
        cookies = cookie_values or parse_cookies(self.headers.get("Cookie"))
        return verify_auth_token(cookies.get(AUTH_COOKIE), self.config.public_password, self.config.cookie_secret)

    def _send_login(self) -> None:
        self.send_text(
            401,
            """
<!doctype html>
<html lang="he" dir="rtl">
<meta charset="utf-8">
<title>Mission Control</title>
<body style="font-family: system-ui; max-width: 720px; margin: 80px auto; line-height: 1.5;">
<h1>Mission Control</h1>
<p>כניסה דרך שער v1:</p>
<p><a href="/?p=3d20">פתח עם ?p=3d20</a></p>
</body>
</html>
""".strip(),
            "text/html; charset=utf-8",
        )

    def _serve_static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"
        target = (self.config.static_dir / path.lstrip("/")).resolve()
        try:
            target.relative_to(self.config.static_dir.resolve())
        except ValueError:
            self.send_json(403, {"status": "forbidden"})
            return
        if not target.exists() or not target.is_file():
            self.send_json(404, {"status": "not_found"})
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _proxy_to_private(self, method: str, path: str, body: dict[str, Any] | None) -> None:
        payload = json.dumps(body or {}, ensure_ascii=False).encode("utf-8") if method == "POST" else None
        conn = http.client.HTTPConnection(self.config.private_host, self.config.private_port, timeout=120)
        headers = {"X-MC-Internal-Secret": self.config.internal_secret}
        if payload is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        try:
            conn.request(method, path, payload, headers)
            resp = conn.getresponse()
            data = resp.read()
            self.send_response(resp.status)
            for name, value in resp.getheaders():
                if name.lower() not in {"connection", "transfer-encoding", "server", "date"}:
                    self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self.send_json(502, {"status": "private_backend_error", "message": str(exc)})
        finally:
            conn.close()

    def _send_events(self, question_id: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last_payload = ""
        deadline = time.time() + 120
        while time.time() < deadline:
            payload = self.service.get_question(question_id) or {"status": "not_found"}
            text = json.dumps(payload, ensure_ascii=False)
            if text != last_payload:
                self.wfile.write(f"data: {text}\n\n".encode("utf-8"))
                self.wfile.flush()
                last_payload = text
            if payload.get("status") in {"done", "failed", "cancelled", "not_found"}:
                break
            time.sleep(1)


class PrivateHandler(HandlerBase):
    def do_GET(self) -> None:
        if not self._allowed_private():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json(200, {"status": "ok", "private": True})
            return
        if parsed.path == "/api/questions":
            self.send_json(200, self.service.list_questions())
            return
        if parsed.path.startswith("/api/questions/"):
            question_id = parsed.path.split("/")[3]
            payload = self.service.get_question(question_id)
            if not payload:
                self.send_json(404, {"status": "not_found"})
                return
            self.send_json(200, payload)
            return
        self.send_json(404, {"status": "not_found"})

    def do_POST(self) -> None:
        if not self._allowed_private():
            return
        parsed = urlparse(self.path)
        try:
            body = self.read_json()
        except Exception as exc:
            self.send_json(400, {"status": "bad_request", "message": str(exc)})
            return
        if parsed.path == "/api/ask":
            question = str(body.get("question") or "")
            sources = body.get("sources") if isinstance(body.get("sources"), dict) else {}
            self.send_json(200, self.service.ask(question, sources))
            return
        if parsed.path.startswith("/api/questions/") and parsed.path.endswith("/cancel"):
            question_id = parsed.path.split("/")[3]
            self.send_json(200, self.service.cancel(question_id))
            return
        if parsed.path.startswith("/api/questions/") and parsed.path.endswith("/rerun"):
            question_id = parsed.path.split("/")[3]
            sources = body.get("sources") if isinstance(body.get("sources"), dict) else None
            self.send_json(200, self.service.rerun(question_id, sources))
            return
        if parsed.path.startswith("/api/questions/") and parsed.path.endswith("/toggle-thread"):
            question_id = parsed.path.split("/")[3]
            self.send_json(200, self.service.toggle_thread(question_id))
            return
        self.send_json(404, {"status": "not_found"})

    def _allowed_private(self) -> bool:
        client_ip = self.client_address[0]
        if client_ip not in {"127.0.0.1", "::1"}:
            self.send_json(403, {"status": "forbidden"})
            return False
        if self.headers.get("X-MC-Internal-Secret") != self.config.internal_secret:
            self.send_json(403, {"status": "forbidden"})
            return False
        return True


if __name__ == "__main__":
    main()
