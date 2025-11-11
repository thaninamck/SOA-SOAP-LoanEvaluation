import sys, logging, json, random
from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted

logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------
# Simulated Credit Bureau (could be replaced by a real external service)
# ---------------------------------------------------------------------
def get_credit_bureau_data(nom: str):
    """Simule la récupération des informations d’un bureau de crédit."""
    random.seed(hash(nom) % 10000)
    return {
        "historique_paiement": random.choice(["excellent", "bon", "moyen", "mauvais"]),
        "dettes_en_cours": random.randint(0, 5),
        "retards_paiement": random.randint(0, 3),
        "anciennete_credit": random.randint(1, 20),  # en années
        "score_bureau": random.randint(400, 850)
    }


# ---------------------------------------------------------------------
# Credit Scoring Model
# ---------------------------------------------------------------------
def compute_credit_score(data: dict) -> (float, dict):
    """Calcule un score global de solvabilité entre 0 et 100 et retourne aussi les détails du bureau."""
    revenu = float(data.get("revenu_mensuel", 0))
    depense = float(data.get("depenses_mensuelles", 0))
    montant = float(data.get("montant_pret", 1))
    age = int(data.get("age", 35))
    emploi_stable = data.get("emploi_stable", "oui").lower() == "oui"
    nom = data.get("nom", "")
    prenom = data.get("prenom", "")

    bureau = get_credit_bureau_data(nom)
    score_bureau = bureau["score_bureau"]

    # --- 1. Ratio revenu / dépense ---
    if depense == 0:
        ratio_revenu = 1
    else:
        ratio_revenu = (revenu - depense) / max(revenu, 1)
    ratio_revenu_score = max(0, min(1, ratio_revenu))

    # --- 2. Ratio montant / revenu annuel ---
    ratio_montant = montant / max(revenu * 12, 1)
    ratio_montant_score = max(0, min(1, 1 - ratio_montant))

    # --- 3. Bureau de crédit ---
    bureau_score_norm = (score_bureau - 400) / (850 - 400)
    bureau_score_norm = max(0, min(1, bureau_score_norm))

    # --- 4. Historique ---
    retard_penalty = 1 - min(bureau["retards_paiement"] / 3, 1)
    dettes_penalty = 1 - min(bureau["dettes_en_cours"] / 5, 1)
    historique_score = 0.6 * retard_penalty + 0.4 * dettes_penalty

    # --- 5. Stabilité de l’emploi et âge ---
    emploi_score = 1.0 if emploi_stable else 0.5
    age_score = 1.0 if 25 <= age <= 60 else 0.7

    # --- Pondération globale ajustée ---
    final_score = (
        0.35 * bureau_score_norm +
        0.25 * ratio_revenu_score +
        0.20 * ratio_montant_score +
        0.10 * historique_score +
        0.10 * ((emploi_score + age_score) / 2)
    ) * 100

    # Petit équilibrage : éviter que les scores chutent trop bas
    final_score = min(100, max(0, final_score * 1.05))

    return round(final_score, 2), bureau


# ---------------------------------------------------------------------
# Spyne SOAP Service
# ---------------------------------------------------------------------
class CreditCheckService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def check_credit(ctx, data):
        """Reçoit une chaîne JSON et retourne le score de crédit (0–100)."""
        try:
            parsed = json.loads(data)
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Invalid JSON: {e}"})

        try:
            score, bureau_data = compute_credit_score(parsed)
            result = {
                "credit_score": score,
                "details": {
                    "revenu_mensuel": parsed.get("revenu_mensuel"),
                    "depenses_mensuelles": parsed.get("depenses_mensuelles"),
                    "montant_pret": parsed.get("montant_pret"),
                    "nom": parsed.get("nom"),
                    "prenom": parsed.get("prenom"),
                    "age": parsed.get("age"),
                    "emploi_stable": parsed.get("emploi_stable"),
                    "credit_bureau": bureau_data
                }
            }
            logging.info(f"[CreditCheck] Calculated score: {score} for {parsed.get('nom')}")
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[CreditCheck] Error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


# ---------------------------------------------------------------------
# Application SOAP
# ---------------------------------------------------------------------
app = Application(
    [CreditCheckService],
    tns='loan.services.credit',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

if __name__ == '__main__':
    sys.exit(run_twisted([(WsgiApplication(app), b'CreditCheckService')], 8002))
