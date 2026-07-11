#!/usr/bin/env python3
"""Encrypted Matrix transport for the CallChat Zero Bot."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
from collections import deque
from concurrent.futures import Future
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Coroutine

from nio import AsyncClient, AsyncClientConfig, MatrixRoom, RoomMessageText

from event_guard import EventLedger
from zero_matrix_bot import CallChatZeroBot, Config, configure_logging, matrix_html


LOG = logging.getLogger("callchat-zero-bot.e2ee")
STORE_DIR = Path(os.getenv("CALLCHAT_BOT_CRYPTO_STORE", "/opt/callchat-zero-bot/store"))
SESSION_FILE = STORE_DIR / "session.json"
EVENT_LEDGER_FILE = STORE_DIR / "event-ledger.sqlite3"


def bounded_env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def load_session() -> dict[str, str]:
    if not SESSION_FILE.is_file():
        return {}
    data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    required = ("user_id", "device_id", "access_token")
    if not all(data.get(key) for key in required):
        raise RuntimeError("The Matrix crypto session file is incomplete")
    return {key: str(data[key]) for key in required}


def save_session(data: dict[str, str]) -> None:
    STORE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(SESSION_FILE, 0o600)


class NioSyncAdapter:
    """Expose the small synchronous transport used by the existing bot logic."""

    def __init__(self, client: AsyncClient, loop: asyncio.AbstractEventLoop) -> None:
        self.client = client
        self.loop = loop
        self.user_id = client.user_id
        self._encrypted_uploads: dict[str, dict[str, Any]] = {}
        self._transaction_id: ContextVar[str | None] = ContextVar("zero_bot_transaction_id", default=None)
        self._reply_event_id: ContextVar[str | None] = ContextVar("zero_bot_reply_event_id", default=None)

    def _wait(self, task: Coroutine[Any, Any, Any], timeout: int = 120) -> Any:
        future: Future[Any] = asyncio.run_coroutine_threadsafe(task, self.loop)
        return future.result(timeout=timeout)

    def resolve_room_alias(self, alias: str) -> str | None:
        response = self._wait(self.client.room_resolve_alias(alias), timeout=30)
        return getattr(response, "room_id", None)

    def begin_event(self, transaction_id: str, reply_event_id: str) -> tuple[Any, Any]:
        return (
            self._transaction_id.set(transaction_id),
            self._reply_event_id.set(reply_event_id),
        )

    def end_event(self, tokens: tuple[Any, Any]) -> None:
        transaction_token, reply_token = tokens
        self._reply_event_id.reset(reply_token)
        self._transaction_id.reset(transaction_token)

    def send_text(self, room_id: str, body: str) -> None:
        self._wait(
            self._send_text(
                room_id,
                body,
                transaction_id=self._transaction_id.get(),
                reply_event_id=self._reply_event_id.get(),
            ),
            timeout=120,
        )

    async def _send_text(
        self,
        room_id: str,
        body: str,
        *,
        transaction_id: str | None = None,
        reply_event_id: str | None = None,
    ) -> None:
        content = {
            "msgtype": "m.text",
            "body": body[:9000],
            "format": "org.matrix.custom.html",
            "formatted_body": matrix_html(body[:9000]),
        }
        if reply_event_id:
            content["m.relates_to"] = {"m.in_reply_to": {"event_id": reply_event_id}}
        response = await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content=content,
            tx_id=transaction_id,
            ignore_unverified_devices=True,
        )
        if not getattr(response, "event_id", None):
            raise RuntimeError("Matrix encrypted text send failed")

    def upload_media(self, filename: str, content_type: str, data: bytes) -> str:
        return self._wait(self._upload_media(filename, content_type, data), timeout=180)

    async def _upload_media(self, filename: str, content_type: str, data: bytes) -> str:
        response, decryption = await self.client.upload(
            io.BytesIO(data),
            content_type=content_type,
            filename=filename,
            encrypt=True,
            filesize=len(data),
        )
        content_uri = getattr(response, "content_uri", "")
        if not content_uri or not decryption:
            raise RuntimeError("Matrix encrypted media upload failed")
        decryption["url"] = content_uri
        self._encrypted_uploads[content_uri] = decryption
        return content_uri

    def send_audio(self, room_id: str, mxc_url: str, filename: str, mimetype: str, size: int) -> None:
        transaction_id = self._transaction_id.get()
        self._wait(
            self._send_audio(
                room_id,
                mxc_url,
                filename,
                mimetype,
                size,
                transaction_id=f"{transaction_id}-audio" if transaction_id else None,
                reply_event_id=self._reply_event_id.get(),
            ),
            timeout=120,
        )

    async def _send_audio(
        self,
        room_id: str,
        mxc_url: str,
        filename: str,
        mimetype: str,
        size: int,
        *,
        transaction_id: str | None = None,
        reply_event_id: str | None = None,
    ) -> None:
        encrypted_file = self._encrypted_uploads.pop(mxc_url, None)
        if not encrypted_file:
            raise RuntimeError("Encrypted media metadata is missing")
        content = {
            "msgtype": "m.audio",
            "body": filename,
            "file": encrypted_file,
            "info": {"mimetype": mimetype, "size": size},
        }
        if reply_event_id:
            content["m.relates_to"] = {"m.in_reply_to": {"event_id": reply_event_id}}
        response = await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content=content,
            tx_id=transaction_id,
            ignore_unverified_devices=True,
        )
        if not getattr(response, "event_id", None):
            raise RuntimeError("Matrix encrypted audio send failed")


def security_fact(room: MatrixRoom, prompt: str) -> str | None:
    normalized = re.sub(r"\s+", " ", prompt.strip().lower())
    phrases = (
        "encrypted by default",
        "is this encrypted",
        "is this room encrypted",
        "is this secure",
        "security status",
        "how secure",
        "zshield status",
        "shield status",
    )
    if not any(phrase in normalized for phrase in phrases):
        return None
    room_state = "on" if room.encrypted else "off"
    return (
        "Verified room security status:\n"
        f"- Matrix end-to-end encryption: {room_state}\n"
        "- Message algorithm when enabled: Megolm AES-SHA2\n"
        "- Calls: Matrix WebRTC with DTLS-SRTP and the configured TURN relay\n"
        "- ZShield: local .zme1 protection for selected files and vault notes\n"
        "- IonQ assurance: server-side receipts outside the live media encryption path\n"
        "Keep passwords, recovery factors, and API keys out of bot prompts."
    )


class EncryptedZeroBot:
    def __init__(self, client: AsyncClient, config: Config) -> None:
        self.client = client
        self.logic = CallChatZeroBot(config)
        self.loop = asyncio.get_running_loop()
        self.logic.matrix = NioSyncAdapter(client, self.loop)
        duplicate_window = bounded_env_int("CALLCHAT_BOT_DUPLICATE_WINDOW_SECONDS", 30, 0, 300)
        retention_days = bounded_env_int("CALLCHAT_BOT_EVENT_RETENTION_DAYS", 14, 1, 90)
        self.ledger = EventLedger(
            EVENT_LEDGER_FILE,
            duplicate_window_seconds=duplicate_window,
            retention_seconds=retention_days * 24 * 60 * 60,
        )
        self.duplicate_window = duplicate_window
        self.timeline_event_ids: set[str] = set()
        self.timeline_event_order: deque[str] = deque()

    async def configure_rooms(self) -> None:
        self.logic.allowed_rooms = await asyncio.to_thread(self.logic.resolve_allowed_rooms)
        if self.logic.config.allow_all_rooms:
            raise RuntimeError("Encrypted Zero Bot refuses CALLCHAT_BOT_ALLOW_ALL_ROOMS=true")
        if not self.logic.allowed_rooms:
            raise RuntimeError("Encrypted Zero Bot requires an explicit approved-room list")
        LOG.info("Approved encrypted rooms: %d", len(self.logic.allowed_rooms))
        LOG.info("One-event/one-reply guard active; prompt window: %ds", self.duplicate_window)

    def mark_timeline_event(self, event_id: str) -> bool:
        if event_id in self.timeline_event_ids:
            return False
        self.timeline_event_ids.add(event_id)
        self.timeline_event_order.append(event_id)
        while len(self.timeline_event_order) > 4096:
            self.timeline_event_ids.discard(self.timeline_event_order.popleft())
        return True

    async def on_message(self, room: MatrixRoom, event: RoomMessageText) -> None:
        if event.sender == self.client.user_id or room.room_id not in self.logic.allowed_rooms:
            return
        if not room.encrypted:
            LOG.warning("Refusing bot input from unencrypted room %s", room.room_id)
            return
        source = event.source if isinstance(event.source, dict) else {}
        content = source.get("content", {}) if isinstance(source.get("content", {}), dict) else {}
        relation = content.get("m.relates_to", {}) if isinstance(content.get("m.relates_to", {}), dict) else {}
        unsigned = source.get("unsigned", {}) if isinstance(source.get("unsigned", {}), dict) else {}
        if relation.get("rel_type") == "m.replace" or unsigned.get("redacted_because"):
            return
        event_id = str(getattr(event, "event_id", "") or "")
        if not event_id:
            LOG.warning("Ignoring Matrix text event without an event ID")
            return
        if not self.mark_timeline_event(event_id):
            return
        body = str(event.body or "").strip()
        if not body:
            return
        command = self.logic.extract_command(body)
        if command is None:
            self.logic.remember(room.room_id, event.sender, body)
            return
        claim = await asyncio.to_thread(
            self.ledger.claim,
            event_id,
            room.room_id,
            event.sender,
            command,
        )
        if not claim.claimed:
            LOG.info("Suppressed duplicate bot input %s (%s)", claim.token, claim.reason)
            return
        self.logic.remember(room.room_id, event.sender, body)
        tokens = self.logic.matrix.begin_event(claim.transaction_id, event_id)
        try:
            rate_message = self.logic.rate_limited(room.room_id, event.sender)
            if rate_message is not None:
                if rate_message:
                    await self.logic.matrix._send_text(
                        room.room_id,
                        rate_message,
                        transaction_id=claim.transaction_id,
                        reply_event_id=event_id,
                    )
                await asyncio.to_thread(self.ledger.complete, event_id)
                return
            answer = security_fact(room, command)
            if answer is None:
                answer = await asyncio.to_thread(
                    self.logic.route_command,
                    room.room_id,
                    event.sender,
                    command,
                )
            if answer:
                await self.logic.matrix._send_text(
                    room.room_id,
                    answer,
                    transaction_id=claim.transaction_id,
                    reply_event_id=event_id,
                )
            await asyncio.to_thread(self.ledger.complete, event_id)
        except Exception as exc:
            await asyncio.to_thread(self.ledger.release, event_id)
            LOG.warning("Bot event %s failed safely: %s", claim.token, exc.__class__.__name__)
            raise
        finally:
            self.logic.matrix.end_event(tokens)


async def build_client(config: Config) -> AsyncClient:
    STORE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STORE_DIR, 0o700)
    session = load_session()
    client_config = AsyncClientConfig(encryption_enabled=True, store_sync_tokens=True)
    if session:
        client = AsyncClient(
            config.homeserver,
            user=session["user_id"],
            device_id=session["device_id"],
            store_path=str(STORE_DIR),
            config=client_config,
        )
        client.restore_login(
            user_id=session["user_id"],
            device_id=session["device_id"],
            access_token=session["access_token"],
        )
        return client

    client = AsyncClient(
        config.homeserver,
        user=config.user_id,
        store_path=str(STORE_DIR),
        config=client_config,
    )
    response = await client.login(password=config.password, device_name="CallChat Zero Bot E2EE")
    if not getattr(response, "access_token", None):
        await client.close()
        raise RuntimeError("Encrypted Matrix login failed")
    save_session(
        {
            "user_id": response.user_id,
            "device_id": response.device_id,
            "access_token": response.access_token,
        }
    )
    return client


async def async_main() -> None:
    configure_logging()
    config = Config.from_env()
    client = await build_client(config)
    bot = EncryptedZeroBot(client, config)
    try:
        first = await client.sync(timeout=30000, full_state=True)
        if not getattr(first, "next_batch", None):
            raise RuntimeError("Initial encrypted Matrix sync failed")
        await bot.configure_rooms()
        client.add_event_callback(bot.on_message, RoomMessageText)
        LOG.info("Encrypted Zero Bot online as %s on device %s", client.user_id, client.device_id)
        await client.sync_forever(timeout=30000, full_state=True)
    finally:
        await client.close()


def main() -> int:
    asyncio.run(async_main())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        LOG.info("Stopping encrypted CallChat Zero Bot")
        raise SystemExit(0)
    except Exception as exc:  # noqa: BLE001
        LOG.exception("Encrypted bot stopped: %s", exc.__class__.__name__)
        raise SystemExit(1)
