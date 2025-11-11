"""
Utilitaires du service composite (simplifié pour exécution synchrone):
- Gestion de la base de données JSON,
- Génération d'identifiants avec timestamp,
- Notifications simulées.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

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
    """Génère un identifiant contenant un timestamp et un court hash."""
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    short_hash = abs(hash(request_text)) % 10000
    return f"REQ_{now}_{short_hash}"


def create_request(request_id: str, text: str):
    """Crée une entrée initiale (status 'done' sera mis après traitement)."""
    db = read_db()
    db["requests"].setdefault(request_id, {})
    db["requests"][request_id].update({
        "text": text,
        "status": "processing",   # on traite immédiatement en synchrone
        "timestamp": datetime.utcnow().isoformat(),
        "last_update": datetime.utcnow().isoformat(),
        "result": None
    })
    write_db(db)


def save_decision(request_id: str, decision: Dict[str, Any]):
    """Enregistre la décision finale et marque 'done'."""
    db = read_db()
    db["requests"].setdefault(request_id, {})
    db["requests"][request_id].update({
        "result": decision,
        "status": "done",
        "last_update": datetime.utcnow().isoformat()
    })
    write_db(db)


def get_request(request_id: str) -> Dict[str, Any]:
    db = read_db()
    return db.get("requests", {}).get(request_id)


# --- Notifications (simple log) --- #
def notify(request_id: str, to_email: str, message: str):
    """Écrit une ligne dans notifications.log (timestamp | id | to=... | message)."""
    now = datetime.utcnow().isoformat()
    entry = f"{now} | {request_id} | to={to_email} | {message}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)
