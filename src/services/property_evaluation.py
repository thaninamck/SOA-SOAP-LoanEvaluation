import sys, logging, json, random
from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted

logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------
# Simulated Data Sources
# ---------------------------------------------------------------------

def get_market_data(region: str):
    """Simule des prix moyens au m² par région."""
    base_prices = {
        "paris": 8500,
        "lyon": 6200,
        "marseille": 4800,
        "toulouse": 4500,
        "lille": 4200,
        "nantes": 4700,
        "bordeaux": 5900,
        "autre": 3500,
    }
    return base_prices.get(region.lower(), base_prices["autre"])


def perform_virtual_inspection(description: str):
    """Analyse la description pour estimer l’état général et la qualité."""
    desc_lower = description.lower()
    condition_score = 1.0

    if any(k in desc_lower for k in ["neuf", "rénové", "modern", "excellent"]):
        condition_score = 1.2
    elif any(k in desc_lower for k in ["ancien", "vieux", "travaux"]):
        condition_score = 0.9
    elif any(k in desc_lower for k in ["délabré", "mauvais état", "usé"]):
        condition_score = 0.7

    # Taille simulée
    if "appartement" in desc_lower:
        size = random.randint(40, 120)
    elif "maison" in desc_lower:
        size = random.randint(80, 250)
    else:
        size = random.randint(60, 150)

    return {
        "condition_score": condition_score,
        "surface_estimee_m2": size
    }


def check_legal_compliance(adresse: str):
    """Simule une vérification de conformité légale."""
    has_litige = random.random() < 0.05  # 5% de chances d’avoir un litige
    conformite = not has_litige
    return {
        "conforme": conformite,
        "litige_en_cours": has_litige,
        "details": "Aucun problème détecté." if conformite else "Litige foncier en cours."
    }


# ---------------------------------------------------------------------
# Property Evaluation Logic
# ---------------------------------------------------------------------

def evaluate_property_value(data: dict) -> (float, dict):
    """Calcule la valeur de la propriété selon des critères simulés."""
    description = data.get("description", "")
    adresse = data.get("adresse", "inconnue")
    region = "autre"
    for city in ["Paris", "Lyon", "Marseille", "Toulouse", "Lille", "Nantes", "Bordeaux"]:
        if city.lower() in adresse.lower():
            region = city.lower()
            break

    market_price = get_market_data(region)
    inspection = perform_virtual_inspection(description)
    legal = check_legal_compliance(adresse)

    # Base value
    base_value = inspection["surface_estimee_m2"] * market_price
    condition_factor = inspection["condition_score"]
    legal_factor = 1.0 if legal["conforme"] else 0.8
    adjustment = random.uniform(0.95, 1.1)

    final_value = base_value * condition_factor * legal_factor * adjustment

    details = {
        "region": region,
        "prix_m2": market_price,
        "surface_estimee_m2": inspection["surface_estimee_m2"],
        "facteur_condition": condition_factor,
        "facteur_conformite": legal_factor,
        "inspection": inspection,
        "legal": legal,
        "adjustment_factor": round(adjustment, 2)
    }

    return round(final_value, 2), details


# ---------------------------------------------------------------------
# Spyne SOAP Service
# ---------------------------------------------------------------------

class PropertyEvaluationService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def evaluate_property(ctx, data):
        """Receives JSON data and returns property value estimation."""
        try:
            parsed = json.loads(data)
        except Exception:
            parsed = {"description": data}

        try:
            value, details = evaluate_property_value(parsed)
            result = {
                "property_value": value,
                "details": details
            }
            logging.info(f"[PropertyEval] Estimated value: {value} € for region {details['region']}")
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[PropertyEval] Error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


# ---------------------------------------------------------------------
# Application SOAP
# ---------------------------------------------------------------------
app = Application(
    [PropertyEvaluationService],
    tns='loan.services.property',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

if __name__ == '__main__':
    sys.exit(run_twisted([(WsgiApplication(app), b'PropertyEvaluationService')], 8003))
