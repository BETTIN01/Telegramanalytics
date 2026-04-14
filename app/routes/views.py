from pathlib import Path
from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from app.services import db_service as db

views_bp = Blueprint("views", __name__)
_ROOT_DIR = Path(__file__).resolve().parents[1]
_ASSET_REVISION = "20260402-cyberpunk-rail-fix-1"


def _asset_version():
    candidates = [
        _ROOT_DIR / "static" / "js" / "dashboard.js",
        _ROOT_DIR / "static" / "js" / "hot-panel.js",
        _ROOT_DIR / "static" / "css" / "dashboard.css",
        _ROOT_DIR / "static" / "css" / "dashboard-premium.css",
        _ROOT_DIR / "static" / "css" / "dashboard-premium-r20260402.css",
        _ROOT_DIR / "static" / "css" / "hot-panel.css",
        _ROOT_DIR / "templates" / "index.html",
        _ROOT_DIR / "templates" / "login.html",
    ]
    latest = 0
    for path in candidates:
        try:
            latest = max(latest, int(path.stat().st_mtime))
        except OSError:
            continue
    return f"{latest or 1}-{_ASSET_REVISION}"


def _render_login(error="", success="", active_form="login", values=None):
    return render_template(
        "login.html",
        error=error,
        success=success,
        active_form=active_form,
        values=values or {},
        asset_version=_asset_version(),
    )


@views_bp.get("/")
def index():
    user = db.get_dashboard_user_by_id(session.get("dashboard_user_id"))
    if not user:
        return redirect(url_for("views.login"))
    auth_user = db.serialize_dashboard_user(user)
    return render_template("index.html", auth_user=auth_user, asset_version=_asset_version())


@views_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("dashboard_user_id"):
            return redirect(url_for("views.index"))
        return _render_login(active_form="login")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    user = db.authenticate_dashboard_user(username, password)
    if not user:
        return _render_login(
            error="Usuario ou senha invalidos.",
            active_form="login",
            values={"username": username},
        )
    session.clear()
    session["dashboard_user_id"] = user["id"]
    return redirect(url_for("views.index"))


@views_bp.post("/register")
def register():
    abort(404)


@views_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("views.login"))
