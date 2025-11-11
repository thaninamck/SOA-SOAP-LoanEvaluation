# 🧩 Loan Evaluation System — SOAP Microservices Architecture

This project implements a **modular loan evaluation platform** using a **SOAP-based microservice architecture** built with Python and Spyne.  
It simulates the real-world process of assessing a loan request by combining several specialized services (credit, property, decision, etc.) into a **composite orchestration layer**.

---

## 📘 Overview

The system processes a client’s loan application through several stages:

1. **Information Extraction Service**  
   → Parses structured loan request text to extract relevant fields (name, income, expenses, loan amount, property details).

2. **Credit Check Service**  
   → Generates or retrieves a simulated credit score and history data.

3. **Property Evaluation Service**  
   → Estimates the property’s market value based on description and context.

4. **Decision Service**  
   → Applies institutional financial policies (loan-to-value ratio, debt-to-income ratio, credit score thresholds, etc.)  
   → Produces an **approval or rejection decision** with detailed reasoning and recommendations.

5. **Composite Service**  
   → Orchestrates all services in sequence.  
   → Consolidates all results into a single decision response.  
   → Stores results in a local JSON “database” and writes notifications.

---

## ⚙️ Architecture Diagram

Figure


Each service runs as an independent SOAP endpoint and communicates using JSON-encoded payloads over SOAP.

---

## 🧠 Features

- ✅ Modular architecture (microservices)
- ✅ SOAP endpoints for interoperability
- ✅ Rich and detailed decision logic
- ✅ Automatic orchestration (via `main.py`)
- ✅ Persistent database with timestamped request IDs
- ✅ Human-readable notification log
- ✅ Designed for easy integration and testing (e.g., SoapUI)
- ✅ Easy debugging through each service's logs (via `logs\`)

---

## 🧩 How to run

### Clone & Setup Environment
```bash
$ git clone https://github.com/LyCrash/SOA-SOAP-LoanEvaluation.git
$ cd SOA-SOAP-LoanEvaluation
$ python -m venv venv
$ .\venv\Scripts\activate   # or source venv/bin/activate on Linux
$ pip install -r src\requirements.txt
```
### Start all services
```bash
$ python main.py
```
You should see something like this:

🚀 Starting Information Extraction on port 8001...
✅ Information Extraction running (PID: 4940)
...
🧩 Composite service is available at:
👉 http://127.0.0.1:8000/LoanEvaluationService?wsdl

A `logs\` folder is automatically created with individual service logs.

### Run a client test
The `clients\` folder contains different tests, you can play on the loan_text message to try different scenarios
python client\client_test.py

Each client sends a SOAP request to the Composite Service (port 8000), which orchestrates the full workflow. Results are automatically:
- Stored in data/database.json
- Logged in notifications.log
- Displayed in the client terminal

### Stop All Services
Simply press `Ctrl+C` in the terminal running main.py.


## 🧰 Technologies Used
- Python 3.10
- Spyne — SOAP web service framework
- Twisted / WSGI — for asynchronous service hosting
- JSON / SOAP — for data serialization
- subprocess + logging — service orchestration and monitoring

## 🏁 Notes
- All ports (8000–8004) must be available before running.
- Ensure no other instances of the services are already running.
- You can modify parameters (thresholds, base rate, etc.) inside decision_service.py to simulate different policy rules.
