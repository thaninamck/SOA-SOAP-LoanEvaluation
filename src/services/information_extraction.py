import os
import re
import json
import unicodedata
import logging
from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import google.generativeai as genai

from dotenv import load_dotenv
import os
import google.generativeai as genai

# Charger le fichier .env
load_dotenv()

# Lire la clé d'environnement
api_key = os.getenv("GOOGLE_API_KEY")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
genai.configure(api_key=api_key)
def preprocess_text(texte: str) -> str:
    t = unicodedata.normalize("NFKC", texte or "")
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def call_gemini_extract(texte: str) -> dict:
    """
    Demande à Gemini d'extraire les champs en FR et de retourner uniquement un JSON.
    Si Gemini échoue, on retourne None pour utiliser le fallback regex.
    """
    prompt = f"""
Tu es un assistant qui extrait des informations depuis une demande de prêt immobilier rédigée en langage naturel.
Retourne **uniquement** un JSON valide (rien d'autre) avec ces clés exactes en français :
nom, adresse, email, telephone, montant_pret, revenu_mensuel, depenses_mensuelles, description.

Contraintes :
- montant_pret, revenu_mensuel, depenses_mensuelles doivent être des nombres (ex : 150000 ou 1200.5).
- Si une information est absente, mets 0 pour les montants/nombres et une chaîne vide "" pour les textes.
- Ne mets aucun signe monétaire (€, EUR, etc.) dans les champs numériques.

Texte :
\"\"\"{texte}\"\"\"
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text_out = response.text.strip()
        start, end = text_out.find('{'), text_out.rfind('}')
        if start != -1 and end != -1:
            payload = text_out[start:end+1]
            return json.loads(payload)
    except Exception as e:
        logging.warning("Gemini error: %s", e)
    return None

# fallback regex extraction (retourne dict avec mêmes clés)
def fallback_extract(texte: str) -> dict:
    def find(pat):
        m = re.search(pat, texte, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def to_number(s):
        if not s:
            return 0.0
        s2 = re.sub(r"[^\d,.\-]", "", s).replace(",", ".")
        try:
            return float(s2) if s2 else 0.0
        except:
            return 0.0

    return {
        "nom": find(r"(?:Nom du Client|Nom)\s*[:\-]?\s*([A-Za-zÀ-ÖØ-öø-ÿ' \-]+)"),
        "adresse": find(r"(?:Adresse|Adresse du Bien|Adresse)\s*[:\-]?\s*(.*?)(?=\s*(?:Email|Courriel|Montant|$))"),
        "email": find(r"([\w\.-]+@[\w\.-]+\.\w+)"),
        "telephone": find(r"(?:Numéro de Téléphone|Téléphone|Tél)\s*[:\-]?\s*([\d\+\s\-]{6,})"),
        "montant_pret": to_number(find(r"(?:Montant du Prêt Demandé|Montant du Prêt|Montant)\s*[:\-]?\s*([\d\s,\.]+)")),
        "revenu_mensuel": to_number(find(r"(?:Revenu Mensuel|Revenu)\s*[:\-]?\s*([\d\s,\.]+)")),
        "depenses_mensuelles": to_number(find(r"(?:Dépenses Mensuelles|Dépenses)\s*[:\-]?\s*([\d\s,\.]+)")),
        "description": find(r"(?:Description de la Propriété|Description)\s*[:\-]?\s*(.+)")
    }

class InformationExtractionService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def extract_information(ctx, text):
        # entrée libre en langage naturel
        texte = preprocess_text(text)
        logging.info("Received text (snippet): %s", texte[:200])

        # try LLM
        data = call_gemini_extract(texte)
        if not data:
            logging.info("Gemini failed or returned nothing -> fallback regex")
            data = fallback_extract(texte)

        # ensure keys + defaults and types exactly like original service
        defaults = {
            "nom": "Inconnu",
            "adresse": "Non spécifiée",
            "email": "unknown@email.com",
            "telephone": "N/A",
            "montant_pret": 0.0,
            "revenu_mensuel": 0.0,
            "depenses_mensuelles": 0.0,
            "description": "Aucune description fournie"
        }

        normalized = {}
        # numeric cleaning helper
        def to_num(v):
            if v is None or v == "":
                return 0.0
            try:
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v)
                s = re.sub(r"[^\d,.\-]", "", s).replace(",", ".")
                return float(s) if s else 0.0
            except:
                return 0.0

        for k, d in defaults.items():
            if k in ["montant_pret", "revenu_mensuel", "depenses_mensuelles"]:
                normalized[k] = to_num(data.get(k)) if data.get(k) is not None else d
            else:
                val = data.get(k)
                normalized[k] = val if (val is not None and str(val).strip() != "") else d

        # ajout du texte original (court extrait)
        normalized["texte_original"] = texte[:1000]

        # renvoyer JSON (même format que le 1er service)
        result_json = json.dumps(normalized, ensure_ascii=False)
        logging.info("Extraction result: %s", result_json)
        return result_json

# app Spyne
app = Application(
    [InformationExtractionService],
    tns='loan.services.information',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from spyne.server.wsgi import WsgiApplication
    from wsgiref.simple_server import make_server
    wsgi_app = WsgiApplication(app)
    port = 8001
    print(f"Service SOAP en écoute sur http://0.0.0.0:{port}")
    server = make_server("0.0.0.0", port, wsgi_app)
    server.serve_forever()
