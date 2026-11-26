"""UDP Calculator - server.

Receives requests like "12 * 7" over UDP, checks them, and sends back the
result. The server includes basic hardening:

* strict input validation (format, range, operator, division by zero)
* per-client rate limiting, with memory cleanup of idle clients
* no reply to rate-limited clients (limits UDP reflection / amplification)
* the server never crashes on a bad packet

Author: Yoav Batat van Dien
"""

import argparse
import socket
import time
from collections import defaultdict

DEFAULT_HOST = "127.0.0.1"   # Local only. Use --host 0.0.0.0 to accept LAN clients.
DEFAULT_PORT = 9081
BUFFER_SIZE = 1024

MIN_VALUE = -9999            # Numbers must be in the range -9999 .. 9999
MAX_VALUE = 9999
OPERATORS = ("+", "-", "*", "/")

MAX_REQUESTS = 10            # Each client can send 10 requests ...
TIME_WINDOW = 30             # ... in each 30-second window.


class RateLimiter:
    """Sliding-window rate limiter, keyed by client IP address."""

    def __init__(self, max_requests=MAX_REQUESTS, window=TIME_WINDOW, clock=time.monotonic):
        self.max_requests = max_requests
        self.window = window
        self.clock = clock
        self._requests = defaultdict(list)
        self._last_cleanup = clock()

    def allow(self, client):
        """Return True if the client can send one more request now."""
        now = self.clock()
        self._cleanup(now)

        recent = [t for t in self._requests[client] if now - t < self.window]
        if len(recent) >= self.max_requests:
            self._requests[client] = recent
            return False

        recent.append(now)
        self._requests[client] = recent
        return True

    def _cleanup(self, now):
        """Remove idle clients, so memory does not grow without limit."""
        if now - self._last_cleanup < self.window:
            return
        idle = [c for c, times in self._requests.items()
                if not times or now - times[-1] >= self.window]
        for client in idle:
            del self._requests[client]
        self._last_cleanup = now


def parse_request(message):
    """Parse "num1 op num2". Return (num1, op, num2) or raise ValueError."""
    parts = message.split()
    if len(parts) != 3:
        raise ValueError("invalid message format, expected: <num1> <op> <num2>")

    num1_text, operator, num2_text = parts
    try:
        num1 = int(num1_text)
        num2 = int(num2_text)
    except ValueError:
        raise ValueError("numbers must be integers") from None

    if not MIN_VALUE <= num1 <= MAX_VALUE:
        raise ValueError(f"number1 out of range ({MIN_VALUE}..{MAX_VALUE})")
    if not MIN_VALUE <= num2 <= MAX_VALUE:
        raise ValueError(f"number2 out of range ({MIN_VALUE}..{MAX_VALUE})")
    if operator not in OPERATORS:
        raise ValueError("invalid operator, use + - * /")
    if operator == "/" and num2 == 0:
        raise ValueError("division by zero")

    return num1, operator, num2


def calculate(num1, operator, num2):
    """Do the calculation and return the result as text."""
    if operator == "+":
        result = num1 + num2
    elif operator == "-":
        result = num1 - num2
    elif operator == "*":
        result = num1 * num2
    else:
        result = num1 / num2
        if result.is_integer():
            result = int(result)
        else:
            result = round(result, 6)
    return str(result)


def build_response(data):
    """Turn raw request bytes into the response text."""
    try:
        message = data.decode("utf-8").strip()
        num1, operator, num2 = parse_request(message)
        return calculate(num1, operator, num2)
    except UnicodeDecodeError:
        return "ERROR: message must be UTF-8 text"
    except ValueError as error:
        return f"ERROR: {error}"


def serve(host, port, limiter=None):
    """Run the server loop until Ctrl+C."""
    limiter = limiter or RateLimiter()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.settimeout(1.0)  # Wake up every second, so Ctrl+C works.
        print(f"UDP Calculator server listening on {host}:{port}  (Ctrl+C to stop)")

        while True:
            try:
                data, client = server_socket.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            except OSError as error:
                print(f"[!] Receive error: {error}")
                continue

            # Rate limit first, before any other work. The key is the IP address
            # only: a client gets a new source port for each socket, so keying by
            # (IP, port) is easy to bypass. Rate-limited clients get no reply, so
            # a spoofed source address cannot be used for reflection.
            if not limiter.allow(client[0]):
                print(f"[!] Rate limit: dropped request from {client[0]}:{client[1]}")
                continue

            response = build_response(data)
            try:
                server_socket.sendto(response.encode("utf-8"), client)
            except OSError as error:
                print(f"[!] Send error to {client}: {error}")
                continue
            print(f"[+] {client[0]}:{client[1]}  {data[:64]!r} -> {response}")


def main():
    parser = argparse.ArgumentParser(description="UDP Calculator server")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"address to listen on (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"UDP port (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    try:
        serve(args.host, args.port)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except OSError as error:
        print(f"Cannot start server on {args.host}:{args.port}: {error}")


if __name__ == "__main__":
    main()
