#!/usr/bin/env python3
"""Small public CallChat widget -> OpenZero bridge.

This is intentionally simple and dependency-free. Put it behind Nginx/Apache,
keep it private to approved domains, and prefer a stronger production gateway
for large public deployments.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import provider_control


HOST = os.getenv("ZERO_AGENT_HOST", "127.0.0.1")
PORT = int(os.getenv("ZERO_AGENT_PORT", "8787"))
OPENZERO_BASE_URL = os.getenv("OPENZERO_BASE_URL", "http://127.0.0.1:1024").rstrip("/")
OPENZERO_API_KEY = os.getenv("OPENZERO_API_KEY", "")
OPENZERO_MODEL = os.getenv("OPENZERO_MODEL", "gemma4:e4b")
AI_PROVIDER = os.getenv("CALLCHAT_AI_PROVIDER", "").strip().lower()
OPENAI_MODEL = os.getenv("CALLCHAT_OPENAI_MODEL", "").strip()
GROQ_MODEL = os.getenv("CALLCHAT_GROQ_MODEL", "").strip()
IONQ_API_KEY = os.getenv("IONQ_API_KEY", "").strip()
IONQ_BACKEND = os.getenv("CALLCHAT_IONQ_BACKEND", "").strip()
IONQ_ALLOW_PAID_QPU = os.getenv("CALLCHAT_IONQ_ALLOW_PAID_QPU", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ALLOWED_ORIGINS = {x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip()}
DAILY_LIMIT = int(os.getenv("ZERO_AGENT_DAILY_LIMIT", "40"))
SITE_CONTEXT = os.getenv(
    "SITE_CONTEXT",
    "CallChat Community helps people self-host Matrix/Synapse/Element with optional OpenZero AI support. Q Call secure-comms licenses are USD 55/month or USD 550/year for unlimited users on one approved public server IP.",
)

WINDOW_SECONDS = 24 * 60 * 60
RATE: dict[str, tuple[int, float]] = {}
SECRET_ASSIGNMENT = re.compile(
    r"\b(?:password|passphrase|api[ _-]?key|access[ _-]?token|private[ _-]?key|secret)\b"
    r"\s*(?::|=|\bis\b)\s*['\"]?\S{6,}",
    re.IGNORECASE,
)
MATRIX_TOKEN = re.compile(r"\bsyt_[A-Za-z0-9_-]{20,}\b")


def allowed_origin(origin: str) -> bool:
    return canonical_allowed_origin(origin) is not None


def canonical_allowed_origin(origin: str) -> str | None:
    if not origin or "\r" in origin or "\n" in origin:
        return None
    for allowed in ALLOWED_ORIGINS:
        if origin == allowed and "\r" not in allowed and "\n" not in allowed:
            return allowed
    return None


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
        return "Shield is an optional premium vault layer for protected workflows. The Q Call secure-comms license is USD 55/month or USD 550/year for unlimited users on one approved public server IP. Start at https://callchat.org/license/."
    if "price" in lower or "pricing" in lower or "license" in lower or "buy" in lower or "cost" in lower or "q call" in lower:
        return "Q Call secure comms is licensed at USD 55/month or USD 550/year for unlimited users on one approved public server IP. The live buy and capture page is https://callchat.org/license/."
    return "CallChat Community is a self-host kit for Matrix/Synapse/Element with CallChat branding, optional OpenZero AI, and a clean private boundary for premium Shield features. If you need secure comms for a team, Q Call is USD 55/month or USD 550/year at https://callchat.org/license/."


def site_messages(message: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are CallChat Zero, a concise site sales and support assistant. "
                "Help users understand CallChat, Matrix/Synapse/Element setup, OpenZero, voice/video, Q Call licensing, and safe Shield boundaries. "
                "When visitors show buying intent, qualify their use case and route them to https://callchat.org/license/. "
                "State that Q Call secure-comms licenses are USD 55/month or USD 550/year for unlimited users on one approved public server IP. "
                "Do not ask for passwords, tokens, private keys, or recovery phrases. "
                f"Site context: {SITE_CONTEXT}"
            ),
        },
        {"role": "user", "content": message[:1200]},
    ]


def configured_provider_state() -> dict[str, Any]:
    state = provider_control.load_provider_state()
    if AI_PROVIDER in provider_control.AI_PROVIDER_IDS:
        state["active_ai_provider"] = AI_PROVIDER
    for provider, model in (("openai", OPENAI_MODEL), ("groq", GROQ_MODEL)):
        if model:
            try:
                state["providers"][provider]["model"] = provider_control.valid_model(model)
            except provider_control.ProviderConfigError:
                pass
    if IONQ_BACKEND in provider_control.IONQ_BACKENDS:
        if IONQ_BACKEND == "simulator" or IONQ_ALLOW_PAID_QPU:
            state["providers"]["ionq"]["backend"] = IONQ_BACKEND
            state["providers"]["ionq"]["allow_paid_qpu"] = IONQ_ALLOW_PAID_QPU
    for provider in ("openai", "groq", "ionq"):
        if provider_control.environment_key(provider):
            state["providers"][provider]["enabled"] = True
    if IONQ_API_KEY and not provider_control.provider_key("ionq", state):
        state["providers"]["ionq"].update({"api_key": IONQ_API_KEY, "enabled": True})
    active = state["active_ai_provider"]
    if active != "local" and not provider_control.provider_key(active, state):
        state["active_ai_provider"] = "local"
    return state


def likely_secretish(message: str) -> bool:
    text = str(message or "")[:8_000]
    lower = text.lower()
    if "-----begin " in lower and "private key-----" in lower:
        return True
    if SECRET_ASSIGNMENT.search(text) or MATRIX_TOKEN.search(text):
        return True
    if "recovery phrase" in lower or "seed phrase" in lower:
        tail = re.split(r"recovery phrase|seed phrase", lower, maxsplit=1)[-1]
        if len(re.findall(r"[a-z]{2,}", tail)) >= 8:
            return True
    return False


def ask_openzero(message: str) -> str | None:
    payload = {
        "model": OPENZERO_MODEL,
        "messages": site_messages(message),
        "temperature": 0.45,
        "max_tokens": 260,
    }
    headers = {"Content-Type": "application/json"}
    if OPENZERO_API_KEY:
        headers["Authorization"] = f"Bearer {OPENZERO_API_KEY}"
    req = urllib.request.Request(
        f"{OPENZERO_BASE_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
        return None


def ask_ai(message: str) -> str | None:
    if likely_secretish(message):
        return ask_openzero(message)
    state = configured_provider_state()
    cloud_reply, _route = provider_control.cloud_chat_completion(
        site_messages(message),
        state=state,
        max_tokens=260,
        temperature=0.45,
    )
    return cloud_reply or ask_openzero(message)


def request_ionq_receipt(commitment: str) -> tuple[dict[str, Any] | None, str | None]:
    """Submit a provider-isolated quantum receipt for a non-secret commitment."""
    return provider_control.ionq_receipt(
        commitment,
        purpose="zshield-receipt",
        name="CallChat ZShield assurance receipt",
        state=configured_provider_state(),
    )


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

        if self.path.rstrip("/") == "/v1/quantum/ionq/receipt":
            receipt, error = request_ionq_receipt(str(body.get("commitment") or ""))
            self.send_json(receipt or {"error": error}, 201 if receipt else 503 if "not configured" in (error or "") else 400)
            return

        message = str(body.get("message", "")).strip()
        if not message:
            self.send_json({"error": "empty message"}, 400)
            return

        reply = ask_ai(message) or fallback_reply(message)
        self.send_json({"reply": reply})

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        origin = self.headers.get("Origin", "")
        response_origin = canonical_allowed_origin(origin)
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if response_origin:
            self.send_header("Access-Control-Allow-Origin", response_origin)
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
