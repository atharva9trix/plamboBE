from flask import jsonify

def register_error_handlers(app):

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return jsonify({"status": "error", "message": str(error)}), 400

    @app.errorhandler(Exception)
    def handle_exception(error):
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500
