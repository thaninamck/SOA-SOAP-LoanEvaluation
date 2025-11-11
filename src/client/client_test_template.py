import json, time
from suds.client import Client

COMPOSITE = "http://127.0.0.1:8000/LoanEvaluationService?wsdl"
client = Client(COMPOSITE)



# Approved
loan_text = """
Nom du Client: Sophie Durand
Adresse: 10 Boulevard Victor Hugo, Montpellier
Email: sophie.durand@email.com
Numéro de Téléphone: +33699112233
Montant du Prêt Demandé: 150000
Revenu Mensuel: 7200
Dépenses Mensuelles: 1800
Description de la Propriété: Appartement moderne de 90m² avec balcon et parking, situé en centre-ville, récemment rénové.
"""

# # Rejected
# loan_text = """
# Nom du Client: Julien Martin
# Adresse: 58 Rue du Lac, Bordeaux
# Email: julien.martin@email.com
# Numéro de Téléphone: +33666778899
# Montant du Prêt Demandé: 400000
# Revenu Mensuel: 5000
# Dépenses Mensuelles: 2500
# Description de la Propriété: Maison ancienne à rénover de 150m² située en périphérie de la ville.
# """

# # Medium
# loan_text = """
# Nom du Client: Alice Dupont
# Adresse: 12 rue des Lilas, Paris
# Email: alice.dupont@email.com
# Numéro de Téléphone: +33678912345
# Montant du Prêt Demandé: 180000
# Revenu Mensuel: 4200
# Dépenses Mensuelles: 1200
# Description de la Propriété: Appartement de 75m² situé dans un quartier calme, proche du centre-ville, bien entretenu.
# """


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
