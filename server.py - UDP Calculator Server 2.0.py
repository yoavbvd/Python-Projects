#Author Yoav Batat van Dien
import socket
import time
from collections import defaultdict

# הגדרות שרת
HOST = '0.0.0.0'
PORT = 9081
BUFFER_SIZE = 1024

# הגדרות למניעת DoS - סעיף 4
MAX_REQUESTS = 10  # מקסימום בקשות ללקוח
TIME_WINDOW = 30  # חלון זמן בשניות
request_tracker = defaultdict(list)  # מעקב אחרי בקשות


def validate_input(num1_str, operator, num2_str):

#    בודק תקינות הקלט - סעיף 3.3

    try:
        # המרה למספרים שלמים
        num1 = int(num1_str)
        num2 = int(num2_str)

        # בדיקת טווח
        if num1 <= -10000 or num1 >= 10000:
            return False, "ERROR: number1 out of range", None, None
        if num2 <= -10000 or num2 >= 10000:
            return False, "ERROR: number2 out of range", None, None

        # בדיקת אופרטור
        if operator not in ['+', '-', '*', '/']:
            return False, "ERROR: invalid operator", None, None

        # בדיקת חלוקה באפס
        if operator == '/' and num2 == 0:
            return False, "ERROR: division by zero", None, None

        return True, None, num1, num2

    except ValueError:
        return False, "ERROR: invalid number format", None, None


def check_rate_limit(client_address):

#    בודק האם הלקוח עבר את הגבול - מניעת DoS

    current_time = time.time()
    timestamps = request_tracker[client_address]

    # מנקה timestamps ישנים
    timestamps[:] = [t for t in timestamps if current_time - t < TIME_WINDOW]

    # בדיקה אם עבר את הגבול
    if len(timestamps) >= MAX_REQUESTS:
        return False, "ERROR: too many requests, please try later"

    # מוסיף את הבקשה הנוכחית
    timestamps.append(current_time)
    return True, None


def calculate(num1, operator, num2):

#    מבצע את החישוב המתמטי

    if operator == '+':
        result = num1 + num2
    elif operator == '-':
        result = num1 - num2
    elif operator == '*':
        result = num1 * num2
    else:  # operator == '/'
        result = num1 / num2

    return str(result)


def handle_request(data, client_address, server_socket):

#    מטפל בבקשה מהלקוח

    try:
        # פענוח ההודעה
        message = data.decode('utf-8').strip()
        parts = message.split(' ')

        if len(parts) != 3:
            response = "ERROR: invalid message format"
            server_socket.sendto(response.encode('utf-8'), client_address)
            return

        num1_str, operator, num2_str = parts

        # בדיקת rate limiting
        allowed, rate_error = check_rate_limit(client_address)
        if not allowed:
            server_socket.sendto(rate_error.encode('utf-8'), client_address)
            print(f"Rate limit exceeded for {client_address}")
            return

        # ולידציה
        is_valid, error_msg, num1, num2 = validate_input(num1_str, operator, num2_str)
        if not is_valid:
            server_socket.sendto(error_msg.encode('utf-8'), client_address)
            print(f"Validation error: {error_msg}")
            return

        # ביצוע החישוב
        result = calculate(num1, operator, num2)
        server_socket.sendto(result.encode('utf-8'), client_address)
        print(f"Sent result to {client_address}: {num1} {operator} {num2} = {result}")

    except Exception as e:
        # Hardening - השרת לא נופל
        error_response = "ERROR: internal server error"
        try:
            server_socket.sendto(error_response.encode('utf-8'), client_address)
        except:
            pass
        print(f"Error: {str(e)}")


def main():
    # יצירת socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(1.0)  # timeout למניעת תקיעות

    try:
        server_socket.bind((HOST, PORT))
        print(f"Server started on {HOST}:{PORT}")
        print("Waiting for requests...")

        while True:
            try:
                data, client_address = server_socket.recvfrom(BUFFER_SIZE)
                print(f"\nReceived from {client_address}")
                handle_request(data, client_address, server_socket)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error in loop: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("\nThe server is shutting down...")
    finally:
        server_socket.close()
        print("Server closed.")


if __name__ == "__main__":
    main()