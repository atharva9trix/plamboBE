from flask import Blueprint, request, jsonify
from src.services.web_service import WebService

web_bp = Blueprint("web", __name__)

@web_bp.route("/web-search", methods=["POST"])
def web_search():
    payload = request.get_json()
    return jsonify(WebService.search(payload))
