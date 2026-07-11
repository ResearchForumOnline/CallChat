#!/usr/bin/env python3
"""Durable one-event/one-reply coordination for Zero Bot."""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _prompt_digest(value: str) -> str:
    normalized = re.sub(r"(?im)^\s*!zero(?:\s+|$)", "", value)
    normalized = re.sub(r"[^\w@#:/.-]+", " ", normalized.casefold())
    return _digest(re.sub(r"\s+", " ", normalized).strip())


def matrix_transaction_id(event_id: str, suffix: str = "") -> str:
    """Return a stable Matrix transaction ID without exposing the event ID."""
    base = f"zbot-{_digest(event_id)[:32]}"
    clean_suffix = re.sub(r"[^a-z0-9-]", "", suffix.casefold())[:12]
    return f"{base}-{clean_suffix}" if clean_suffix else base


@dataclass(frozen=True)
class EventClaim:
    claimed: bool
    reason: str
    token: str
    transaction_id: str


class EventLedger:
    """Atomically claim Matrix events and suppress immediate prompt duplicates.

    Only SHA-256 digests are persisted. Message bodies, room IDs, user IDs and
    Matrix event IDs are never written to the ledger.
    """

    def __init__(
        self,
        path: Path,
        *,
        duplicate_window_seconds: int = 30,
        stale_processing_seconds: int = 300,
        retention_seconds: int = 14 * 24 * 60 * 60,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.path = path
        self.duplicate_window_seconds = max(0, duplicate_window_seconds)
        self.stale_processing_seconds = max(30, stale_processing_seconds)
        self.retention_seconds = max(3600, retention_seconds)
        self.clock = clock
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS event_claims (
                    event_key TEXT PRIMARY KEY,
                    room_key TEXT NOT NULL,
                    sender_key TEXT NOT NULL,
                    prompt_key TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('processing', 'sent')),
                    claimed_at INTEGER NOT NULL,
                    completed_at INTEGER
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS event_claims_prompt_recent
                ON event_claims (room_key, sender_key, prompt_key, claimed_at)
                """
            )
            connection.commit()
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def claim(self, event_id: str, room_id: str, sender: str, prompt: str) -> EventClaim:
        if not all(isinstance(item, str) and item for item in (event_id, room_id, sender, prompt)):
            return EventClaim(False, "invalid", "", "")

        now = int(self.clock())
        event_key = _digest(event_id)
        room_key = _digest(room_id)
        sender_key = _digest(sender)
        prompt_key = _prompt_digest(prompt)
        transaction_id = matrix_transaction_id(event_id)

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM event_claims WHERE claimed_at < ?",
                (now - self.retention_seconds,),
            )
            existing = connection.execute(
                "SELECT state, claimed_at FROM event_claims WHERE event_key = ?",
                (event_key,),
            ).fetchone()
            if existing:
                state, claimed_at = existing
                if state != "processing" or claimed_at >= now - self.stale_processing_seconds:
                    connection.rollback()
                    return EventClaim(False, "event", event_key[:12], transaction_id)
                connection.execute("DELETE FROM event_claims WHERE event_key = ?", (event_key,))

            if self.duplicate_window_seconds:
                repeated_prompt = connection.execute(
                    """
                    SELECT 1 FROM event_claims
                    WHERE room_key = ? AND sender_key = ? AND prompt_key = ? AND claimed_at >= ?
                    LIMIT 1
                    """,
                    (room_key, sender_key, prompt_key, now - self.duplicate_window_seconds),
                ).fetchone()
                if repeated_prompt:
                    connection.rollback()
                    return EventClaim(False, "prompt", event_key[:12], transaction_id)

            connection.execute(
                """
                INSERT INTO event_claims
                    (event_key, room_key, sender_key, prompt_key, state, claimed_at)
                VALUES (?, ?, ?, ?, 'processing', ?)
                """,
                (event_key, room_key, sender_key, prompt_key, now),
            )
            connection.commit()
        return EventClaim(True, "claimed", event_key[:12], transaction_id)

    def complete(self, event_id: str) -> None:
        if not event_id:
            return
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE event_claims
                SET state = 'sent', completed_at = ?
                WHERE event_key = ?
                """,
                (int(self.clock()), _digest(event_id)),
            )
            connection.commit()

    def release(self, event_id: str) -> None:
        if not event_id:
            return
        with closing(self._connect()) as connection:
            connection.execute(
                "DELETE FROM event_claims WHERE event_key = ? AND state = 'processing'",
                (_digest(event_id),),
            )
            connection.commit()

    def counts(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT state, COUNT(*) FROM event_claims GROUP BY state"
            ).fetchall()
        values = {"processing": 0, "sent": 0}
        values.update({str(state): int(count) for state, count in rows})
        return values


__all__ = ["EventClaim", "EventLedger", "matrix_transaction_id"]
