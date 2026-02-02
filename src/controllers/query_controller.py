from flask import Blueprint, request, jsonify
from src.validators.query_validator import QueryValidator
from src.services.query_service import QueryService

query_bp = Blueprint("query", __name__)

@query_bp.route("/query", methods=["POST"])
def query():
    payload = request.get_json()
    QueryValidator.validate(payload)
    return jsonify(QueryService.process(payload))
