"""
Nexus AI – Application Entry Point
====================================
Flask app factory with blueprint registration, global error
handlers, and health/test endpoints.

Usage:
    python app.py              (development)
    gunicorn app:app           (production)
"""

import logging
import os

from flask import Flask, jsonify

from config import get_config
from extensions import cors, db, init_mongo, jwt


def create_app(config_class=None):
    """
    Application factory.

    Args:
        config_class: Optional configuration class override.
                      Defaults to the environment-based config.
    """
    app = Flask(__name__)
    app.config.from_object(config_class or get_config())

    # ── Logging ─────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # ── Ensure upload directory exists ──────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Initialise extensions ───────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])
    init_mongo(app)

    # ── Create SQL tables ───────────────────────────────────────
    with app.app_context():
        # Import models so SQLAlchemy registers them
        from models.chat_model import Chat  # noqa: F401
        from models.file_model import File  # noqa: F401
        from models.usage_model import Usage  # noqa: F401
        from models.digital_twin_model import Avatar, VoiceProfile  # noqa: F401

        db.create_all()
        logger.info("Database tables verified / created.")

    # ── Register blueprints ─────────────────────────────────────
    from routes.auth_routes import auth_bp
    from routes.chat_routes import chat_bp
    from routes.upload_routes import upload_bp
    from routes.user_routes import user_bp
    from routes.twin_routes import twin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(twin_bp)

    # ── Health & test endpoints ─────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"success": True, "message": "Backend running"}), 200

    @app.route("/api/test-ai", methods=["GET"])
    def test_ai():
        """Quick smoke test for AI connectivity."""
        from services.ai_service import AIService

        try:
            svc = AIService()
            result = svc.generate_response("Say hello in one sentence.")
            return jsonify({"success": True, "data": result}), 200
        except Exception as exc:
            logger.exception("AI test failed")
            return jsonify({"success": False, "message": str(exc)}), 500

    # ── JWT error handlers ──────────────────────────────────────
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return jsonify({
            "success": False,
            "message": "Missing authorization header."
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({
            "success": False,
            "message": "Invalid or expired token."
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "message": "Token has expired. Please login again."
        }), 401

    # ── Global error handlers ───────────────────────────────────
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "message": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({"success": False, "message": "File too large"}), 413

    @app.errorhandler(500)
    def internal_error(error):
        logger.exception("Internal server error")
        return jsonify({"success": False, "message": "Internal server error"}), 500

    logger.info("=" * 50)
    logger.info("  Nexus AI backend initialised successfully")
    logger.info("  Environment: %s", os.getenv("FLASK_ENV", "development"))
    logger.info("  Database: %s", app.config["SQLALCHEMY_DATABASE_URI"])
    logger.info("  Groq API: %s", "configured" if app.config["GROQ_API_KEY"] else "NOT SET")
    logger.info("  OpenAI API: %s", "configured" if app.config["OPENAI_API_KEY"] else "NOT SET")
    logger.info("=" * 50)

    return app


# ── Module-level app instance for gunicorn / flask run ──────────
app = create_app()

if __name__ == "__main__":
    print("\n>> Starting Nexus AI Backend...")
    print("   -> http://localhost:5000/api/health")
    print("   -> http://localhost:5000/api/test-ai\n")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
