import os
from flask import Flask, request, jsonify,Blueprint
from src.tatvaAI.tatva_ai import TatvaAIMain
from src.config.config import Config
config = Config()
from src.data_description.data_types import DataDescribe


tatvaAI_bp = Blueprint('tatvaAI_route', __name__)
tatva_ai = TatvaAIMain()
dtype_obj = DataDescribe()
# output_path = config.OUTPUT_DATA_PATH
base_path = config.STD_PATH

@tatvaAI_bp.route("/create_session", methods=["GET"])
def create_session():
    try:
        user_id=request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        useer_session_id = tatva_ai.get_user_session_id(user_id)
        return useer_session_id

    except Exception as e:
        return str(e)

@tatvaAI_bp.route('/fetch_attribute/dtype/v1.0',methods=["POST"])
def fetch_attr_dtype():
    file_ = request.files.get("file")
    if file_ is None or file_.filename == "":
        return jsonify({"error": "File is missing"}), 400
    data = request.form
    user_id = data["user_id"]
    session_id = data["session_id"]
    if not all(k in data and data[k] for k in ("user_id", "session_id")):
        return jsonify({"error": "Missing fields user_id or session_id"}), 400
    upload_path = os.path.join(base_path, file_.filename)
    file_.save(upload_path)
    fetch_attribute_dtype = dtype_obj.fetch_attr_dtype(upload_path, user_id, session_id)
    print(fetch_attribute_dtype)
    return jsonify(fetch_attribute_dtype), 200