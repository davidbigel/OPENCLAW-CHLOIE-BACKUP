from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from http import cookies
from typing import Mapping


AUTH_COOKIE = "mc_auth"
CSRF_COOKIE = "mc_csrf"
AUTH_MAX_AGE_SECONDS = 12 * 60 * 60


def _sign(value: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def make_auth_token(password: str, secret: str, issued_at: int | None = None) -> str:
    issued = int(issued_at if issued_at is not None else time.time())
    signature = _sign(f"{password}:{issued}", secret)
    return f"v1:{issued}:{signature}"


def verify_auth_token(
    token: str | None,
    password: str,
    secret: str,
    *,
    now: int | None = None,
    max_age_seconds: int = AUTH_MAX_AGE_SECONDS,
) -> bool:
    if not token:
        return False
    parts = token.split(":")
    if len(parts) != 3 or parts[0] != "v1":
        return False
    try:
        issued = int(parts[1])
    except ValueError:
        return False
    current = int(now if now is not None else time.time())
    if issued > current + 60 or current - issued > max_age_seconds:
        return False
    expected = make_auth_token(password, secret, issued)
    return hmac.compare_digest(token, expected)


def make_csrf_token() -> str:
    return secrets.token_urlsafe(24)


def parse_cookies(header: str | None) -> dict[str, str]:
    if not header:
        return {}
    jar = cookies.SimpleCookie()
    jar.load(header)
    return {key: morsel.value for key, morsel in jar.items()}


def make_cookie_header(
    name: str,
    value: str,
    *,
    http_only: bool,
    max_age: int | None = None,
    secure: bool = False,
) -> str:
    parts = [
        f"{name}={value}",
        "Path=/",
        "SameSite=Lax",
    ]
    if max_age is not None:
        parts.append(f"Max-Age={int(max_age)}")
    if http_only:
        parts.append("HttpOnly")
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def origin_allowed(headers: Mapping[str, str], allowed_origins: tuple[str, ...]) -> bool:
    origin = headers.get("Origin")
    if origin:
        return origin in allowed_origins
    referer = headers.get("Referer")
    if referer:
        return any(referer.startswith(origin + "/") or referer == origin for origin in allowed_origins)
    return True


def csrf_valid(headers: Mapping[str, str], cookie_values: dict[str, str]) -> bool:
    header_value = headers.get("X-CSRF-Token")
    cookie_value = cookie_values.get(CSRF_COOKIE)
    return bool(header_value and cookie_value and hmac.compare_digest(header_value, cookie_value))
