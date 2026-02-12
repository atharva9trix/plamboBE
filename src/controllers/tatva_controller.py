import os
from flask import Flask, request, jsonify, Blueprint
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
        user_id = request.args.get("user_id")
        print(user_id)
        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        useer_session_id = tatva_ai.get_user_session_id(user_id)
        return useer_session_id

    except Exception as e:
        return str(e)


@tatvaAI_bp.route('/fetch_attribute/dtype/v1.0', methods=["POST"])
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
    print("file saved success")
    fetch_attribute_dtype = dtype_obj.fetch_attr_dtype(upload_path, user_id, session_id)
    print(fetch_attribute_dtype)
    return jsonify(fetch_attribute_dtype), 200


@tatvaAI_bp.route("/run_query", methods=["POST"])
def run_query_api():
    try:
        userid = request.form.get("userid")
        sessionid = request.form.get("sessionid")
        question = request.form.get("question")
        print(question)
        file_name = request.form.get("file_name")
        # client_id = request.form.get("client_id")
        # print('file',file_name)
        if not (userid and sessionid and question):
            return jsonify({"error": "Missing required parameters"}), 400
        # file_name = f'output_path{client_id}_sales.paraquet'
        print(userid, sessionid, question, file_name)
        result = tatva_ai.query_analysis(userid, sessionid, question, file_name)
        print(result)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tatvaAI_bp.route("/get_insights", methods=["POST"])
def get_insights():
    try:
        payload = request.get_json()
        response_data = payload["response_data"]
        print(response_data)
        result = tatva_ai.get_insights(response_data)
        print('res', result)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tatvaAI_bp.route('/update_col_dtype/v1.0', methods=["POST"])
def update_col_dtype():
    try:
        payload = request.get_json()
        required_params = ["file_name", "id"]
        missing = [p for p in required_params if not payload.get(p)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        file_name = payload.get("file_name")
        rename_col = payload.get("rename_col")
        user_id = payload.get("id")
        update_dtype = payload.get("update_dtype")

        if not file_name:
            return jsonify({"error": "file_name required"}), 400

        result = dtype_obj.updated_col_dtype(file_name=file_name, user_id=user_id, rename_col=rename_col,
                                             update_dtype=update_dtype)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tatvaAI_bp.route('/update_file_attribute/v1.0', methods=["POST"])
def update_attr():
    print("wecolme")
    # file_ = request.files["file"]
    file_ = request.files.get("file")
    print(file_.filename)
    if file_ is None or file_.filename == "":
        return jsonify({"error": "File is missing"}), 400
    data = request.form
    print(data)
    user_id = data["user_id"]
    session_id = data["session_id"]
    if not all(k in data and data[k] for k in ("user_id", "session_id")):
        return jsonify({"error": "Missing fields user_id or session_id"}), 400
    upload_path = os.path.join(base_path, file_.filename)
    print(upload_path)
    file_.save(upload_path)
    print("filesaved success", upload_path)
    fetch_attribute_dtype = dtype_obj.replace_file_attributes(upload_path, user_id, session_id)
    return jsonify(fetch_attribute_dtype), 200
