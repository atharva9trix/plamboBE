from flask import Flask
from flask_cors import CORS
from src.controllers.query_controller import query_bp
from src.controllers.web_controller import web_bp
from src.controllers.health_controller import health_bp
from src.middlewares.error_handler import register_error_handlers
from src.config.settings import API_PREFIX
from src.controllers.tatva_controller import tatvaAI_bp
from src.controllers.generate_controller import generate_bp

app = Flask(__name__)
CORS(app)


app.register_blueprint(query_bp, url_prefix=API_PREFIX)
app.register_blueprint(web_bp, url_prefix=API_PREFIX)
app.register_blueprint(health_bp, url_prefix=API_PREFIX)
app.register_blueprint(tatvaAI_bp, url_prefix=API_PREFIX)
app.register_blueprint(generate_bp, url_prefix=API_PREFIX)


register_error_handlers(app)


if __name__ == "__main__":
    print("digu")
#    app = create_app()
#    app.run(host="0.0.0.0", port=8000, debug=True)
