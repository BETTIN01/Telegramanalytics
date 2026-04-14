from flask import Blueprint, jsonify, request
from app.services import db_service as db
from app.services import bot_service as bot
import config

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

@settings_bp.get("")
def get_settings():
    token = config.get_token()
    return jsonify({
        "token_set":   bool(token),
        "bot_running": bot.is_running(),
        "groups":      db.get_all_groups(),
        "report_delivery": {
            "smtp_host": db.get_setting("smtp_host", ""),
            "smtp_port": db.get_setting("smtp_port", "587"),
            "smtp_username": db.get_setting("smtp_username", ""),
            "smtp_password_set": bool(db.get_setting("smtp_password", "")),
            "smtp_sender": db.get_setting("smtp_sender", ""),
            "smtp_tls": db.get_setting("smtp_tls", "1"),
        },
    })

@settings_bp.post("/token")
def save_token():
    data  = request.get_json(force=True)
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"ok": False, "msg": "Token vazio."}), 400
    config.set_token(token)
    ok, msg = bot.start_bot(token)
    return jsonify({"ok": ok, "msg": msg})

@settings_bp.post("/bot/restart")
def restart_bot():
    token = config.get_token()
    if not token:
        return jsonify({"ok": False, "msg": "Configure o token primeiro."}), 400
    ok, msg = bot.start_bot(token)
    return jsonify({"ok": ok, "msg": msg})

@settings_bp.post("/bot/stop")
def stop_bot():
    bot.stop_bot()
    return jsonify({"ok": True, "msg": "Bot parado."})

@settings_bp.post("/groups/add")
def add_group():
    data = request.get_json(force=True)
    try:
        chat_id = int(data.get("chat_id", 0))
    except:
        return jsonify({"ok": False, "msg": "chat_id inválido."}), 400
    title = (data.get("title") or "").strip() or f"Grupo {chat_id}"
    db.upsert_group(chat_id, title)
    return jsonify({"ok": True, "msg": f"Grupo \"{title}\" adicionado."})

@settings_bp.delete("/groups/<path:chat_id>")
def remove_group(chat_id):
    try:
        cid = int(chat_id)
    except:
        return jsonify({"ok": False, "msg": "chat_id invalido"}), 400
    db.delete_group(cid)
    return jsonify({"ok": True, "msg": "Grupo removido."})


@settings_bp.post("/report-delivery")
def save_report_delivery():
    data = request.get_json(force=True) or {}
    db.set_setting("smtp_host", (data.get("smtp_host") or "").strip())
    db.set_setting("smtp_port", str(data.get("smtp_port") or "587").strip())
    db.set_setting("smtp_username", (data.get("smtp_username") or "").strip())
    if "smtp_password" in data and str(data.get("smtp_password") or "").strip():
        db.set_setting("smtp_password", str(data.get("smtp_password") or "").strip())
    db.set_setting("smtp_sender", (data.get("smtp_sender") or "").strip())
    db.set_setting("smtp_tls", "1" if str(data.get("smtp_tls", "1")) != "0" else "0")
    return jsonify({"ok": True, "msg": "Entrega de relatorios atualizada."})
