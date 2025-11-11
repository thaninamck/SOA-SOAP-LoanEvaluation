#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilitaires du service composite (simplifié pour exécution synchrone):
- Gestion de la base de données JSON
- Génération d'identifiants avec timestamp
- Notifications par email automatiquement après décision
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration Email --- #
SENDER_EMAIL = "zinebfellati09@gmail.com"      # <-- ton email
SENDER_PASSWORD = "fpgw aynq crqe vpdd"       # <-- mot de passe d'application Gmail
RECIPIENT_EMAIL = "zinebfellati09@gmail.com"  # destinataire par défaut

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Chemins fichiers --- #
DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")
LOG_PATH = os.path.join(os.path.dirname(__file__), "notifications.log")


# --- Base JSON --- #
def ensure_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump({"requests": {}}, f, indent=2, ensure_ascii=False)


def read_db() -> Dict[str, Any]:
    ensure_db()
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
            if "requests" not in db:
                db["requests"] = {}
            return db
    except (json.JSONDecodeError, FileNotFoundError):
        write_db({"requests": {}})
        return {"requests": {}}


def write_db(db: Dict[str, Any]):
    ensure_db()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# --- Lifecycle helpers --- #
def new_request_id(request_text: str) -> str:
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    short_hash = abs(hash(request_text)) % 10000
    return f"REQ_{now}_{short_hash}"


def create_request(request_id: str, text: str):
    db = read_db()
    db["requests"].setdefault(request_id, {})
    db["requests"][request_id].update({
        "text": text,
        "status": "processing",
        "timestamp": datetime.utcnow().isoformat(),
        "last_update": datetime.utcnow().isoformat(),
        "result": None
    })
    write_db(db)


def get_request(request_id: str) -> Dict[str, Any]:
    db = read_db()
    return db.get("requests", {}).get(request_id)


# --- Notifications --- #
def notify(request_id: str, message: str, to_email: str = None):
    """Envoie une notification par email et log. Si to_email non fourni, utilise RECIPIENT_EMAIL."""
    if to_email is None:
        to_email = RECIPIENT_EMAIL

    now = datetime.utcnow().isoformat()
    log_entry = f"{now} | {request_id} | to={to_email} | {message}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)

    request = get_request(request_id) or {}
    status = request.get("status", "unknown")
    request_text = request.get("text", "")

    # Formater la décision proprement
    decision = request.get("result", {})
    if decision:
        # Conserver uniquement les clés importantes ou toute la décision formatée
        result_summary = json.dumps(decision, indent=2, ensure_ascii=False)
    else:
        result_summary = "Aucune décision disponible."

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = f"[{request_id}] Notification de décision"

        body = f"""
{message}

--- Détails de la requête ---
ID Demande : {request_id}
Date : {now}
Statut : {status}
Texte initial :
{request_text}

Décision (résumé) :
{result_summary}
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email envoyé à {to_email}")

    except Exception as e:
        print(f"⚠️ Erreur email: {str(e)} (mais notification loggée)")



# --- Save decision et notification automatique --- #
def save_decision(request_id: str, decision: Dict[str, Any], to_email: str = None):
    db = read_db()
    db["requests"].setdefault(request_id, {})
    db["requests"][request_id].update({
        "result": decision,
        "status": "done",
        "last_update": datetime.utcnow().isoformat()
    })
    write_db(db)

    # Envoi automatique de l'email après décision
    notify(request_id, "La décision finale a été prise pour votre demande.", to_email)
