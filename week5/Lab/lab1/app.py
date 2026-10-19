import os
from flask import Flask, jsonify
from config import config_by_name
from models import db
from routes import api_bp
from pagination import PaginationValidationError
from marshmallow import ValidationError


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_obj)

    db.init_app(app)

    # Register Blueprint
    app.register_blueprint(api_bp)

    # Root health/info route
    @app.get("/")
    def index():
        return jsonify({
            "name": "Flask Bookstore API",
            "version": "1.0.0",
            "documentation": "/api/v1/books",
        })

    # Global Error Handlers
    @app.errorhandler(PaginationValidationError)
    def app_pagination_error(error):
        return jsonify({
            "error": error.message,
            "code": error.code,
            "detail": error.message,
        }), error.status_code

    @app.errorhandler(ValidationError)
    def app_validation_error(error):
        return jsonify({
            "error": "Validation failed.",
            "code": "VALIDATION_ERROR",
            "detail": error.messages,
        }), 422

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "code": "NOT_FOUND",
            "detail": "The requested URL or resource was not found.",
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "Method Not Allowed",
            "code": "METHOD_NOT_ALLOWED",
            "detail": "The HTTP method is not allowed on this endpoint.",
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal Server Error",
            "code": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred.",
        }), 500

    return app


if __name__ == "__main__":
    app = create_app("development")
    with app.app_context():
        db.create_all()
        # Seed if empty
        from seed import seed_database
        seed_database()
    app.run(host="127.0.0.1", port=5000, debug=True)
