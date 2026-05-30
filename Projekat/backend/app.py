import os

from flask import Flask, jsonify

from audit import configure_audit_logger
from database.db import init_db
from routes.auth import auth_bp
from routes.run import run_bp
from routes.upload import upload_bp


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

    configure_audit_logger()
    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(run_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    host = os.environ.get("OBLAK_HOST", "127.0.0.1")
    port = int(os.environ.get("OBLAK_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
