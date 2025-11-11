import json
import time
from suds.client import Client

# --- CONFIG --- #
COMPOSITE = "http://127.0.0.1:8000/LoanEvaluationService?wsdl"
client = Client(COMPOSITE)

# --- Loan request text --- #
loan_text = """
Nom du Client: Jeanne Petit
Adresse: 5 Rue des Fleurs, Paris
Email: jeanne.petit@email.com
Numéro de Téléphone: +33600111222
Montant du Prêt Demandé: 300000
Revenu Mensuel: 2000
Dépenses Mensuelles: 1500
Description de la Propriété: Petit appartement ancien, nécessite quelques travaux, proche d'une route passante.
"""

# --- 1️⃣ Submit the request --- #
print("📨 Submitting loan request (expected: rejection)...")
response_json = client.service.submitRequest(loan_text)
response = json.loads(response_json)

if response.get("status") != "done":
    print("❌ Error submitting request:", response.get("message"))
    exit()

request_id = response["request_id"]
print(f"✅ Request submitted successfully! ID: {request_id}")

# Note: The service already processed the decision synchronously,
# but we simulate an asynchronous workflow by calling getResult separately.

# --- 2️⃣ Wait (simulate delay if processing was async) --- #
print("\n⏳ Waiting for processing to complete (simulated delay)...")
time.sleep(2)

# --- 3️⃣ Fetch results using getResult --- #
print("\n📥 Fetching result using getResult...")
result_json = client.service.getResult(request_id)
result = json.loads(result_json)

if result.get("status") == "error":
    print(f"⚠️ {result.get('message')}")
else:
    print(f"\n✅ Final decision for {request_id}:")
    print(json.dumps(result.get("result", result), indent=2, ensure_ascii=False))

    # If you want to print only key summary info:
    decision = result.get("result", {})
    msg = decision.get("message", "No message")
    print(f"\nSummary: {msg}")
