
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
from suds.client import Client
import sys
import io

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# --- CONFIG --- #
COMPOSITE = "http://127.0.0.1:8000/LoanEvaluationService?wsdl"
client = Client(COMPOSITE)

# --- Loan request text --- #
loan_text = """
Nom du Client: Marc Lefevre
Adresse: 25 Avenue des Sciences, Lyon
Email: marc.lefevre@email.com
Numéro de Téléphone: +33677889900
Montant du Prêt Demandé: 200000
Revenu Mensuel: 6500
Dépenses Mensuelles: 1500
Description de la Propriété: Maison individuelle récente de 120m² avec jardin, située dans un quartier résidentiel calme. État du bien excellent.
"""

# --- 1️⃣ Submit the request --- #

print("📨 Submitting loan request...")
response_json = client.service.submitRequest(loan_text)
try:
    response = json.loads(response_json)
except Exception as e:
    print("❌ Failed to parse response as JSON:", e)
    print("Raw response:", response_json)
    exit()

print("DEBUG - Response from service:", response)

if response.get("status") != "done":
    print("❌ Error submitting request:", response.get("message", "Unknown error"))
    exit()

request_id = response.get("request_id")
if not request_id:
    print("❌ No request_id returned! Response was:", response)
    exit()

print(f"✅ Request submitted successfully! ID: {request_id}")


# --- 2️⃣ Wait (simulate delay if processing was async) --- #
print("\n⏳ Waiting for processing to complete (simulated delay)...")
time.sleep(2)

# --- 3️⃣ Fetch results using getResult --- #
print("\n📥 Fetching result using getResult...")
result_json = client.service.getResult(request_id)

try:
    result = json.loads(result_json)
except Exception as e:
    print("❌ Failed to parse getResult response as JSON:", e)
    print("Raw response:", result_json)
    exit()


if result.get("status") == "error":
    print(f"⚠️ {result.get('message')}")
else:
    print(f"\n✅ Final decision for {request_id}:")
    print(json.dumps(result.get("result", result), indent=2, ensure_ascii=False))

    decision = result.get("result", {})
    msg = decision.get("message", "No message")
    print(f"\nSummary: {msg}")
