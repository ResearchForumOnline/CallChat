#!/usr/bin/env python3
"""CallChat ZERO Matrix bot bridge.

This bot intentionally uses the Matrix Client-Server HTTP API directly so the
MVP has only one Python dependency: requests.
"""

from __future__ import annotations

import json
import logging
import os
import re
import socket
import sys
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests


LOG = logging.getLogger("callchat-zero-bot")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Config:
    homeserver: str
    user_id: str
    username: str
    password: str
    access_token: str
    allowed_rooms_raw: list[str]
    allow_all_rooms: bool
    mention_responses: bool
    ambient_responses: bool
    rate_seconds: int
    user_rate_burst: int
    user_rate_window_seconds: int
    room_rate_burst: int
    room_rate_window_seconds: int
    rate_notice_seconds: int
    rate_exempt_users: list[str]
    buffer_messages: int
    max_prompt_chars: int
    max_response_tokens: int
    context_messages: int
    context_message_chars: int
    openzero_url: str
    openzero_model: str
    openzero_api_key: str
    openzero_timeout: int
    voicebox_url: str
    voicebox_endpoint: str
    voicebox_profile: str
    voicebox_language: str
    voicebox_timeout: int
    persona: str
    site_name: str
    knowledge_file: str

    @classmethod
    def from_env(cls) -> "Config":
        homeserver = os.getenv("MATRIX_HOMESERVER", "https://callchat.org").rstrip("/")
        return cls(
            homeserver=homeserver,
            user_id=os.getenv("MATRIX_USER_ID", "@zero:callchat.org").strip(),
            username=os.getenv("MATRIX_USERNAME", "zero").strip(),
            password=os.getenv("MATRIX_PASSWORD", ""),
            access_token=os.getenv("MATRIX_ACCESS_TOKEN", ""),
            allowed_rooms_raw=csv_env("CALLCHAT_BOT_ALLOWED_ROOMS"),
            allow_all_rooms=env_bool("CALLCHAT_BOT_ALLOW_ALL_ROOMS", False),
            mention_responses=env_bool("CALLCHAT_BOT_MENTION_RESPONSES", True),
            ambient_responses=env_bool("CALLCHAT_BOT_AMBIENT_RESPONSES", False),
            rate_seconds=env_int("CALLCHAT_BOT_RATE_SECONDS", 8),
            user_rate_burst=env_int("CALLCHAT_BOT_USER_RATE_BURST", 5),
            user_rate_window_seconds=env_int("CALLCHAT_BOT_USER_RATE_WINDOW_SECONDS", 60),
            room_rate_burst=env_int("CALLCHAT_BOT_ROOM_RATE_BURST", 40),
            room_rate_window_seconds=env_int("CALLCHAT_BOT_ROOM_RATE_WINDOW_SECONDS", 60),
            rate_notice_seconds=env_int("CALLCHAT_BOT_RATE_NOTICE_SECONDS", 60),
            rate_exempt_users=csv_env("CALLCHAT_BOT_RATE_EXEMPT_USERS"),
            buffer_messages=env_int("CALLCHAT_BOT_BUFFER_MESSAGES", 30),
            max_prompt_chars=env_int("CALLCHAT_BOT_MAX_PROMPT_CHARS", 1800),
            max_response_tokens=env_int("ZERO_BOT_MAX_RESPONSE_TOKENS", 320),
            context_messages=env_int("ZERO_BOT_CONTEXT_MESSAGES", 8),
            context_message_chars=env_int("ZERO_BOT_CONTEXT_MESSAGE_CHARS", 420),
            openzero_url=os.getenv("OPENZERO_LLM_URL", "http://127.0.0.1:1024/v1/chat/completions").strip(),
            openzero_model=os.getenv("OPENZERO_MODEL", "glm4:9b-q5").strip(),
            openzero_api_key=os.getenv("OPENZERO_API_KEY", ""),
            openzero_timeout=env_int("OPENZERO_TIMEOUT_SECONDS", 75),
            voicebox_url=os.getenv("VOICEBOX_URL", "").strip().rstrip("/"),
            voicebox_endpoint=os.getenv("VOICEBOX_ENDPOINT", "/generate").strip(),
            voicebox_profile=os.getenv("VOICEBOX_PROFILE", "callchat-zero").strip(),
            voicebox_language=os.getenv("VOICEBOX_LANGUAGE", "en").strip(),
            voicebox_timeout=env_int("VOICEBOX_TIMEOUT_SECONDS", 45),
            persona=os.getenv("ZERO_BOT_PERSONA", "sharp").strip(),
            site_name=os.getenv("ZERO_BOT_SITE_NAME", "CallChat ZERO").strip(),
            knowledge_file=os.getenv("ZERO_BOT_KNOWLEDGE_FILE", "callchat_knowledge.json").strip(),
        )


class MatrixClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.access_token = config.access_token
        self.user_id = config.user_id
        if self.access_token:
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _url(self, path: str) -> str:
        return f"{self.config.homeserver}{path}"

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        response = self.session.request(method, self._url(path), timeout=kwargs.pop("timeout", 30), **kwargs)
        response.raise_for_status()
        return response

    def login(self) -> None:
        if self.access_token:
            LOG.info("Using Matrix access token for %s", self.user_id)
            return

        if not self.config.password:
            raise RuntimeError("MATRIX_PASSWORD or MATRIX_ACCESS_TOKEN must be set")

        payload = {
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": self.config.username},
            "password": self.config.password,
        }
        response = requests.post(
            self._url("/_matrix/client/v3/login"),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.user_id = data.get("user_id", self.user_id)
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        LOG.info("Logged in to Matrix as %s", self.user_id)

    def sync(self, since: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {"timeout": 30000}
        if since:
            params["since"] = since
        response = self.request("GET", "/_matrix/client/v3/sync", params=params, timeout=45)
        return response.json()

    def send_text(self, room_id: str, body: str) -> None:
        txn = uuid.uuid4().hex
        encoded_room = quote(room_id, safe="")
        payload = {
            "msgtype": "m.text",
            "body": body[:9000],
            "format": "org.matrix.custom.html",
            "formatted_body": matrix_html(body[:9000]),
        }
        self.request(
            "PUT",
            f"/_matrix/client/v3/rooms/{encoded_room}/send/m.room.message/{txn}",
            json=payload,
            timeout=30,
        )

    def upload_media(self, filename: str, content_type: str, data: bytes) -> str:
        response = self.request(
            "POST",
            f"/_matrix/media/v3/upload?filename={quote(filename)}",
            data=data,
            headers={"Content-Type": content_type},
            timeout=90,
        )
        return response.json()["content_uri"]

    def send_audio(self, room_id: str, mxc_url: str, filename: str, mimetype: str, size: int) -> None:
        txn = uuid.uuid4().hex
        encoded_room = quote(room_id, safe="")
        payload = {
            "msgtype": "m.audio",
            "body": filename,
            "url": mxc_url,
            "info": {"mimetype": mimetype, "size": size},
        }
        self.request(
            "PUT",
            f"/_matrix/client/v3/rooms/{encoded_room}/send/m.room.message/{txn}",
            json=payload,
            timeout=30,
        )

    def resolve_room_alias(self, alias: str) -> str | None:
        encoded = quote(alias, safe="")
        try:
            response = self.request("GET", f"/_matrix/client/v3/directory/room/{encoded}", timeout=20)
            return response.json().get("room_id")
        except requests.RequestException as exc:
            LOG.warning("Could not resolve room alias %s: %s", alias, exc.__class__.__name__)
            return None


def matrix_html(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    return escaped


class ZeroBrain:
    def __init__(self, config: Config, knowledge: dict[str, Any]) -> None:
        self.config = config
        self.knowledge = knowledge

    def system_prompt(self) -> str:
        return (
            "You are Zero Bot for CallChat ZERO. Be professional, concise, clear, warm, and confident. "
            "Use precise product language and never use jokes or sarcasm in security, privacy, billing, or service-status answers. Do not harass people, threaten, "
            "doxx, expose secrets, produce malware instructions, or help break into systems. "
            "Return plain conversational text only. Do not output SSML/XML tags, <speak> blocks, tool blocks, JSON tool calls, markdown code fences, or internal planning. "
            "Use public product knowledge only. Never ask for raw Shield secrets, pattern material, "
            "recovery phrases, Matrix signing keys, database passwords, API keys, or private ZMath source. "
            "When relevant, explain that standard Matrix chat is free, hosted callchat.org Shield/ZMath is included for message status, protected files, vault notes, and Q-Call posture, and external or self-hosted Shield use is licensed at $55/month or $550/year for one public server IP, "
            "OpenZero is the preferred local brain, Voicebox is optional local speech, and CallChat Q-Calls combine Matrix/WebRTC media protection, Shield call status, PQC-ready planning, and optional server-side IonQ assurance receipts outside the live media key path. "
            "Answer each user turn once, avoid repeated greetings, and do not restate the same paragraph in one response. "
            f"Public knowledge JSON: {json.dumps(self.knowledge, ensure_ascii=True)[:2400]}"
        )

    def ask(self, prompt: str, room_context: str = "") -> tuple[str, str]:
        if not self.config.openzero_url:
            return self.fallback(prompt, "OpenZero URL is not configured."), "fallback"

        url = self.config.openzero_url
        if not url.endswith("/v1/chat/completions"):
            url = f"{url.rstrip('/')}/v1/chat/completions"

        user_text = prompt
        if room_context:
            user_text = f"Recent visible room context:\n{room_context}\n\nUser request:\n{prompt}"

        payload = {
            "model": self.config.openzero_model or "local",
            "messages": [
                {"role": "system", "content": self.system_prompt()},
                {"role": "user", "content": user_text[: self.config.max_prompt_chars]},
            ],
            "temperature": 0.58,
            "max_tokens": max(80, min(self.config.max_response_tokens, 700)),
            "stream": False,
            "openzero_spark": "auto",
        }
        headers = {"Content-Type": "application/json"}
        if self.config.openzero_api_key:
            headers["Authorization"] = f"Bearer {self.config.openzero_api_key}"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.openzero_timeout,
            )
            response.raise_for_status()
            data = response.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if text:
                return normalize_model_text(text), "openzero"
            return self.fallback(prompt, "OpenZero returned an empty answer."), "fallback"
        except Exception as exc:  # noqa: BLE001 - log category only, not prompt content.
            LOG.warning("OpenZero request failed: %s", exc.__class__.__name__)
            return self.fallback(prompt, "OpenZero is not reachable yet."), "fallback"

    def fallback(self, prompt: str, reason: str) -> str:
        lower = prompt.lower()
        if "shield" in lower or "zmath" in lower:
            return (
                "Shield is included for active hosted callchat.org accounts and licensed for external or self-hosted servers at $55/month or $550/year for one public server IP. "
                "Normal Matrix chat stays free. Shield adds CallChat message status, protects selected files as .zme1 containers, "
                "and adds Q-Call security posture around Matrix/WebRTC calls. Never paste raw Shield secrets, "
                "pattern material, or recovery material into chat."
            )
        if any(term in lower for term in ("voice", "voicebox", "tts", "audio reply", "say out loud", "spoken reply")):
            if self.config.voicebox_url:
                return (
                    "Voice is configured for command-triggered room audio. Use `!zero voice your prompt` and I will "
                    "generate a Zero Bot answer, then post it through the CallChat room."
                )
            return (
                "Browser voice is live on the public site. Matrix room audio is wired for Voicebox, but this bot "
                "still needs `VOICEBOX_URL` configured before `!zero voice your text` can post audio in the room."
            )
        if "quantum" in lower or "ionq" in lower or "q-call" in lower or "secure call" in lower:
            return (
                "Q-Calls keep the real call engine on Matrix/Element WebRTC, identity checks, DTLS-SRTP, and the configured TURN relay. "
                "The CallChat layer adds Shield call status, identity posture, PQC-ready guidance, call status evidence, and an optional server-side IonQ research hook. "
                "That is a serious secure-call posture with clear public boundaries: useful now, research-ready next."
            )
        if "openzero" in lower:
            return (
                "OpenZero is the preferred CPU-first local brain for the bot. The bridge is already wired "
                "for the OpenAI-compatible `/v1/chat/completions` route; once that local endpoint is online, "
                "approved room prompts move from product-guide mode to model-backed answers."
            )
        return (
            "I am Zero Bot for CallChat ZERO: the approved-room guide for the web client, Element setup, "
            "Shield/ZMath, OpenZero, Voicebox, and the TalkToAI ecosystem. Ask me what CallChat does, how to "
            "log in from Element, how Shield protects messages/files/calls, or how the local AI lane connects."
        )


class VoiceboxClient:
    def __init__(self, config: Config) -> None:
        self.config = config

    def enabled(self) -> bool:
        return bool(self.config.voicebox_url)

    def synthesize(self, text: str, profile: str | None = None) -> tuple[bytes | None, str, str]:
        if not self.enabled():
            return None, "", "Voicebox is not configured."

        endpoint = self.config.voicebox_endpoint
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{self.config.voicebox_url}{endpoint}"
        payload = {
            "text": text[:900],
            "profile_id": profile or self.config.voicebox_profile,
            "profile": profile or self.config.voicebox_profile,
            "voice": profile or self.config.voicebox_profile,
            "language": self.config.voicebox_language,
        }
        try:
            response = requests.post(url, json=payload, timeout=self.config.voicebox_timeout)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Voicebox request failed: %s", exc.__class__.__name__)
            return None, "", "Voicebox did not answer."

        content_type = response.headers.get("Content-Type", "application/octet-stream").split(";")[0]
        body = response.content
        if content_type.startswith("audio/") or body[:4] in {b"RIFF", b"OggS"}:
            safe_profile = re.sub(r"[^a-z0-9_-]+", "-", (profile or self.config.voicebox_profile).lower()).strip("-")
            filename = f"zero-bot-{safe_profile or 'voice'}.wav"
            if "mpeg" in content_type:
                filename = f"zero-bot-{safe_profile or 'voice'}.mp3"
            elif "ogg" in content_type:
                filename = f"zero-bot-{safe_profile or 'voice'}.ogg"
            return body, content_type or "audio/wav", filename

        try:
            data = response.json()
        except ValueError:
            return None, "", "Voicebox returned a non-audio response."

        for key in ("audio_url", "url", "file", "path"):
            value = data.get(key)
            if value:
                return None, "", f"Voicebox generated audio: {value}"
        return None, "", "Voicebox answered, but no audio file was returned."


class CallChatZeroBot:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.matrix = MatrixClient(config)
        self.knowledge = load_knowledge(config.knowledge_file)
        self.brain = ZeroBrain(config, self.knowledge)
        self.voicebox = VoiceboxClient(config)
        self.allowed_rooms: set[str] = set()
        self.room_buffers: dict[str, deque[tuple[str, str]]] = defaultdict(lambda: deque(maxlen=config.buffer_messages))
        self.user_rate_windows: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self.room_rate_windows: dict[str, deque[float]] = defaultdict(deque)
        self.rate_notice_at: dict[tuple[str, str, str], float] = {}
        self.first_sync = True

    def start(self) -> None:
        self.matrix.login()
        self.allowed_rooms = self.resolve_allowed_rooms()
        if self.config.allow_all_rooms:
            LOG.warning("CALLCHAT_BOT_ALLOW_ALL_ROOMS=true. Bot may respond in every joined room.")
        elif not self.allowed_rooms:
            LOG.warning("No allowed rooms configured. Bot will stay quiet until CALLCHAT_BOT_ALLOWED_ROOMS is set.")
        since = None
        while True:
            try:
                data = self.matrix.sync(since)
                since = data.get("next_batch", since)
                self.handle_sync(data)
                self.first_sync = False
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # noqa: BLE001
                LOG.warning("Sync loop error: %s", exc.__class__.__name__)
                time.sleep(8)

    def resolve_allowed_rooms(self) -> set[str]:
        rooms: set[str] = set()
        for raw in self.config.allowed_rooms_raw:
            if raw.startswith("#"):
                room_id = self.matrix.resolve_room_alias(raw)
                if room_id:
                    rooms.add(room_id)
            else:
                rooms.add(raw)
        return rooms

    def room_is_allowed(self, room_id: str) -> bool:
        return self.config.allow_all_rooms or room_id in self.allowed_rooms

    def handle_sync(self, data: dict[str, Any]) -> None:
        joined_rooms = data.get("rooms", {}).get("join", {})
        for room_id, room_data in joined_rooms.items():
            events = room_data.get("timeline", {}).get("events", [])
            for event in events:
                if event.get("type") != "m.room.message":
                    continue
                self.handle_message(room_id, event)

    def handle_message(self, room_id: str, event: dict[str, Any]) -> None:
        content = event.get("content", {})
        sender = event.get("sender", "")
        if sender == self.matrix.user_id:
            return
        if content.get("msgtype") not in {"m.text", "m.notice"}:
            return
        body = str(content.get("body", "")).strip()
        if not body:
            return
        if self.room_is_allowed(room_id):
            self.remember(room_id, sender, body)
        if self.first_sync:
            return
        if not self.room_is_allowed(room_id):
            return
        command_text = self.extract_command(body)
        if command_text is None:
            return
        rate_message = self.rate_limited(room_id, sender)
        if rate_message is not None:
            if rate_message:
                self.matrix.send_text(room_id, rate_message)
            return
        response = self.route_command(room_id, sender, command_text)
        if response:
            self.matrix.send_text(room_id, response)

    def remember(self, room_id: str, sender: str, body: str) -> None:
        safe_body = re.sub(r"\s+", " ", body)[: max(120, self.config.context_message_chars)]
        self.room_buffers[room_id].append((sender, safe_body))

    def extract_command(self, body: str) -> str | None:
        return extract_command_text(
            body,
            mention_responses=self.config.mention_responses,
            ambient_responses=self.config.ambient_responses,
        )

    def rate_limited(self, room_id: str, sender: str) -> str | None:
        if sender in self.config.rate_exempt_users or "*" in self.config.rate_exempt_users:
            return None

        now = time.time()
        user_key = (room_id, sender)
        user_window = self.user_rate_windows[user_key]
        room_window = self.room_rate_windows[room_id]
        self.prune_window(user_window, now, self.config.user_rate_window_seconds)
        self.prune_window(room_window, now, self.config.room_rate_window_seconds)

        user_burst = max(5, self.config.user_rate_burst)
        room_burst = max(10, self.config.room_rate_burst)
        if len(user_window) >= user_burst:
            return self.rate_notice(
                room_id,
                sender,
                "user",
                f"Zero Bot throttle: you have had {user_burst} replies in {self.config.user_rate_window_seconds}s. "
                "Please pause briefly before requesting another reply.",
            )
        if len(room_window) >= room_burst:
            return self.rate_notice(
                room_id,
                sender,
                "room",
                f"Zero Bot room throttle: this room has had {room_burst} bot replies in {self.config.room_rate_window_seconds}s. "
                "Give the channel a short breather.",
            )

        user_window.append(now)
        room_window.append(now)
        return None

    def prune_window(self, window: deque[float], now: float, seconds: int) -> None:
        cutoff = now - max(1, seconds)
        while window and window[0] < cutoff:
            window.popleft()

    def rate_notice(self, room_id: str, sender: str, scope: str, message: str) -> str:
        now = time.time()
        key = (room_id, sender, scope)
        last = self.rate_notice_at.get(key, 0)
        if now - last < max(1, self.config.rate_notice_seconds):
            return ""
        self.rate_notice_at[key] = now
        return message

    def route_command(self, room_id: str, sender: str, command_text: str) -> str:
        normalized = command_text.strip()
        lower = normalized.lower()
        if lower in {"test", "ping", "bot test", "zero test"}:
            return "Zero Bot check passed: one Matrix input accepted and one reply returned."
        if lower in {"hi", "hello", "hey", "yo", "sup", "hello zero", "hi zero", "hey zero"}:
            return "Hey. Zero Bot is online. Ask naturally about CallChat, setup, security, calls, or anything else."
        if lower in {"help", "commands"}:
            return help_text()
        if lower in {"about", "who are you", "what are you"}:
            return about_text()
        if lower in {"sites", "links"}:
            return sites_text()
        if lower in {"callchat", "what is callchat"}:
            return callchat_text()
        if lower in {"openzero", "brain"}:
            return openzero_text()
        if lower in {"frontdesk", "frontdeskagent"}:
            return frontdesk_text()
        if lower in {"voice", "voicebox"}:
            return voice_text(self.voicebox.enabled())
        if lower in {"q-call", "q-calls", "quantum", "quantum-calls", "ionq", "secure-calls", "calls"}:
            return qcall_text()
        if lower in {"rules", "safety", "privacy"}:
            return rules_text()
        if lower in {"status", "server-status", "openzero status"}:
            return self.status_text()
        if lower in {"explain-shield", "shield", "zmath"}:
            text, backend = self.brain.ask("Explain CallChat Shield and ZMath to a normal user.")
            return labelled(text, backend)
        if lower in {"summary", "decisions", "tasks"}:
            context = self.visible_context(room_id)
            if not context:
                return "AI-generated fallback: I do not have enough visible room context yet. Talk a bit, then ask again."
            text, backend = self.brain.ask(f"Create {lower} from the visible room context.", context)
            return labelled(text, backend)
        if lower in {"forget", "forget-room"}:
            self.room_buffers[room_id].clear()
            return "Room-local bot buffer cleared. Matrix history was not changed."
        if lower.startswith("voice ") or lower.startswith("say "):
            voice_text = normalized.split(" ", 1)[1].strip()
            return self.handle_voice(room_id, voice_text)
        if likely_secret(normalized):
            return (
                "I will not process that because it looks like a secret, key, password, token, or recovery phrase. "
                "Keep it out of chat and rotate it if it was real."
            )

        context = self.visible_context(room_id)
        text, backend = self.brain.ask(normalized, context)
        return labelled(text, backend)

    def visible_context(self, room_id: str) -> str:
        items = list(self.room_buffers[room_id])[-max(2, self.config.context_messages):]
        return "\n".join(f"{sender}: {body}" for sender, body in items)

    def status_text(self) -> str:
        openzero_status = endpoint_status(self.config.openzero_url)
        voicebox_status = endpoint_status(self.config.voicebox_url) if self.voicebox.enabled() else "not configured"
        parts = [
            "Zero Bot status:",
            f"- Matrix homeserver: {self.config.homeserver}",
            f"- Bot user: {self.matrix.user_id}",
            f"- Approved room count: {'all joined rooms' if self.config.allow_all_rooms else len(self.allowed_rooms)}",
            f"- OpenZero endpoint: {openzero_status}",
            f"- OpenZero model: {self.config.openzero_model or 'local'}",
            f"- OpenZero fast budget: {self.config.max_response_tokens} tokens; "
            f"{self.config.context_messages} context messages; {self.config.max_prompt_chars} prompt chars",
            f"- Voicebox: {self.voicebox_status_detail(voicebox_status)}",
            f"- Live room replies: {'on' if self.config.ambient_responses else 'commands/mentions only'}",
            f"- Rate limit: {self.config.user_rate_burst} replies/user/{self.config.user_rate_window_seconds}s; "
            f"{self.config.room_rate_burst} replies/room/{self.config.room_rate_window_seconds}s",
            "- Memory: in-RAM visible room buffer only",
        ]
        if "not reachable" in openzero_status:
            parts.append("")
            parts.append("OpenZero is not reachable from this bot yet, so model-backed replies use the local product fallback.")
        return "\n".join(parts)

    def voicebox_status_detail(self, base_status: str) -> str:
        if not self.voicebox.enabled() or "reachable" not in base_status:
            return base_status
        try:
            response = requests.get(f"{self.config.voicebox_url}/health", timeout=2.5)
            response.raise_for_status()
            data = response.json()
        except Exception:  # noqa: BLE001
            return base_status
        engine = str(data.get("engine") or "unknown")
        profiles = data.get("profiles")
        if isinstance(profiles, list) and profiles:
            visible = ", ".join(str(item) for item in profiles[:8])
            return f"{base_status} ({engine}; profiles: {visible})"
        return f"{base_status} ({engine})"

    def handle_voice(self, room_id: str, voice_text: str) -> str:
        if likely_secret(voice_text):
            return "I will not send likely secrets to a voice service."

        profile, prompt_text = parse_voice_request(voice_text)
        if not prompt_text:
            return voice_text_help(self.voicebox.enabled())
        if likely_secret(prompt_text):
            return "I will not send likely secrets to a voice service."

        direct_script = direct_voice_script(prompt_text)
        if direct_script:
            spoken_text, backend = direct_script, "local-voice-script"
        else:
            context = self.visible_context(room_id)
            ask_text = voice_script_prompt(profile, prompt_text)
            spoken_text, backend = self.brain.ask(ask_text, context)
            spoken_text = clean_spoken_text(spoken_text)
            if weak_voice_script(spoken_text):
                spoken_text = voice_script_fallback(prompt_text)
        audio, content_type, message = self.voicebox.synthesize(spoken_text, profile)
        if audio:
            try:
                mxc = self.matrix.upload_media(message, content_type, audio)
                self.matrix.send_audio(room_id, mxc, message, content_type, len(audio))
                return (
                    f"Voicebox audio posted with `{profile}` via {backend}. Spoken text:\n"
                    f"{spoken_text}"
                )
            except Exception as exc:  # noqa: BLE001
                LOG.warning("Matrix audio upload failed: %s", exc.__class__.__name__)
                return "Voicebox generated audio, but Matrix upload failed."
        return message


def likely_secret(text: str) -> bool:
    patterns = [
        r"sk-[A-Za-z0-9_-]{16,}",
        r"ztapi_[A-Za-z0-9_-]{16,}",
        r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
        r"password\s*[:=]\s*\S{8,}",
        r"access[_-]?token\s*[:=]\s*\S{12,}",
        r"api[_-]?key\s*[:=]\s*\S{12,}",
        r"recovery phrase",
        r"seed phrase",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def extract_command_text(body: str, *, mention_responses: bool, ambient_responses: bool) -> str | None:
    text = str(body or "").strip()
    if not text:
        return None
    explicit = re.search(r"(?:^|\n)\s*!zero(?:\s+([^\r\n]*))?", text, re.IGNORECASE)
    if explicit:
        return (explicit.group(1) or "help").strip() or "help"
    lower = text.lower()
    if mention_responses and ("@zero" in lower or "zero bot" in lower):
        return text
    if ambient_responses and ambient_trigger(text):
        return text
    return None


def ambient_trigger(text: str) -> bool:
    body = re.sub(r"\s+", " ", text.strip())
    if not body or len(body) > 700:
        return False
    lower = body.lower()
    greetings = {
        "hi", "hello", "hey", "yo", "sup", "zero", "zero?", "hello zero", "hi zero",
        "test", "ping", "bot test", "zero test",
    }
    if lower in greetings:
        return True
    if "?" in body:
        return True
    starts = ("hi ", "hello ", "hey ", "yo ", "zero ", "bot ")
    if lower.startswith(starts):
        return True
    keywords = (
        "callchat",
        "shield",
        "zmath",
        "openzero",
        "zerothink",
        "frontdesk",
        "voicebox",
        "voice",
        "matrix",
        "element",
        "agent",
        "what can you do",
    )
    return any(word in lower for word in keywords)


VOICE_PROFILES = {
    "zero": "callchat-zero",
    "rebel": "zero-rebel",
    "cyber": "zero-cyber",
    "calm": "zero-calm",
    "deep": "zero-deep",
    "whisper": "zero-whisper",
    "callchat-zero": "callchat-zero",
    "zero-rebel": "zero-rebel",
    "zero-cyber": "zero-cyber",
    "zero-calm": "zero-calm",
    "zero-deep": "zero-deep",
    "zero-whisper": "zero-whisper",
    "studio": "zero-studio",
    "hype": "zero-hype",
    "zero-studio": "zero-studio",
    "zero-hype": "zero-hype",
}


def parse_voice_request(text: str) -> tuple[str, str]:
    parts = text.strip().split(None, 1)
    if not parts:
        return "callchat-zero", ""
    first = parts[0].lower().strip(":")
    if first in VOICE_PROFILES:
        return VOICE_PROFILES[first], parts[1].strip() if len(parts) > 1 else ""
    return "callchat-zero", text.strip()


def voice_script_prompt(profile: str, prompt_text: str) -> str:
    profile_notes = {
        "callchat-zero": "clear, warm, confident, and professional",
        "zero-rebel": "direct, bold, and concise",
        "zero-cyber": "fast, crisp, futuristic",
        "zero-calm": "calm, clean, helpful",
        "zero-deep": "slower, cinematic, authoritative",
        "zero-whisper": "quiet, private, minimal",
        "zero-studio": "polished, confident, explainer-style",
        "zero-hype": "high-energy, launch-ready, and controlled",
    }
    style = profile_notes.get(profile, profile_notes["callchat-zero"])
    return (
        "VOICE SCRIPT MODE. Return only the exact words to be spoken aloud. "
        "No SSML, XML, HTML, <speak> tags, markdown, bullets, headings, URLs, or stage directions. "
        "Use 2 to 4 short sentences, 28 to 75 words total. "
        f"Voice style: {style}. "
        "Sound like a polished live room agent. "
        "Do not say 'friendly AI guide', 'I've got your back', 'secure messaging platform', or 'feel free to ask me anything'. "
        "Do not repeat the user's wording. "
        "Mention CallChat, Matrix, Shield, OpenZero, or voice only when relevant. "
        "User asked: "
        f"{prompt_text}"
    )


def normalize_model_text(text: str) -> str:
    cleaned = text.strip()
    if "```tool" in cleaned or '"action"' in cleaned:
        match = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.DOTALL)
        if match:
            try:
                cleaned = json.loads(f'"{match.group(1)}"')
            except json.JSONDecodeError:
                cleaned = match.group(1)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"<\s*break\b[^>]*>", ". ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?\s*(speak|s|p|voice|prosody|emphasis|mstts:[^>\s]+)\b[^>]*>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"^Here(?:'| i)?s (?:my|the) [^:\n]{0,80}:\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^Spoken text:\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"```(?:tool|json|text)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    cleaned = cleaned.replace("Matrix-compatible", "Matrix compatible")
    replacements = {
        "CallChat ZERO": "CallChat Zero",
        "OpenZero": "Open Zero",
        "ZeroThink": "Zero Think",
        "ZMath": "Z Math",
        "Voicebox": "Voice Box",
        "PQC": "P Q C",
        "IonQ": "Ion Q",
        "WebRTC": "Web R T C",
        "DTLS-SRTP": "D T L S S R T P",
        ".zme1": "Z M E one",
    }
    for before, after in replacements.items():
        cleaned = cleaned.replace(before, after)
    cleaned = re.sub(r"\bI'm Zero Bot, your friendly AI guide for CallChat Zero\.?", "I'm Zero Bot, the CallChat Zero room agent.", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\byour friendly AI guide\b", "the room agent", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bI've got your back\.?", "I can help.", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bsecure messaging platform\b", "secure messenger", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bFeel free to ask me anything!?\.?", "Ask me something useful and I will keep it sharp.", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def trim_spoken_text(text: str, max_words: int = 82) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    clipped = " ".join(words[:max_words]).rstrip(" ,;:")
    return clipped if clipped.endswith((".", "!", "?")) else clipped + "."


def clean_spoken_text(text: str) -> str:
    cleaned = re.sub(r"^Zero Bot (via OpenZero|Lab):\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = normalize_model_text(cleaned)
    return trim_spoken_text(cleaned) or "Zero Bot is online and ready."


def weak_voice_script(text: str) -> bool:
    lower = text.lower()
    weak_terms = (
        "<speak",
        "</speak",
        "friendly ai guide",
        "i've got your back",
        "feel free to ask me anything",
        "secure messaging platform",
        "make sure you get the most out of",
        "hello there! i'm zero bot",
    )
    return not text or any(term in lower for term in weak_terms)


def voice_script_fallback(prompt_text: str) -> str:
    lower = prompt_text.lower()
    if any(term in lower for term in ("yourself", "who are you", "hello", "hi", "speak freely")):
        return (
            "Hello. I am Zero Bot, the CallChat Zero room agent. "
            "I help with Matrix login, calls, Shielded messages, protected files, and the Open Zero brain lane. "
            "Ask me a real question and I will keep it sharp."
        )
    if "shield" in lower or "zmath" in lower:
        return (
            "Shield is the CallChat protection layer for message status, protected files, vault notes, and Q-Calls. "
            "On callchat.org it is included for hosted accounts; outside servers need the self-hosted Shield license at $55/month or $550/year for one public server IP. "
            "Standard Matrix chat remains free."
        )
    if any(term in lower for term in ("voice", "speak", "audio", "voicebox")):
        return (
            "Voice is live through a natural neural route first, with local Piper as the fallback. "
            "I write a short script first, then Voice Box turns it into audio. "
            "The voice path remains owner-controlled and can operate without a paid external voice dependency."
        )
    return (
        "CallChat Zero gives you Matrix chat, Element compatibility, Shielded messages, protected files, Q-Calls, and a live Zero Bot lane. "
        "Ask what you want to test or configure next."
    )


def direct_voice_script(prompt_text: str) -> str | None:
    lower = prompt_text.lower()
    greeting = re.search(r"(^|[\s,!.?])(hello|hi|hey|yo)([\s,!.?]|$)", lower)
    if any(term in lower for term in ("yourself", "who are you", "what are you", "speak freely")) or greeting:
        return (
            "Hello. I am Zero Bot, the CallChat Zero room agent. "
            "I help with Matrix login, calls, Shielded messages, protected files, and the Open Zero brain lane. "
            "Ask me a real question and I will keep it sharp."
        )
    if "shield" in lower or "zmath" in lower or "z math" in lower or "zme1" in lower:
        return (
            "Shield is CallChat's message, file, vault, and Q-Call posture layer. "
            "Hosted CallChat accounts get it included; outside servers need the self-hosted Shield license at $55/month or $550/year for one public server IP. "
            "Standard Matrix chat remains free."
        )
    if any(term in lower for term in ("element", "login", "homeserver", "sign in", "matrix")):
        return (
            "Use callchat.org as the homeserver. "
            "The live web client is on CallChat, and Element apps can connect by choosing a custom homeserver. "
            "Controlled access keeps the spam flood outside where it belongs."
        )
    if any(term in lower for term in ("voice", "speak", "audio", "voicebox", "piper")):
        return (
            "Voice now prefers a natural neural route, with local Piper ready as the fallback. "
            "I write a short script first, then Voice Box turns it into audio. "
            "That gives the room a better voice without tying it to ElevenLabs."
        )
    if any(term in lower for term in ("q-call", "q call", "quantum", "ionq", "secure call", "video call", "voice call")):
        return (
            "Calls stay on the real Matrix and Web R T C stack, with TURN and identity checks. "
            "Q-Calls add CallChat Shield call status, PQC-ready planning, and optional IonQ assurance receipts outside the live media key path."
        )
    return None


def voice_text_help(enabled: bool) -> str:
    if not enabled:
        return voice_text(False)
    return (
        "Voice commands now generate a Zero Bot answer first, then speak it. Try:\n"
        "- `!zero voice tell me about yourself`\n"
        "- `!zero voice rebel give a bold product summary`\n"
        "- `!zero voice cyber explain CallChat`\n"
        "- `!zero voice calm help me set up Element`\n"
        "- `!zero voice deep what are Q-Calls`\n"
        "- `!zero voice whisper explain Shield`\n"
        "- `!zero voice studio give a polished product intro`\n"
        "- `!zero voice hype deliver a launch summary`"
    )


def endpoint_status(url_text: str) -> str:
    if not url_text:
        return "not configured"
    try:
        parsed = urlparse(url_text)
        host = parsed.hostname
        if not host:
            return "configured, but URL is invalid"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=1.5):
            return f"reachable at {host}:{port}"
    except OSError:
        return "configured, but not reachable yet"


def labelled(text: str, backend: str) -> str:
    label = "Zero Bot via OpenZero" if backend == "openzero" else "Zero Bot Lab"
    return f"{label}:\n{text.strip()}"


def help_text() -> str:
    return (
        "Zero Bot commands:\n"
        "- `!zero about` - what I am\n"
        "- `!zero sites` - useful TalkToAI links\n"
        "- `!zero callchat` - CallChat in plain English\n"
        "- `!zero openzero` - how the local brain connects\n"
        "- `!zero frontdesk` - FrontDeskAgent link\n"
        "- `!zero voice` - how Voicebox speech works\n"
        "- `!zero q-call` - Q-Calls, IonQ assurance receipts, and live call security\n"
        "- `!zero status` - bot/OpenZero/Voicebox status\n"
        "- `!zero explain-shield` - Shield and ZMath in plain English\n"
        "- `!zero rules` - privacy and room boundaries\n"
        "- `!zero summary` - summarize recent visible room messages\n"
        "- `!zero decisions` - extract decisions from visible context\n"
        "- `!zero tasks` - extract tasks from visible context\n"
        "- `!zero voice <text>` - generate and speak a Zero Bot answer\n"
        "- `!zero voice rebel|cyber|calm|deep|whisper|studio|hype <text>` - choose a voice profile\n"
        "- `!zero forget` - clear my in-RAM room buffer\n\n"
        "Rate limit: five quick replies per user by default, then a short cooldown. "
        "In the live lab room I can also answer normal greetings and product questions."
    )


def about_text() -> str:
    return (
        "I am Zero Bot for CallChat ZERO: a Matrix room agent designed to use OpenZero as the local brain and "
        "Voicebox as the optional local voice. I can help with CallChat, Element setup, Shield/ZMath, site questions, "
        "Q-Calls, and room summaries. I do not need your passwords, keys, recovery phrases, or private Shield materials. "
        "If OpenZero is reachable, I use the local brain; otherwise I answer from the approved public product map."
    )


def callchat_text() -> str:
    return (
        "CallChat ZERO is the Matrix-compatible messenger layer for the TalkToAI ecosystem. "
        "Use `callchat.org` as the homeserver, use the live web client at `/element/`, and use this bot room "
        "for AI-assisted testing. Standard Matrix chat stays free; hosted callchat.org Shield/ZMath is included, "
        "while external and self-hosted Shield use requires the paid ZMath Shield licence: $55/month or $550/year for one public server IP."
    )


def openzero_text() -> str:
    return (
        "OpenZero is the preferred local brain for me. When OpenZero is running on this server or a private network, "
        "I can send approved room prompts to its OpenAI-compatible `/v1/chat/completions` API. Until then I use local "
        "fallback replies from the approved public product map."
    )


def frontdesk_text() -> str:
    return (
        "FrontDeskAgent can share the same OpenZero and Voicebox stack for business intake, leads, calls, and staff alerts. "
        "The neat architecture is: FrontDeskAgent for reception workflows, CallChat for secure Matrix rooms, OpenZero for "
        "local AI, and Voicebox for local speech."
    )


def voice_text(enabled: bool) -> str:
    if enabled:
        return (
            "Voice is configured for this bot. Use `!zero voice <text>` and I will generate a Zero Bot answer, "
            "then post it as audio. The live route prefers a natural neural voice and falls back to local Piper. "
            "Profiles: `rebel`, `cyber`, `calm`, `deep`, `whisper`, `studio`, and `hype`. "
            "Automatic public-room speech stays off so room members retain explicit control over audio output."
        )
    return (
        "Voicebox is not configured on this bot yet. Once a local Voicebox service is running, set `VOICEBOX_URL` in the "
        "private bot env and restart the service. Then `!zero voice <text>` can post audio."
    )


def qcall_text() -> str:
    return (
        "CallChat Q-Calls are the secure-call option: normal calls still use Matrix/Element WebRTC with DTLS-SRTP, "
        "device identity, and the configured TURN relay. Q-Call mode adds the CallChat policy layer: Shield status, "
        "PQC-ready planning, call setup evidence, and optional server-side IonQ assurance receipts. "
        "IonQ credentials stay server-side, and assurance processing remains separate from the live media encryption path."
    )


def rules_text() -> str:
    return (
        "Room rules: I answer in approved rooms only, keep only a small in-RAM visible-message buffer, and do not need "
        "passwords, API keys, Matrix recovery phrases, Shield pattern images, signing keys, or private ZMath source. "
        "A short reply allowance is followed by rate limiting to keep approved rooms usable."
    )


def sites_text() -> str:
    return (
        "Useful links:\n"
        "- CallChat: https://callchat.org/\n"
        "- CallChat Web: https://callchat.org/element/#/login\n"
        "- CallChat guide: https://callchat.org/guide/\n"
        "- TalkToAI: https://talktoai.org/\n"
        "- OpenZero: https://openzero.talktoai.org/\n"
        "- ZeroThink: https://zerothink.talktoai.org/\n"
        "- FrontDeskAgent: https://frontdeskagent.online/"
    )


def load_knowledge(path_text: str) -> dict[str, Any]:
    configured = Path(path_text)
    candidates = [configured]
    if not configured.is_absolute() and configured.name == path_text:
        candidates.append(Path(__file__).with_name(path_text))
    for path in candidates:
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                LOG.warning("Could not load knowledge file %s: %s", path, exc.__class__.__name__)
    return {}


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("ZERO_BOT_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> int:
    configure_logging()
    config = Config.from_env()
    bot = CallChatZeroBot(config)
    bot.start()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        LOG.info("Stopping CallChat Zero Bot")
        raise SystemExit(0)
    except Exception as exc:  # noqa: BLE001
        LOG.error("Fatal startup/runtime error: %s", exc.__class__.__name__)
        raise SystemExit(1)
