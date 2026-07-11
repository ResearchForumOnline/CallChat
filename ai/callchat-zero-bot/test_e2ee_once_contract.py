from __future__ import annotations

import unittest
from pathlib import Path


class EncryptedTransportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Path(__file__).with_name("zero_matrix_bot_e2ee.py").read_text(encoding="utf-8")

    def test_matrix_send_uses_deterministic_transaction_id(self) -> None:
        self.assertIn("tx_id=transaction_id", self.source)
        self.assertIn("transaction_id=claim.transaction_id", self.source)

    def test_event_claim_completes_or_releases(self) -> None:
        self.assertIn("self.ledger.claim", self.source)
        self.assertIn("self.ledger.complete", self.source)
        self.assertIn("self.ledger.release", self.source)

    def test_edits_and_notice_events_do_not_trigger_new_answers(self) -> None:
        self.assertIn('relation.get("rel_type") == "m.replace"', self.source)
        self.assertIn("add_event_callback(bot.on_message, RoomMessageText)", self.source)
        self.assertNotIn("RoomMessageNotice", self.source)

    def test_replies_are_related_to_the_single_input_event(self) -> None:
        self.assertIn('"m.in_reply_to": {"event_id": reply_event_id}', self.source)


if __name__ == "__main__":
    unittest.main()
