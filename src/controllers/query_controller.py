from flask import Blueprint, request, jsonify
from src.validators.query_validator import QueryValidator
from src.services.query_service import QueryService
from src.config.settings import CLIENTS
from src.crud_ops.crud_operations import CRUD_Operations

query_bp = Blueprint("query", __name__)
crud_obj = CRUD_Operations()

@query_bp.route("/query", methods=["POST"])
def query():
    payload = request.get_json()
    #{"client_id":{"Id":5,"Client_Name":"Kalahari"},"query":"What are the rules to be followed in park?","conversation_context":""}
    #print(payload)
    cl_id = payload["client_id"]["Client_Name"]
    payload.pop("client_id")
    payload["client_id"] = cl_id
    QueryValidator.validate(payload)
    return jsonify(QueryService.process(payload))
    
@query_bp.route("/clients", methods = ["GET"])
def get_clients():
#    client=  {
#        "clients": list(CLIENTS.keys().title()),
#        "total": len(CLIENTS)
#    }
    client = {
    "clients": [key.title() for key in CLIENTS.keys()],
    "total": len(CLIENTS)
}
    
    return client
    
@query_bp.route("/create", methods = ["POST"])
def create():
    payload = request.get_json()
    level = request.args.get("level")
    #level = "client"
    create_respones = crud_obj.create(payload, level)
    return create_respones
    

@query_bp.route("/get", methods = ["POST"])
def fetch():
    payload = request.get_json()
    level = request.args.get("level")
    fetch_respones = crud_obj.get(payload, level)
    return fetch_respones