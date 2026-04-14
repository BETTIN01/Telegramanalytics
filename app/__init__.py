import os
from flask import Flask, g, jsonify, redirect, request, session, url_for
from app.routes.api      import api_bp
from app.routes.views    import views_bp
from app.routes.settings import settings_bp
from app.services import db_service as db

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "painel-hot-local-dev")

    @app.before_request
    def require_dashboard_auth():
        path = request.path or "/"
        public_paths = {
            "/login",
            "/register",
            "/logout",
            "/favicon.ico",
            "/api/auth/me",
            "/api/auth/logout",
        }
        if path.startswith("/static/") or path in public_paths:
            return None
        if path == "/api/finance/pixgo/webhook":
            return None

        user_id = session.get("dashboard_user_id")
        if not user_id:
            if path.startswith("/api/"):
                return jsonify({"ok": False, "msg": "Authentication required."}), 401
            return redirect(url_for("views.login"))

        user = db.get_dashboard_user_by_id(user_id)
        if not user or not int(user.get("is_active") or 0):
            session.clear()
            if path.startswith("/api/"):
                return jsonify({"ok": False, "msg": "Session expired."}), 401
            return redirect(url_for("views.login"))

        g.current_dashboard_user = db.serialize_dashboard_user(user)
        return None

    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(settings_bp)
    return app
