from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from event_guard import EventLedger, matrix_transaction_id


class EventLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.now = 1_800_000_000
        self.ledger = EventLedger(
            Path(self.temporary.name) / "events.sqlite3",
            duplicate_window_seconds=30,
            clock=lambda: self.now,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_same_event_is_claimed_once(self) -> None:
        first = self.ledger.claim("$event-a", "!room", "@user", "test")
        second = self.ledger.claim("$event-a", "!room", "@user", "test")
        self.assertTrue(first.claimed)
        self.assertFalse(second.claimed)
        self.assertEqual(second.reason, "event")
        self.assertEqual(first.transaction_id, second.transaction_id)

    def test_same_prompt_with_new_event_is_coalesced(self) -> None:
        self.assertTrue(self.ledger.claim("$event-a", "!room", "@user", "!zero Test!").claimed)
        duplicate = self.ledger.claim("$event-b", "!room", "@user", "test")
        self.assertFalse(duplicate.claimed)
        self.assertEqual(duplicate.reason, "prompt")

    def test_prompt_can_be_repeated_after_window(self) -> None:
        self.assertTrue(self.ledger.claim("$event-a", "!room", "@user", "test").claimed)
        self.ledger.complete("$event-a")
        self.now += 31
        self.assertTrue(self.ledger.claim("$event-b", "!room", "@user", "test").claimed)

    def test_failed_processing_can_be_retried(self) -> None:
        self.assertTrue(self.ledger.claim("$event-a", "!room", "@user", "status").claimed)
        self.ledger.release("$event-a")
        self.assertTrue(self.ledger.claim("$event-a", "!room", "@user", "status").claimed)

    def test_completed_claim_is_recorded_without_plain_identifiers(self) -> None:
        self.assertTrue(self.ledger.claim("$event-a", "!room", "@user", "private wording").claimed)
        self.ledger.complete("$event-a")
        self.assertEqual(self.ledger.counts(), {"processing": 0, "sent": 1})
        database = (Path(self.temporary.name) / "events.sqlite3").read_bytes()
        for value in (b"$event-a", b"!room", b"@user", b"private wording"):
            self.assertNotIn(value, database)
        if os.name == "posix":
            self.assertEqual((Path(self.temporary.name) / "events.sqlite3").stat().st_mode & 0o777, 0o600)

    def test_transaction_ids_are_stable_and_bounded(self) -> None:
        first = matrix_transaction_id("$event-a")
        self.assertEqual(first, matrix_transaction_id("$event-a"))
        self.assertNotEqual(first, matrix_transaction_id("$event-b"))
        self.assertLessEqual(len(matrix_transaction_id("$event-a", "audio")), 64)
        self.assertNotIn("$event-a", first)


if __name__ == "__main__":
    unittest.main()
