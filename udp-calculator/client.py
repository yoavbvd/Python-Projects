"""UDP Calculator - client.

Asks the user for two numbers and an operator, sends the request to the
server over UDP, and shows the result.

Author: Yoav Batat van Dien
"""

import argparse
import socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9081
BUFFER_SIZE = 1024
TIMEOUT_SECONDS = 5.0

MIN_VALUE = -9999
MAX_VALUE = 9999
OPERATORS = ("+", "-", "*", "/")


def ask_number(prompt):
    """Ask until the user types an integer in the allowed range."""
    while True:
        text = input(prompt).strip()
        try:
            number = int(text)
        except ValueError:
            print("  Please enter a whole number, for example 42 or -7.")
            continue
        if MIN_VALUE <= number <= MAX_VALUE:
            return number
        print(f"  The number must be between {MIN_VALUE} and {MAX_VALUE}.")


def ask_operator():
    """Ask until the user types a valid operator."""
    while True:
        operator = input("Operator (+ - * /): ").strip()
        if operator in OPERATORS:
            return operator
        print("  Please enter one of: + - * /")


def ask_calculation():
    """Ask for a full calculation. Return (num1, operator, num2)."""
    num1 = ask_number("First number: ")
    operator = ask_operator()
    while True:
        num2 = ask_number("Second number: ")
        if operator == "/" and num2 == 0:
            print("  You cannot divide by zero. Enter another number.")
            continue
        return num1, operator, num2


def send_request(message, host, port):
    """Send one request and return the server's reply as text."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.settimeout(TIMEOUT_SECONDS)
        client_socket.sendto(message.encode("utf-8"), (host, port))
        try:
            reply, _ = client_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            return ("ERROR: no reply from server. Is the server running? "
                    "You may also be rate limited (10 requests / 30 s).")
        except ConnectionResetError:
            return "ERROR: server is not reachable. Start server.py first."
    return reply.decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="UDP Calculator client")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"server address (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"server UDP port (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    print(f"UDP Calculator  ->  server {args.host}:{args.port}")
    print("Press Ctrl+C to quit.\n")

    try:
        while True:
            num1, operator, num2 = ask_calculation()
            message = f"{num1} {operator} {num2}"
            reply = send_request(message, args.host, args.port)

            if reply.startswith("ERROR"):
                print(f"\n  {reply}\n")
            else:
                print(f"\n  {message} = {reply}\n")

            if input("Another calculation? (y/n): ").strip().lower() != "y":
                break
            print()
    except (KeyboardInterrupt, EOFError):
        print()
    print("Bye!")


if __name__ == "__main__":
    main()
