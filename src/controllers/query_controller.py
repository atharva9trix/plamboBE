from flask import Blueprint, request, jsonify
from src.validators.query_validator import QueryValidator
from src.services.query_service import QueryService
from src.config.settings import CLIENTS

query_bp = Blueprint("query", __name__)


@query_bp.route("/query", methods=["POST"])
def query():
    payload = request.get_json()
    print(payload)
    QueryValidator.validate(payload)
    return jsonify(QueryService.process(payload))


@query_bp.route("/clients", methods=["GET"])
def get_clients():
    return {
        "clients": list(CLIENTS.keys()),
        "total": len(CLIENTS)
    }
