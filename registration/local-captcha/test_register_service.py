import hashlib
import hmac
import unittest
from unittest.mock import patch

from register_service import PublicError, RegistrationState, registration_mac, validate_account


class Clock:
    def __init__(self):
        self.now = 1_000.0

    def __call__(self):
        return self.now


class RegistrationServiceTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.state = RegistrationState(clock=self.clock)

    @patch("register_service.secrets.randbelow", side_effect=[5, 9])
    @patch("register_service.secrets.token_urlsafe", return_value="challenge-token")
    def test_challenge_is_server_held_and_one_time(self, _token, _numbers):
        result = self.state.issue_challenge("192.0.2.1")
        self.assertEqual(result["prompt"], "7 + 11 =")
        self.assertNotIn("18", result.values())
        self.state.consume_challenge("192.0.2.1", "challenge-token", "18")
        with self.assertRaises(PublicError):
            self.state.consume_challenge("192.0.2.1", "challenge-token", "18")

    @patch("register_service.secrets.randbelow", side_effect=[1, 1])
    @patch("register_service.secrets.token_urlsafe", return_value="wrong-answer-token")
    def test_wrong_answer_consumes_challenge(self, _token, _numbers):
        self.state.issue_challenge("192.0.2.2")
        with self.assertRaisesRegex(PublicError, "incorrect"):
            self.state.consume_challenge("192.0.2.2", "wrong-answer-token", "99")
        with self.assertRaisesRegex(PublicError, "expired"):
            self.state.consume_challenge("192.0.2.2", "wrong-answer-token", "6")

    @patch("register_service.secrets.randbelow", side_effect=[2, 2])
    @patch("register_service.secrets.token_urlsafe", return_value="bound-token")
    def test_challenge_is_bound_to_client_ip(self, _token, _numbers):
        self.state.issue_challenge("192.0.2.3")
        with self.assertRaisesRegex(PublicError, "expired"):
            self.state.consume_challenge("192.0.2.4", "bound-token", "8")

    @patch("register_service.secrets.randbelow", side_effect=[3, 3])
    @patch("register_service.secrets.token_urlsafe", return_value="expired-token")
    def test_challenge_expires(self, _token, _numbers):
        self.state.issue_challenge("192.0.2.5")
        self.clock.now += 301
        with self.assertRaisesRegex(PublicError, "expired"):
            self.state.consume_challenge("192.0.2.5", "expired-token", "10")

    def test_account_validation(self):
        self.assertEqual(validate_account("Test.User", "correct horse battery"), ("test.user", "correct horse battery"))
        with self.assertRaises(PublicError):
            validate_account("admin space", "correct horse battery")
        with self.assertRaises(PublicError):
            validate_account("valid", "short")

    def test_synapse_mac_matches_protocol(self):
        actual = registration_mac("secret", "nonce", "alice", "password1234")
        digest = hmac.new(b"secret", digestmod=hashlib.sha1)
        digest.update(b"nonce\x00alice\x00password1234\x00notadmin")
        self.assertEqual(actual, digest.hexdigest())


if __name__ == "__main__":
    unittest.main()
