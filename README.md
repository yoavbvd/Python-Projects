# UDP Calculator – Python Project
Author: Yoav Batat van Dien

---

## Project Overview

This project implements a **UDP-based calculator** with a client-server architecture in Python.  

- The **client** sends arithmetic operations to the server and receives results.  
- The **server** validates input, calculates results, handles errors, and prevents DoS via rate limiting.  

The project demonstrates **networking, exception handling, input validation, and basic server hardening techniques**.

---

## 🛠 Skills Practiced

- Python programming & scripting  
- UDP networking (`socket`)  
- Input validation and exception handling  
- Client-server communication  
- Rate limiting / DoS prevention  
- Logging and safe server practices  
- Handling network timeouts and errors  

---

## 📂 How to Run

1. Start the server first:

```bash
python server.py
Run the client in another terminal:

bash
Copy code
python client.py
Follow prompts in the client for numbers and operators (+, -, *, /).
