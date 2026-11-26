"""Unit tests for the UDP Calculator server. Run: python -m unittest -v"""

import os
import socket
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import server  # noqa: E402


class ParseRequestTests(unittest.TestCase):
    def test_valid_request(self):
        self.assertEqual(server.parse_request("12 * -3"), (12, "*", -3))

    def test_extra_spaces_are_allowed(self):
        self.assertEqual(server.parse_request("  5   +  6 "), (5, "+", 6))

    def test_bad_requests_are_rejected(self):
        bad = ["", "1 +", "1 + 2 3", "a + 1", "1.5 + 1", "1 % 2",
               "10000 + 1", "1 - -10000", "5 / 0"]
        for message in bad:
            with self.subTest(message=message):
                with self.assertRaises(ValueError):
                    server.parse_request(message)

    def test_range_limits_are_inclusive(self):
        self.assertEqual(server.parse_request("9999 + -9999"), (9999, "+", -9999))


class CalculateTests(unittest.TestCase):
    def test_operations(self):
        self.assertEqual(server.calculate(7, "+", 5), "12")
        self.assertEqual(server.calculate(7, "-", 9), "-2")
        self.assertEqual(server.calculate(7, "*", 6), "42")
        self.assertEqual(server.calculate(8, "/", 2), "4")
        self.assertEqual(server.calculate(1, "/", 3), "0.333333")


class BuildResponseTests(unittest.TestCase):
    def test_success_and_errors(self):
        self.assertEqual(server.build_response(b"2 + 2"), "4")
        self.assertEqual(server.build_response(b"5 / 0"), "ERROR: division by zero")
        self.assertTrue(server.build_response(b"\xff\xfe").startswith("ERROR"))


class RateLimiterTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.limiter = server.RateLimiter(max_requests=3, window=10, clock=lambda: self.now)

    def test_blocks_after_limit_and_recovers(self):
        client = ("10.0.0.1", 5000)
        self.assertTrue(all(self.limiter.allow(client) for _ in range(3)))
        self.assertFalse(self.limiter.allow(client))
        self.now = 11
        self.assertTrue(self.limiter.allow(client))

    def test_clients_are_independent(self):
        for _ in range(3):
            self.limiter.allow(("10.0.0.1", 1))
        self.assertTrue(self.limiter.allow(("10.0.0.2", 1)))

    def test_idle_clients_are_removed(self):
        for i in range(100):
            self.limiter.allow(("10.0.0.%d" % i, 1))
        self.now = 25
        self.limiter.allow(("10.0.1.1", 1))
        self.assertEqual(len(self.limiter._requests), 1)


class EndToEndTest(unittest.TestCase):
    """Starts a real server on a free local port and talks to it over UDP."""

    def test_round_trip(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()

        limiter = server.RateLimiter(max_requests=2, window=60)
        thread = threading.Thread(target=server.serve, args=("127.0.0.1", port, limiter),
                                  daemon=True)
        thread.start()

        import client
        import time
        time.sleep(0.3)
        self.assertEqual(client.send_request("6 * 7", "127.0.0.1", port), "42")
        self.assertEqual(client.send_request("1 / 0", "127.0.0.1", port),
                         "ERROR: division by zero")
        # Third request is over the limit: the server drops it, the client times out.
        client.TIMEOUT_SECONDS = 1.0
        self.assertIn("no reply", client.send_request("1 + 1", "127.0.0.1", port))


if __name__ == "__main__":
    unittest.main()
