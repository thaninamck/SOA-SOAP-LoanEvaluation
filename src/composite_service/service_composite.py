import sys, logging, json, os
from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted
from suds.client import Client

# Import utilitaires (robuste pour exécution en package ou directe)
try:
    from composite_service.utils import (
        new_request_id, create_request, save_decision, get_request, notify
    )
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(__file__))
    from utils import new_request_id, create_request, save_decision, get_request, notify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# URLs des services enfants (attendus en local)
IE_URL = "http://127.0.0.1:8001/InformationExtractionService?wsdl"
CC_URL = "http://127.0.0.1:8002/CreditCheckService?wsdl"
PE_URL = "http://127.0.0.1:8003/PropertyEvaluationService?wsdl"
DS_URL = "http://127.0.0.1:8004/DecisionService?wsdl"


class LoanEvaluationComposite(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def submitRequest(ctx, request_text):
        """
        Traite synchroniquement la demande entière et retourne la décision finale.
        - Crée request_id
        - Sauvegarde l'enregistrement initial (status=processing)
        - Appelle IE -> CC -> PE -> DS
        - Enregistre la décision, notifie, et retourne la décision + request_id
        """
        try:
            # Générer et créer l'enregistrement
            request_id = new_request_id(request_text)
            create_request(request_id, request_text)
            logging.info(f"[Composite] Start processing request {request_id}")

            # Instancier clients SOAP
            ie = Client(IE_URL)
            cc = Client(CC_URL)
            pe = Client(PE_URL)
            ds = Client(DS_URL)

            # 1) Information Extraction (renvoie JSON string)
            extracted_json = ie.service.extract_information(request_text)
            # parsed sera dict
            parsed = json.loads(extracted_json)
            logging.info(f"[Composite] IE output: {parsed}")

            # 2) Credit Check: envoie JSON string (extracted_json)
            cc_response_json = cc.service.check_credit(extracted_json)
            cc_result = json.loads(cc_response_json)
            logging.info(f"[Composite] CC output: {cc_result}")

            # 3) Property Evaluation: envoie JSON string (extracted_json)
            pe_response_json = pe.service.evaluate_property(extracted_json)
            pe_result = json.loads(pe_response_json)
            logging.info(f"[Composite] PE output: {pe_result}")

            # 4) Decision: construit l'entrée attendue par DecisionService
            decision_input = {
                "credit_score": cc_result.get("credit_score", 0),
                "property_value": pe_result.get("property_value", 0),
                "loan_amount": float(parsed.get("montant_pret", 0)),
                # optional: forward income/expenses for better risk calculation
                "revenu_mensuel": parsed.get("revenu_mensuel", 0),
                "depenses_mensuelles": parsed.get("depenses_mensuelles", 0),
                "emploi_stable": parsed.get("emploi_stable", True),
                # embed raw sub-results for auditing
                "credit_check": cc_result,
                "property_evaluation": pe_result
            }
            decision_json = ds.service.make_decision(json.dumps(decision_input))
            decision = json.loads(decision_json)
            logging.info(f"[Composite] Decision output: {decision}")

            # Enregistrer et notifier
            save_decision(request_id, decision)

            # Message simple pour notification: Approved ou Rejected (use decision["message"] if present)
            notif_msg = decision.get("message", "Result ready")
            notify(request_id, parsed.get("email", "unknown@email.com"), notif_msg)

            # Retour complet synchronique
            return json.dumps({
                "status": "done",
                "request_id": request_id,
                "decision": decision
            }, ensure_ascii=False)

        except Exception as e:
            logging.error(f"[Composite] Error processing request: {e}", exc_info=True)
            # Save minimal error result
            error_result = {
                "approved": False,
                "message": f"Internal error: {str(e)}"
            }
            try:
                # Try to save decision anyway with a request_id if present
                if 'request_id' in locals():
                    save_decision(request_id, error_result)
                    notify(request_id, "unknown", error_result["message"])
            except Exception:
                pass
            return json.dumps({"status": "error", "message": str(e)})

    @rpc(Unicode, _returns=Unicode)
    def getResult(ctx, request_id):
        """Récupère l'enregistrement sauvegardé pour request_id (status + result)."""
        rec = get_request(request_id)
        if not rec:
            return json.dumps({"status": "error", "message": f"No request found for {request_id}"})
        return json.dumps(rec, ensure_ascii=False)


# --- Application SOAP --- #
app = Application(
    [LoanEvaluationComposite],
    tns='loan.composite',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)


if __name__ == '__main__':
    logging.info("[Composite] Running on port 8000")
    sys.exit(run_twisted([(WsgiApplication(app), b'LoanEvaluationService')], 8000))
