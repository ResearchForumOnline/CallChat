from __future__ import annotations

import unittest

from zero_matrix_bot import ambient_trigger, extract_command_text


class CommandExtractionTests(unittest.TestCase):
    def test_multiline_explicit_command_has_precedence(self) -> None:
        self.assertEqual(
            extract_command_text(
                "yo yo, what is up\n!zero status",
                mention_responses=True,
                ambient_responses=True,
            ),
            "status",
        )

    def test_one_message_returns_only_first_explicit_command(self) -> None:
        self.assertEqual(
            extract_command_text(
                "!zero test\n!zero status",
                mention_responses=True,
                ambient_responses=True,
            ),
            "test",
        )

    def test_mention_and_ambient_modes_remain_supported(self) -> None:
        self.assertEqual(
            extract_command_text("@zero are calls ready?", mention_responses=True, ambient_responses=False),
            "@zero are calls ready?",
        )
        self.assertEqual(
            extract_command_text("test", mention_responses=True, ambient_responses=True),
            "test",
        )
        self.assertIsNone(
            extract_command_text("ordinary room note", mention_responses=True, ambient_responses=True)
        )

    def test_test_and_ping_are_intentional_ambient_health_checks(self) -> None:
        self.assertTrue(ambient_trigger("test"))
        self.assertTrue(ambient_trigger("ping"))


if __name__ == "__main__":
    unittest.main()
