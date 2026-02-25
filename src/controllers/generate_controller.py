import os
from flask import Flask, request, jsonify, send_from_directory, send_file,Blueprint
from flask_cors import CORS
from pydantic import BaseModel, ValidationError

from src.generator_agent.agent import MediaAgent  # Make sure this exists

#generate = Flask(__name__)
generate_bp = Blueprint("generate", __name__)
#CORS(app)  # Allows all origins (tighten in production)

# ----------------------------
# Ensure Directories Exist
# ----------------------------
IMAGE_DIR = "generated_data/images"
VIDEO_DIR = "generated_data/videos"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

#md_obj=MediaAgent()


# ----------------------------
# Pydantic Request Model
# ----------------------------
class MediaRequest(BaseModel):
    prompt: str
    media_type: str = "image"


# ----------------------------
# Static File Routes
# ----------------------------
@generate_bp.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)


@generate_bp.route("/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename)


# ----------------------------
# Media Generation Endpoint
# ----------------------------
#@generate_bp.route("/generate", methods=["POST"])
#def generate_media():
#    print("hello this is image generator")
#    try:
#        data = request.get_json()
#        print(data)
#
#        # Validate with Pydantic
#        #req = MediaRequest(**data)
#        #return jsonify(req,default=str)
#        md_obj = MediaAgent()
#        result = md_obj.generate(
#            payload=data
#        )
#        print(result,"this is result")
#
#        return jsonify({
#            "success": True,
#            "type": result["type"],
#            "filename": result["filename"],
#            "url": f"/{result['type']}s/{result['filename']}"
#        })
#
#    except ValidationError as ve:
#        return jsonify({"detail": ve.errors()}), 400
#
#    except ValueError as ve:
#        return jsonify({"detail": str(ve)}), 400
#
#    except Exception as e:
#        return jsonify({"detail": str(e)}), 500

@generate_bp.route("/generate", methods=["POST"])
def generate_media():
    print("this is generator")
    try:
        data = request.get_json()
        print("hiii ", data)
        md_obj = MediaAgent()   # <-- THIS was missing in your life
        result = md_obj.generate(data)

#        return jsonify({
#            "success": True,
#            "type": result["type"],
#            "filename": result["filename"],
#            "url": f"/{result['type']}s/{result['filename']}"
#        })
        return send_from_directory(
        result['file_folder'],
        result['filename'],
        as_attachment=False)

    except ValidationError as ve:
        return jsonify({"detail": ve.errors()}), 400

    except ValueError as ve:
        return jsonify({"detail": str(ve)}), 400

    except Exception as e:
        return jsonify({"detail": str(e)}), 500

# ----------------------------
# Run Server
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)