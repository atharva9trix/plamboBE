from flask import Flask
from src.controllers.query_controller import query_bp
from src.controllers.web_controller import web_bp
from src.controllers.health_controller import health_bp
from src.middlewares.error_handler import register_error_handlers
from src.config.settings import API_PREFIX
from src.controllers.tatva_controller import tatvaAI_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(query_bp, url_prefix=API_PREFIX)
    app.register_blueprint(web_bp, url_prefix=API_PREFIX)
    app.register_blueprint(health_bp, url_prefix=API_PREFIX)
    app.register_blueprint(tatvaAI_bp, url_prefix=API_PREFIX)

    register_error_handlers(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
