import json
import re
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from register_service import PublicError, RegistrationHandler, RegistrationState, SynapseRegistrar, validate_account


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

    def test_synapse_helper_is_called_for_non_admin_account(self):
        calls = []
        registrar = SynapseRegistrar("s" * 32)
        registrar._registration_helper = lambda: lambda **kwargs: calls.append(kwargs)
        self.assertEqual(registrar.register("alice", "correct horse battery"), "@alice:callchat.org")
        self.assertEqual(calls[0]["admin"], False)
        self.assertEqual(calls[0]["user"], "alice")
        self.assertEqual(calls[0]["password"], "correct horse battery")


class FakeRegistrar:
    def __init__(self):
        self.calls = []

    def register(self, username, password):
        self.calls.append((username, password))
        return f"@{username}:callchat.org"


class RegistrationHttpTests(unittest.TestCase):
    def setUp(self):
        self.registrar = FakeRegistrar()
        handler = type("TestRegistrationHandler", (RegistrationHandler,), {
            "state": RegistrationState(),
            "registrar": self.registrar,
            "allowed_origin": "https://callchat.org",
        })
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.headers = {"Origin": "https://callchat.org", "X-CallChat-Same-Origin": "1"}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_http_challenge_and_registration(self):
        request = urllib.request.Request(self.base + "/v1/challenge", headers=self.headers)
        with urllib.request.urlopen(request, timeout=2) as response:
            challenge = json.load(response)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
        answer = sum(int(value) for value in re.findall(r"\d+", challenge["prompt"]))
        payload = json.dumps({
            "username": "Alice",
            "password": "correct horse battery",
            "challenge_id": challenge["challenge_id"],
            "captcha_answer": str(answer),
        }).encode()
        request = urllib.request.Request(
            self.base + "/v1/register", data=payload, method="POST",
            headers={**self.headers, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            result = json.load(response)
        self.assertEqual(result["user_id"], "@alice:callchat.org")
        self.assertEqual(self.registrar.calls, [("alice", "correct horse battery")])

    def test_cross_site_origin_is_rejected(self):
        request = urllib.request.Request(
            self.base + "/v1/challenge",
            headers={"Origin": "https://cross-site.invalid", "X-CallChat-Same-Origin": "1"},
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)
        self.assertEqual(raised.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
