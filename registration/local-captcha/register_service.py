#!/usr/bin/env python3
"""Same-origin arithmetic CAPTCHA and restricted Synapse account creation."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable


USERNAME_RE = re.compile(r"^[a-z0-9._=-]{3,32}$")
MAX_BODY_BYTES = 4096


class PublicError(Exception):
    def __init__(self, message: str, status: int = 400, code: str = "invalid_request") -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


@dataclass
class Challenge:
    answer: str
    expires: float
    client_ip: str


class RegistrationState:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self.lock = threading.Lock()
        self.challenges: dict[str, Challenge] = {}
        self.challenge_requests: defaultdict[str, deque[float]] = defaultdict(deque)
        self.registration_requests: defaultdict[str, deque[float]] = defaultdict(deque)

    @staticmethod
    def _trim(events: deque[float], now: float, window: int) -> None:
        while events and events[0] <= now - window:
            events.popleft()

    def _allow(self, bucket: defaultdict[str, deque[float]], key: str, limit: int, window: int) -> bool:
        now = self.clock()
        events = bucket[key]
        self._trim(events, now, window)
        if len(events) >= limit:
            return False
        events.append(now)
        return True

    def _prune_challenges(self, now: float) -> None:
        expired = [token for token, challenge in self.challenges.items() if challenge.expires <= now]
        for token in expired:
            self.challenges.pop(token, None)

    def issue_challenge(self, client_ip: str) -> dict[str, object]:
        with self.lock:
            if not self._allow(self.challenge_requests, client_ip, 30, 600):
                raise PublicError("Too many CAPTCHA requests. Wait a few minutes and try again.", 429, "rate_limited")
            now = self.clock()
            self._prune_challenges(now)
            if len(self.challenges) >= 10_000:
                raise PublicError("Registration protection is busy. Try again shortly.", 503, "busy")
            left = secrets.randbelow(9) + 2
            right = secrets.randbelow(9) + 2
            token = secrets.token_urlsafe(24)
            self.challenges[token] = Challenge(str(left + right), now + 300, client_ip)
            return {"challenge_id": token, "prompt": f"{left} + {right} =", "expires_in": 300}

    def consume_challenge(self, client_ip: str, token: str, answer: str) -> None:
        with self.lock:
            if not self._allow(self.registration_requests, client_ip, 5, 3600):
                raise PublicError("Too many account attempts. Wait before trying again.", 429, "rate_limited")
            now = self.clock()
            self._prune_challenges(now)
            challenge = self.challenges.pop(token, None)
            if challenge is None or challenge.expires <= now or challenge.client_ip != client_ip:
                raise PublicError("The CAPTCHA expired. Load a new question and try again.", 400, "captcha_expired")
            if not hmac.compare_digest(challenge.answer, answer.strip()):
                raise PublicError("That CAPTCHA answer is incorrect. Try the new question.", 400, "captcha_incorrect")


def validate_account(username: object, password: object) -> tuple[str, str]:
    clean_username = str(username or "").strip().lower()
    clean_password = password if isinstance(password, str) else ""
    if not USERNAME_RE.fullmatch(clean_username):
        raise PublicError("Use 3-32 lowercase letters, numbers, dots, underscores, equals signs, or hyphens.")
    if not 12 <= len(clean_password) <= 128:
        raise PublicError("Use a password between 12 and 128 characters.")
    return clean_username, clean_password


def registration_mac(secret: str, nonce: str, username: str, password: str) -> str:
    # Synapse's shared-secret registration protocol mandates HMAC-SHA1 here;
    # this authenticates one loopback request and is not a password hash.
    # codeql[py/weak-sensitive-data-hashing]
    digest = hmac.new(secret.encode("utf-8"), digestmod=hashlib.sha1)
    for value in (nonce, username, password):
        digest.update(value.encode("utf-8"))
        digest.update(b"\x00")
    digest.update(b"notadmin")
    return digest.hexdigest()


class SynapseRegistrar:
    def __init__(self, shared_secret: str, endpoint: str = "http://127.0.0.1:8008/_synapse/admin/v1/register") -> None:
        self.shared_secret = shared_secret
        self.endpoint = endpoint

    @staticmethod
    def _json_request(request: urllib.request.Request) -> tuple[int, dict[str, object]]:
        try:
            with urllib.request.urlopen(request, timeout=6) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                payload = json.loads(error.read().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {}
            return error.code, payload
        except (OSError, TimeoutError) as error:
            raise PublicError("The account service is temporarily unavailable.", 503, "homeserver_unavailable") from error

    def register(self, username: str, password: str) -> str:
        status, nonce_payload = self._json_request(urllib.request.Request(self.endpoint, method="GET"))
        nonce = nonce_payload.get("nonce")
        if status != 200 or not isinstance(nonce, str):
            raise PublicError("The account service is temporarily unavailable.", 503, "homeserver_unavailable")
        body = json.dumps({
            "nonce": nonce,
            "username": username,
            "password": password,
            "mac": registration_mac(self.shared_secret, nonce, username, password),
            "admin": False,
        }).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=body, method="POST", headers={"Content-Type": "application/json"})
        status, payload = self._json_request(request)
        if status == 200:
            return str(payload.get("user_id") or f"@{username}:callchat.org")
        errcode = payload.get("errcode")
        if errcode == "M_USER_IN_USE":
            raise PublicError("That username is already registered. Try another.", 409, "username_in_use")
        if errcode == "M_INVALID_USERNAME":
            raise PublicError("That username is not allowed.", 400, "invalid_username")
        if errcode == "M_WEAK_PASSWORD":
            raise PublicError("Choose a stronger password.", 400, "weak_password")
        raise PublicError("The homeserver did not create the account. Try again later.", 502, "homeserver_error")


class RegistrationHandler(BaseHTTPRequestHandler):
    server_version = "CallChatRegister/1"
    state: RegistrationState
    registrar: SynapseRegistrar
    allowed_origin: str

    def log_message(self, format: str, *args: object) -> None:
        return

    def _headers(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._headers(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _client_ip(self) -> str:
        candidate = self.headers.get("X-Real-IP", self.client_address[0]).strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return self.client_address[0]

    def _same_origin(self) -> None:
        if self.headers.get("X-CallChat-Same-Origin", "") != "1":
            raise PublicError("Cross-site registration is not allowed.", 403, "origin_rejected")
        origin = self.headers.get("Origin", "")
        if origin and origin != self.allowed_origin:
            raise PublicError("Cross-site registration is not allowed.", 403, "origin_rejected")

    def do_GET(self) -> None:
        try:
            if self.path == "/health":
                self._json(200, {"ok": True})
                return
            if self.path != "/v1/challenge":
                raise PublicError("Not found.", 404, "not_found")
            self._same_origin()
            self._json(200, self.state.issue_challenge(self._client_ip()))
        except PublicError as error:
            self._json(error.status, {"ok": False, "code": error.code, "error": error.message})

    def do_POST(self) -> None:
        try:
            if self.path != "/v1/register":
                raise PublicError("Not found.", 404, "not_found")
            self._same_origin()
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise PublicError("Invalid request size.") from error
            if length < 2 or length > MAX_BODY_BYTES:
                raise PublicError("Invalid request size.", 413, "request_too_large")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise PublicError("Invalid JSON request.") from error
            if not isinstance(payload, dict):
                raise PublicError("Invalid registration request.")
            username, password = validate_account(payload.get("username"), payload.get("password"))
            token = str(payload.get("challenge_id") or "")
            answer = str(payload.get("captcha_answer") or "")
            self.state.consume_challenge(self._client_ip(), token, answer)
            user_id = self.registrar.register(username, password)
            self._json(201, {"ok": True, "user_id": user_id})
        except PublicError as error:
            self._json(error.status, {"ok": False, "code": error.code, "error": error.message})


def load_secret(path: str) -> str:
    secret = Path(path).read_text(encoding="utf-8").strip()
    if len(secret) < 32:
        raise RuntimeError("Registration secret is unavailable")
    return secret


def main() -> None:
    host = os.environ.get("CALLCHAT_REGISTER_HOST", "127.0.0.1")
    port = int(os.environ.get("CALLCHAT_REGISTER_PORT", "1031"))
    origin = os.environ.get("CALLCHAT_ALLOWED_ORIGIN", "https://callchat.org")
    secret_path = os.environ.get("CALLCHAT_REGISTRATION_SECRET_FILE", "/etc/callchat-register/registration-secret")
    state = RegistrationState()
    registrar = SynapseRegistrar(load_secret(secret_path))
    handler = type("ConfiguredRegistrationHandler", (RegistrationHandler,), {
        "state": state,
        "registrar": registrar,
        "allowed_origin": origin,
    })
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
