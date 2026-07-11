import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import provider_control


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit=-1):
        return json.dumps(self.payload).encode("utf-8")


class ProviderStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Path(self.temp.name) / "provider-secrets.json"

    def tearDown(self):
        self.temp.cleanup()

    @patch.dict(os.environ, {}, clear=False)
    def test_writes_owner_only_store_and_redacts_status(self):
        key = "sk-test-provider-key-1234567890"
        state = provider_control.update_provider_state(
            {
                "active_ai_provider": "openai",
                "providers": {
                    "openai": {
                        "api_key": key,
                        "enabled": True,
                        "model": "gpt-5.5",
                    }
                },
            },
            self.store,
        )
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.store.stat().st_mode), 0o600)
        public = provider_control.public_provider_status(state)
        self.assertTrue(public["providers"]["openai"]["configured"])
        self.assertNotIn(key, json.dumps(public))
        self.assertNotIn("fingerprint", json.dumps(public))

    def test_rejects_unconfigured_active_provider(self):
        with self.assertRaises(provider_control.ProviderConfigError):
            provider_control.update_provider_state(
                {"active_ai_provider": "groq"},
                self.store,
            )

    def test_rejects_disabled_active_provider(self):
        with self.assertRaises(provider_control.ProviderConfigError):
            provider_control.update_provider_state(
                {
                    "active_ai_provider": "openai",
                    "providers": {
                        "openai": {
                            "api_key": "sk-test-provider-key-1234567890",
                            "enabled": False,
                        }
                    },
                },
                self.store,
            )

    def test_requires_paid_qpu_confirmation(self):
        with self.assertRaises(provider_control.ProviderConfigError):
            provider_control.update_provider_state(
                {
                    "providers": {
                        "ionq": {
                            "api_key": "ionq-test-key-1234567890",
                            "enabled": True,
                            "backend": "qpu.aria-1",
                            "allow_paid_qpu": False,
                        }
                    }
                },
                self.store,
            )


class ProviderRequestTests(unittest.TestCase):
    @patch("provider_control.urllib.request.urlopen")
    def test_openai_key_test_returns_model_ids(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"data": [{"id": "gpt-5.5"}, {"id": "gpt-5.4-mini"}]}
        )
        result = provider_control.test_provider_key(
            "openai", "sk-test-provider-key-1234567890"
        )
        self.assertTrue(result["valid"])
        self.assertIn("gpt-5.5", result["models"])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, provider_control.PROVIDER_ENDPOINTS["openai"]["models"])
        self.assertTrue(request.headers["Authorization"].startswith("Bearer "))

    @patch("provider_control.urllib.request.urlopen")
    def test_cloud_chat_uses_configured_model_without_key_in_body(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"choices": [{"message": {"content": "Provider route ready."}}]}
        )
        key = "sk-test-provider-key-1234567890"
        state = provider_control.default_provider_state()
        state["active_ai_provider"] = "openai"
        state["providers"]["openai"].update(
            {"api_key": key, "enabled": True, "model": "gpt-5.5"}
        )
        text, route = provider_control.cloud_chat_completion(
            [{"role": "user", "content": "status"}], state=state
        )
        self.assertEqual(text, "Provider route ready.")
        self.assertEqual(route, {"provider": "openai", "model": "gpt-5.5"})
        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(body["model"], "gpt-5.5")
        self.assertNotIn(key, request.data.decode("utf-8"))
        self.assertIn("max_completion_tokens", body)
        self.assertNotIn("temperature", body)

    @patch("provider_control.urllib.request.urlopen")
    def test_ionq_receipt_contains_commitment_not_key_material(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"id": "test-ionq-job-1234", "status": "submitted"}
        )
        state = provider_control.default_provider_state()
        state["providers"]["ionq"].update(
            {
                "api_key": "ionq-test-key-1234567890",
                "enabled": True,
                "backend": "simulator",
            }
        )
        commitment = "a" * 64
        result, error = provider_control.ionq_receipt(commitment, state=state)
        self.assertIsNone(error)
        self.assertFalse(result["key_material"])
        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(body["metadata"]["commitment"], commitment)
        self.assertNotIn("plaintext", body)
        self.assertNotIn("passphrase", body)
        self.assertNotIn("api_key", body)

    @patch("provider_control.urllib.request.urlopen")
    def test_ionq_factor_job_uses_measurements_without_client_secret(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"id": "019f52ea-8506-74f8-acb1-2699c0a8fcec", "status": "submitted"}
        )
        state = provider_control.default_provider_state()
        state["providers"]["ionq"].update(
            {
                "api_key": "ionq-test-key-1234567890",
                "enabled": True,
                "backend": "simulator",
            }
        )
        commitment = "b" * 64
        result, error = provider_control.ionq_submit_factor_job(commitment, state=state)
        self.assertIsNone(error)
        self.assertEqual(result["source_class"], "simulator-test")
        self.assertFalse(result["final_factor_material"])
        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(body["shots"], 512)
        self.assertEqual(body["input"]["qubits"], 8)
        self.assertEqual(len(body["input"]["circuit"]), 8)
        self.assertEqual(body["metadata"]["client_commitment"], commitment)
        self.assertNotIn("client_secret", json.dumps(body))
        self.assertNotIn("final_factor", json.dumps(body))

    @patch("provider_control.urllib.request.urlopen")
    def test_ionq_completed_factor_returns_validated_measurement_digest(self, urlopen):
        job_id = "019f52ea-8506-74f8-acb1-2699c0a8fcec"
        urlopen.side_effect = [
            FakeResponse(
                {
                    "id": job_id,
                    "status": "completed",
                    "backend": "qpu.forte-1",
                    "completed_at": "2026-07-11T20:00:00Z",
                    "metadata": {
                        "purpose": "callchat-qpu-factor-v1",
                        "client_commitment": "c" * 64,
                        "security_boundary": "no-final-factor-or-plaintext",
                    },
                }
            ),
            FakeResponse({"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}),
        ]
        state = provider_control.default_provider_state()
        state["providers"]["ionq"].update(
            {
                "api_key": "ionq-test-key-1234567890",
                "enabled": True,
                "backend": "qpu.forte-1",
                "allow_paid_qpu": True,
            }
        )
        result, error = provider_control.ionq_factor_job(job_id, "c" * 64, state=state)
        self.assertIsNone(error)
        self.assertEqual(result["source_class"], "qpu-measurement")
        self.assertTrue(result["measurement_contribution"])
        self.assertRegex(result["measurement_sha512"], r"^[a-f0-9]{128}$")
        self.assertRegex(result["result_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn("probabilities", result)

    @patch("provider_control.urllib.request.urlopen")
    def test_ionq_factor_rejects_a_different_job_commitment(self, urlopen):
        job_id = "019f52ea-8506-74f8-acb1-2699c0a8fcec"
        urlopen.return_value = FakeResponse(
            {
                "id": job_id,
                "status": "completed",
                "backend": "simulator",
                "metadata": {
                    "purpose": "callchat-qpu-factor-v1",
                    "client_commitment": "e" * 64,
                    "security_boundary": "no-final-factor-or-plaintext",
                },
            }
        )
        state = provider_control.default_provider_state()
        state["providers"]["ionq"].update(
            {"api_key": "ionq-test-key-1234567890", "enabled": True}
        )
        result, error = provider_control.ionq_factor_job(job_id, "f" * 64, state=state)
        self.assertIsNone(result)
        self.assertIn("does not match", error)
        self.assertEqual(urlopen.call_count, 1)

    @patch("provider_control.urllib.request.urlopen")
    def test_ionq_hardware_factor_requires_per_job_cost_confirmation(self, urlopen):
        state = provider_control.default_provider_state()
        state["providers"]["ionq"].update(
            {
                "api_key": "ionq-test-key-1234567890",
                "enabled": True,
                "backend": "qpu.forte-1",
                "allow_paid_qpu": True,
            }
        )
        result, error = provider_control.ionq_submit_factor_job("d" * 64, state=state)
        self.assertIsNone(result)
        self.assertIn("Confirm paid QPU use", error)
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
