import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zero_agent_bridge as bridge


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return json.dumps({"id": "test-ionq-job-1234", "status": "submitted"}).encode("utf-8")


class IonQReceiptTests(unittest.TestCase):
    def setUp(self):
        self.original_key = bridge.IONQ_API_KEY

    def tearDown(self):
        bridge.IONQ_API_KEY = self.original_key

    def test_requires_server_side_key(self):
        bridge.IONQ_API_KEY = ""
        result, error = bridge.request_ionq_receipt("a" * 64)
        self.assertIsNone(result)
        self.assertIn("not configured", error)

    def test_rejects_invalid_commitment(self):
        bridge.IONQ_API_KEY = "test-only-key"
        result, error = bridge.request_ionq_receipt("not-a-commitment")
        self.assertIsNone(result)
        self.assertIn("valid commitment", error)

    @patch("zero_agent_bridge.provider_control.urllib.request.urlopen", return_value=FakeResponse())
    def test_submits_simulator_receipt_outside_key_path(self, mocked_urlopen):
        bridge.IONQ_API_KEY = "test-only-key"
        result, error = bridge.request_ionq_receipt("b" * 64)
        self.assertIsNone(error)
        self.assertEqual(result["backend"], "simulator")
        self.assertFalse(result["key_material"])
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["backend"], "simulator")
        self.assertEqual(payload["metadata"]["security_boundary"], "provider-isolated")
        self.assertNotIn("plaintext", payload)
        self.assertNotIn("passphrase", payload)


class OriginTests(unittest.TestCase):
    def setUp(self):
        self.original_origins = bridge.ALLOWED_ORIGINS.copy()

    def tearDown(self):
        bridge.ALLOWED_ORIGINS.clear()
        bridge.ALLOWED_ORIGINS.update(self.original_origins)

    def test_returns_canonical_allowlisted_origin(self):
        bridge.ALLOWED_ORIGINS.clear()
        bridge.ALLOWED_ORIGINS.add("https://callchat.example")
        self.assertEqual(
            bridge.canonical_allowed_origin("https://callchat.example"),
            "https://callchat.example",
        )
        self.assertTrue(bridge.allowed_origin("https://callchat.example"))

    def test_rejects_unlisted_and_header_injection_origins(self):
        bridge.ALLOWED_ORIGINS.clear()
        bridge.ALLOWED_ORIGINS.add("https://callchat.example")
        self.assertIsNone(bridge.canonical_allowed_origin("https://attacker.example"))
        self.assertIsNone(
            bridge.canonical_allowed_origin("https://callchat.example\r\nX-Test: injected")
        )
        self.assertFalse(bridge.allowed_origin("https://attacker.example"))

    def test_empty_allowlist_rejects_cross_origin_requests(self):
        bridge.ALLOWED_ORIGINS.clear()
        self.assertIsNone(bridge.canonical_allowed_origin("https://callchat.example"))
        self.assertFalse(bridge.allowed_origin("https://callchat.example"))


class SecretRoutingTests(unittest.TestCase):
    def test_detects_assigned_secrets_without_blocking_general_questions(self):
        self.assertTrue(bridge.likely_secretish("password: CorrectHorseBatteryStaple"))
        self.assertTrue(bridge.likely_secretish("access token = syt_abcdefghijklmnopqrstuvwxyz123456"))
        self.assertFalse(bridge.likely_secretish("How should I protect a password?"))

    def test_likely_secret_skips_cloud_provider(self):
        with patch(
            "zero_agent_bridge.provider_control.cloud_chat_completion",
            return_value=("cloud reply", {"provider": "openai", "model": "gpt-5.5"}),
        ) as cloud, patch(
            "zero_agent_bridge.ask_openzero", return_value="local only"
        ) as local:
            self.assertEqual(bridge.ask_ai("api key: sk-private-example-123456"), "local only")
            cloud.assert_not_called()
            local.assert_called_once()


if __name__ == "__main__":
    unittest.main()
