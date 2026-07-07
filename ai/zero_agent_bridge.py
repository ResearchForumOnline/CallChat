#!/usr/bin/env python3
"""Small public CallChat widget -> OpenZero bridge.

This is intentionally simple and dependency-free. Put it behind Nginx/Apache,
keep it private to approved domains, and prefer a stronger production gateway
for large public deployments.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


HOST = os.getenv("ZERO_AGENT_HOST", "127.0.0.1")
PORT = int(os.getenv("ZERO_AGENT_PORT", "8787"))
OPENZERO_BASE_URL = os.getenv("OPENZERO_BASE_URL", "http://127.0.0.1:1024").rstrip("/")
OPENZERO_API_KEY = os.getenv("OPENZERO_API_KEY", "")
OPENZERO_MODEL = os.getenv("OPENZERO_MODEL", "gemma4:e4b")
ALLOWED_ORIGINS = {x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip()}
DAILY_LIMIT = int(os.getenv("ZERO_AGENT_DAILY_LIMIT", "40"))
SITE_CONTEXT = os.getenv(
    "SITE_CONTEXT",
    "CallChat Community helps people self-host Matrix/Synapse/Element with optional OpenZero AI support.",
)

WINDOW_SECONDS = 24 * 60 * 60
RATE: dict[str, tuple[int, float]] = {}


def allowed_origin(origin: str) -> bool:
    return not ALLOWED_ORIGINS or origin in ALLOWED_ORIGINS


def rate_ok(ip: str) -> bool:
    now = time.time()
    count, reset_at = RATE.get(ip, (0, now + WINDOW_SECONDS))
    if now > reset_at:
        count, reset_at = 0, now + WINDOW_SECONDS
    if count >= DAILY_LIMIT:
        RATE[ip] = (count, reset_at)
        return False
    RATE[ip] = (count + 1, reset_at)
    return True


def fallback_reply(message: str) -> str:
    lower = message.lower()
    if "element" in lower or "login" in lower:
        return "Install Element, choose a custom homeserver, and enter your public CallChat domain. If discovery is not ready, use the Matrix API URL your admin provides."
    if "openzero" in lower or "ai" in lower or "bot" in lower:
        return "OpenZero can power the CallChat room bot and website widget through a private local bridge. Keep the Super Panel private and expose only a narrow, rate-limited endpoint."
    if "call" in lower or "video" in lower or "voice" in lower:
        return "Voice and video need TURN/coturn for reliability across mobile networks, home routers, and stricter office networks."
    if "shield" in lower or "zmath" in lower:
        return "Shield is an optional premium vault layer. This public kit documents the safe boundary without publishing private implementation code."
    return "CallChat Community is a self-host kit for Matrix/Synapse/Element with CallChat branding, optional OpenZero AI, and a clean private boundary for premium Shield features."


def ask_openzero(message: str) -> str | None:
    if not OPENZERO_API_KEY:
        return None

    payload = {
        "model": OPENZERO_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are CallChat Zero, a concise site assistant. "
                    "Help users understand CallChat, Matrix/Synapse/Element setup, OpenZero, voice/video, and safe Shield boundaries. "
                    "Do not ask for passwords, tokens, private keys, or recovery phrases. "
                    f"Site context: {SITE_CONTEXT}"
                ),
            },
            {"role": "user", "content": message[:1200]},
        ],
        "temperature": 0.45,
        "max_tokens": 260,
    }
    req = urllib.request.Request(
        f"{OPENZERO_BASE_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENZERO_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "CallChatZeroAgent/0.1"

    def do_OPTIONS(self) -> None:
        self.send_json({"ok": True})

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json({"ok": True, "openzero": bool(OPENZERO_API_KEY)})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin and not allowed_origin(origin):
            self.send_json({"error": "origin not allowed"}, 403)
            return

        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        if not rate_ok(ip):
            self.send_json({"error": "rate limited"}, 429)
            return

        length = min(int(self.headers.get("Content-Length", "0")), 4096)
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json({"error": "invalid json"}, 400)
            return

        message = str(body.get("message", "")).strip()
        if not message:
            self.send_json({"error": "empty message"}, 400)
            return

        reply = ask_openzero(message) or fallback_reply(message)
        self.send_json({"reply": reply})

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        origin = self.headers.get("Origin", "")
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if origin and allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: Any) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"CallChat Zero Agent bridge listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
