#Author Yoav Batat van Dien
import socket

# הגדרות חיבור לשרת
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9081
BUFFER_SIZE = 1024


def get_number(prompt):

#    מקבל מספר מהמשתמש עם ולידציה

    while True:
        try:
            num_input = input(prompt)
            number = int(num_input)

            # בדיקת טווח
            if number > -10000 and number < 10000:
                return number
            else:
                print("Error: Number must be between -10000 and 10000")
        except ValueError:
            print("Error: Please enter a valid integer")


def get_operator():

#    מקבל אופרטור מהמשתמש

    valid_ops = ['+', '-', '*', '/']

    while True:
        op = input("Enter operator (+, -, *, /): ").strip()
        if op in valid_ops:
            return op
        else:
            print("Error: Invalid operator")


def get_input():

#    מקבל את כל הקלט מהמשתמש

    print("\n=== Calculator ===")

    # מספר ראשון
    num1 = get_number("Enter first number: ")

    # אופרטור
    operator = get_operator()

    # מספר שני - עם בדיקת חלוקה באפס
    while True:
        num2 = get_number("Enter second number: ")

        if operator == '/' and num2 == 0:
            print("Error: Cannot divide by zero")
            continue
        break

    return num1, operator, num2


def send_request(num1, operator, num2):

#    שולח את הבקשה לשרת ומקבל תשובה

    try:
        # יצירת socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5.0)

        # הכנת ההודעה
        message = f"{num1} {operator} {num2}"

        # שליחה לשרת
        client_socket.sendto(message.encode('utf-8'), (SERVER_HOST, SERVER_PORT))
        print(f"\nSent: {message}")

        # קבלת תשובה
        response, _ = client_socket.recvfrom(BUFFER_SIZE)
        result = response.decode('utf-8')

        client_socket.close()
        return result

    except socket.timeout:
        return "ERROR: Server timeout"
    except Exception as e:
        return f"ERROR: {str(e)}"


def show_result(result):

#    מציג את התוצאה למשתמש

    if result.startswith("ERROR"):
        print(f"\n{result}")
    else:
        print(f"\nResult: {result}")


def main():
    while True:
        try:
            # קבלת קלט
            num1, operator, num2 = get_input()

            # שליחה וקבלה
            result = send_request(num1, operator, num2)

            # הצגת תוצאה
            show_result(result)

            # שאלה האם להמשיך
            print("\n" + "=" * 30)
            choice = input("Another calculation? (y/n): ").strip().lower()
            if choice != 'y':
                print("Bye!")
                break

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()

