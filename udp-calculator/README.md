# 🧮 UDP Calculator

[![Live demo](https://img.shields.io/badge/▶_Live_demo-Open_project_page-0f9d76?style=for-the-badge)](https://yoavbvd.github.io/Python-Projects/)

A small **client–server calculator** that talks over **UDP**, written in pure Python.
The client sends a calculation such as `12 * 7`. The server checks it, calculates, and sends back `84`.

The project shows **socket programming**, **input validation**, **error handling**, and **basic server hardening** (rate limiting and protection against UDP reflection).

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-success)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## ⚡ Quick start

You need **Python 3.8 or later**. There is nothing to install: the project uses only the Python standard library.

```bash
git clone https://github.com/yoavbvd/Python-Projects.git
cd Python-Projects/udp-calculator
```

**Terminal 1 – start the server:**

```bash
python3 server.py
```

**Terminal 2 – start the client:**

```bash
python3 client.py
```

> On Windows, use `python` instead of `python3`.

### Example session

```text
UDP Calculator  ->  server 127.0.0.1:9081
Press Ctrl+C to quit.

First number: 12
Operator (+ - * /): *
Second number: 7

  12 * 7 = 84

Another calculation? (y/n): n
Bye!
```

---

## 🔄 How it works

```text
┌────────────┐   "12 * 7"  (UDP)    ┌────────────┐
│   client   │ ───────────────────► │   server   │
│            │ ◄─────────────────── │            │
└────────────┘       "84"           └────────────┘
```

1. The **client** asks for two numbers and an operator, and checks them locally.
2. It sends one UDP message in the format `<num1> <op> <num2>`.
3. The **server** checks the rate limit, validates the message again, and calculates.
4. The server replies with the result, or with a message that starts with `ERROR:`.

### Protocol rules

| Rule | Value |
|---|---|
| Message format | `<num1> <op> <num2>`, separated by spaces |
| Numbers | Integers from **-9999** to **9999** |
| Operators | `+` `-` `*` `/` |
| Division | Division by zero is rejected. The result is rounded to 6 decimal places. |
| Errors | Replies that start with `ERROR:` |
| Rate limit | **10 requests per 30 seconds** per client IP |

---

## 🛡️ Security features

| Feature | What it does |
|---|---|
| **Validation on both sides** | The client checks input for a good user experience. The server checks again, because it must never trust the client. |
| **Rate limiting per IP** | Each IP address can send 10 requests in 30 seconds. The key is the IP address, not IP + port, so a client cannot bypass the limit by opening new sockets. |
| **Silent drop when limited** | A rate-limited request gets no reply. An attacker who spoofs a victim's IP cannot use the server to send traffic to the victim (UDP reflection). |
| **Memory cleanup** | Idle clients are removed from the rate-limit table, so a flood of fake addresses cannot fill the memory. |
| **Local by default** | The server listens on `127.0.0.1`. You must choose `--host 0.0.0.0` to open it to the network. |
| **Never crashes** | Bad bytes, bad format and network errors are handled. The server continues to run. |

---

## ⚙️ Options

Both scripts accept `--host` and `--port`:

```bash
python3 server.py --host 0.0.0.0 --port 9090   # accept clients from your LAN
python3 client.py --host 192.168.1.20 --port 9090
```

If you open the server to the network, allow UDP port 9081 (or your port) in the firewall only for trusted hosts.

---

## ✅ Tests

The tests use the built-in `unittest` module. They include an end-to-end test that starts a real server.

```bash
python3 -m unittest discover -s tests -v
```

---

## 📁 Project structure

```text
udp-calculator/
├── server.py          # UDP server: validation, rate limiting, calculation
├── client.py          # Interactive command-line client
├── tests/
│   └── test_server.py # Unit tests + end-to-end test
└── README.md
```

---

## 🧠 Skills practiced

- UDP networking with Python `socket`
- Client–server protocol design
- Input validation and exception handling
- Rate limiting and DoS / reflection mitigation
- Command-line tools with `argparse`
- Automated testing with `unittest`

---

## 👤 Author

**Yoav Batat van Dien** · [GitHub @yoavbvd](https://github.com/yoavbvd)

Licensed under the [MIT License](../LICENSE.md).
