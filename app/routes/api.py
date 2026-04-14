from flask import Blueprint, Response, g, jsonify, request, session, stream_with_context
import csv
import hmac
import hashlib
import io
import json
import queue
import re
import threading
import time as _time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.parse import quote_plus, urlsplit, urlunsplit
import base64
import app.services.db_service        as db
import app.services.analytics_service as an
from app.services import report_service as reporter
from app.services import bot_service as bot
from app.services import pixgo_service as pixgo
from config import PAGE_SIZE

api_bp = Blueprint("api", __name__, url_prefix="/api")
_ngrok_sync_lock = threading.Lock()
_ngrok_last_sync_at = 0.0
_ngrok_last_result = {"synced": 0, "failures": []}
_finance_refresh_lock = threading.Lock()
_finance_refresh_last_run = {}

def get_chat_id(val):
    try:
        return int(val)
    except:
        return None


def current_dashboard_user():
    user = getattr(g, "current_dashboard_user", None)
    if user:
        return user
    user_id = session.get("dashboard_user_id")
    if not user_id:
        return None
    raw = db.get_dashboard_user_by_id(user_id)
    return db.serialize_dashboard_user(raw) if raw else None


def require_admin_user():
    user = current_dashboard_user()
    if not user:
        return None, (jsonify({"ok": False, "msg": "Authentication required."}), 401)
    if user.get("role") != "admin":
        return user, (jsonify({"ok": False, "msg": "Admin access required."}), 403)
    return user, None


def can_manage_user(target_user_id):
    user = current_dashboard_user()
    if not user:
        return False
    return user.get("role") == "admin" or int(user["id"]) == int(target_user_id)


@api_bp.get("/auth/me")
def auth_me():
    user = current_dashboard_user()
    if not user:
        return jsonify({"ok": False, "msg": "Authentication required."}), 401
    return jsonify({
        "ok": True,
        "user": user,
        "preferences": db.get_dashboard_user_preferences(user["id"]),
        "saas": db.get_saas_context_for_user(user["id"]),
    })


@api_bp.post("/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"ok": True})

@api_bp.get("/groups")
def groups():
    return jsonify(db.get_all_groups())


@api_bp.get("/users")
def dashboard_users():
    _, error = require_admin_user()
    if error:
        return error
    return jsonify(db.get_dashboard_users())


@api_bp.post("/users")
def dashboard_user_create():
    _, error = require_admin_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    display_name = (data.get("display_name") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "user").strip().lower()
    try:
        created = db.create_dashboard_user(username, display_name, password=password, role=role)
        return jsonify({"ok": True, "user": created})
    except ValueError as err:
        messages = {
            "username-required": "username required",
            "password-required": "password required",
            "username-exists": "username already exists",
        }
        return jsonify({"ok": False, "msg": messages.get(str(err), str(err))}), 400
    except Exception as err:
        return jsonify({"ok": False, "msg": str(err)}), 400


@api_bp.delete("/users/<int:user_id>")
def dashboard_user_delete(user_id):
    user, error = require_admin_user()
    if error:
        return error
    if int(user["id"]) == int(user_id):
        return jsonify({"ok": False, "msg": "You cannot remove your own admin account while logged in."}), 400
    try:
        db.delete_dashboard_user(user_id)
        return jsonify({"ok": True})
    except ValueError as err:
        messages = {
            "last-user": "Cannot remove the last user.",
            "last-admin": "Cannot remove the last admin.",
        }
        return jsonify({"ok": False, "msg": messages.get(str(err), str(err))}), 400


@api_bp.get("/users/<int:user_id>/preferences")
def dashboard_user_preferences(user_id):
    if not can_manage_user(user_id):
        return jsonify({"ok": False, "msg": "Access denied."}), 403
    return jsonify(db.get_dashboard_user_preferences(user_id))


@api_bp.post("/users/<int:user_id>/preferences")
def dashboard_user_preferences_save(user_id):
    if not can_manage_user(user_id):
        return jsonify({"ok": False, "msg": "Access denied."}), 403
    data = request.get_json(silent=True) or {}
    prefs = db.save_dashboard_user_preferences(
        user_id,
        language=data.get("language"),
        theme_mode=data.get("theme_mode"),
        theme_preset=data.get("theme_preset"),
        avatar_url=data.get("avatar_url"),
        profile_title=data.get("profile_title"),
        profile_bio=data.get("profile_bio"),
        motion_level=data.get("motion_level"),
    )
    return jsonify({"ok": True, "preferences": prefs})


@api_bp.get("/saas/plans")
def saas_plans():
    return jsonify({"ok": True, "plans": db.get_saas_plans(active_only=True)})


@api_bp.get("/saas/context")
def saas_context():
    user = current_dashboard_user()
    if not user:
        return jsonify({"ok": False, "msg": "Authentication required."}), 401
    return jsonify({"ok": True, "context": db.get_saas_context_for_user(user["id"])})


@api_bp.get("/saas/admin/overview")
def saas_admin_overview():
    _, error = require_admin_user()
    if error:
        return error
    return jsonify({"ok": True, "overview": db.get_saas_admin_overview(), "plans": db.get_saas_plans(active_only=False)})


@api_bp.post("/saas/admin/subscription")
def saas_admin_subscription_update():
    _, error = require_admin_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    organization_id = int(data.get("organization_id") or 1)
    plan_code = (data.get("plan_code") or "").strip().lower()
    billing_cycle = (data.get("billing_cycle") or "monthly").strip().lower()
    status = (data.get("status") or "active").strip().lower()
    try:
        subscription = db.update_organization_subscription(
            organization_id,
            plan_code,
            billing_cycle=billing_cycle,
            status=status,
            seats=data.get("seats"),
        )
        return jsonify({"ok": True, "subscription": subscription})
    except ValueError as err:
        return jsonify({"ok": False, "msg": str(err)}), 400

@api_bp.get("/stats/<path:chat_id>")
def stats(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    s  = db.get_summary(cid)
    tj = s.get("total_joins",  0) or 0
    tl = s.get("total_leaves", 0) or 0
    return jsonify({**s, "net_growth": tj - tl, "churn_rate": an.churn_rate(tj, tl)})

@api_bp.get("/timeseries/<path:chat_id>")
def timeseries(chat_id):
    cid    = get_chat_id(chat_id)
    ts     = db.get_timeseries(cid)
    joins  = [r["joins"]  for r in ts]
    leaves = [r["leaves"] for r in ts]
    return jsonify({
        "labels":      [r["day"] for r in ts],
        "joins":       joins,
        "leaves":      leaves,
        "net_members": an.net_series(ts),
        "joins_ma7":   an.moving_avg(joins,  7),
        "leaves_ma7":  an.moving_avg(leaves, 7),
    })

@api_bp.get("/events/<path:chat_id>")
def events(chat_id):
    cid         = get_chat_id(chat_id)
    page        = max(1, request.args.get("page", 1, type=int))
    rows, total = db.get_events_page(cid, page, PAGE_SIZE)
    return jsonify({
        "events":      rows,
        "page":        page,
        "total":       total,
        "total_pages": max(1, -(-total // PAGE_SIZE)),
    })

@api_bp.get("/reports/<path:chat_id>")
def reports(chat_id):
    cid = get_chat_id(chat_id)
    s   = db.get_summary(cid)
    ts  = db.get_timeseries(cid)
    hr  = db.get_hourly(cid)
    wd  = db.get_weekday(cid)
    tj  = s.get("total_joins",  0) or 0
    tl  = s.get("total_leaves", 0) or 0
    return jsonify({
        "summary":      {**s, "net_growth": tj - tl, "churn_rate": an.churn_rate(tj, tl)},
        "weekly":       an.weekly_stats(ts)[-8:],
        "monthly":      an.monthly_stats(ts)[-6:],
        "peak_hour":    an.peak_hour(hr),
        "peak_weekday": an.peak_weekday(wd),
        "spikes":       an.detect_spikes(ts),
        "drops":        an.detect_drops(ts),
        "insights":     an.generate_insights(ts, hr, wd, s),
    })

@api_bp.get("/recent/<path:chat_id>")
def recent(chat_id):
    cid = get_chat_id(chat_id)
    return jsonify(db.get_recent(cid, limit=10))

@api_bp.get("/members/<path:chat_id>")
def members(chat_id):
    cid = get_chat_id(chat_id)
    return jsonify({
        "members": db.get_members(cid),
        "count":   db.get_member_count(cid),
    })

@api_bp.post("/members/<path:chat_id>/sync")
def sync_members(chat_id):
    cid = get_chat_id(chat_id)
    ok, msg = bot.sync_members_sync(cid)
    return jsonify({"ok": ok, "msg": msg})
@api_bp.post("/members/<path:chat_id>/sync-full")
def sync_members_full(chat_id):
    cid = get_chat_id(chat_id)
    from app.services.telethon_service import sync_all_members
    ok, msg = sync_all_members(cid)
    return jsonify({"ok": ok, "msg": msg})

# ── COFRE ──────────────────────────────────────────────────
import json as _json
from app.services.db_service import _c as _db

@api_bp.get("/vault/categories")
def vault_categories():
    c = _db()
    rows = c.execute("SELECT * FROM vault_categories ORDER BY name").fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])

@api_bp.post("/vault/categories")
def vault_category_create():
    d = request.json
    c = _db()
    c.execute("INSERT INTO vault_categories (name,icon,color) VALUES (?,?,?)",
              (d.get("name"), d.get("icon",""), d.get("color","#58a6ff")))
    c.commit(); c.close()
    return jsonify({"ok": True})

@api_bp.delete("/vault/categories/<int:cat_id>")
def vault_category_delete(cat_id):
    c = _db()
    c.execute("DELETE FROM vault_entries    WHERE category_id=?", (cat_id,))
    c.execute("DELETE FROM vault_categories WHERE id=?",          (cat_id,))
    c.commit(); c.close()
    return jsonify({"ok": True})

@api_bp.get("/vault/entries/<int:cat_id>")
def vault_entries(cat_id):
    c = _db()
    rows = c.execute("SELECT * FROM vault_entries WHERE category_id=? ORDER BY title", (cat_id,)).fetchall()
    c.close()
    result = []
    for r in rows:
        r = dict(r)
        try:    r["fields"] = _json.loads(r.get("fields") or "[]")
        except: r["fields"] = []
        result.append(r)
    return jsonify(result)

@api_bp.post("/vault/entries")
def vault_entry_create():
    d = request.json
    c = _db()
    c.execute("INSERT INTO vault_entries (category_id,title,fields,notes) VALUES (?,?,?,?)",
              (d.get("category_id"), d.get("title"), _json.dumps(d.get("fields",[])), d.get("notes","")))
    c.commit(); c.close()
    return jsonify({"ok": True})

@api_bp.put("/vault/entries/<int:entry_id>")
def vault_entry_update(entry_id):
    d = request.json
    c = _db()
    c.execute("UPDATE vault_entries SET title=?,fields=?,notes=? WHERE id=?",
              (d.get("title"), _json.dumps(d.get("fields",[])), d.get("notes",""), entry_id))
    c.commit(); c.close()
    return jsonify({"ok": True})

@api_bp.delete("/vault/entries/<int:entry_id>")
def vault_entry_delete(entry_id):
    c = _db()
    c.execute("DELETE FROM vault_entries WHERE id=?", (entry_id,))
    c.commit(); c.close()
    return jsonify({"ok": True})

# SSE broadcast queue
_alert_queues = []
_alert_lock   = threading.Lock()

def _group_label(chat_id):
    for group in db.get_all_groups():
        try:
            if int(group.get("chat_id")) == int(chat_id):
                return group.get("chat_title") or str(chat_id)
        except Exception:
            continue
    return str(chat_id)

def _default_finance_chat_id():
    groups = db.get_all_groups()
    if len(groups) == 1:
        return get_chat_id(groups[0].get("chat_id"))
    chat_ids = []
    for row in db.get_finance_transactions(limit=400):
        cid = row.get("chat_id")
        if cid not in (None, ""):
            chat_ids.append(get_chat_id(cid))
    unique = [cid for cid in sorted(set(chat_ids)) if cid is not None]
    return unique[0] if len(unique) == 1 else None

def _slugify(value):
    value = re.sub(r"[^A-Za-z0-9]+", "-", (value or "")).strip("-").lower()
    return value or "grupo"

def _export_filename(chat_id, ext):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    group = _slugify(_group_label(chat_id))
    return f"tg-analytics_{group}_{chat_id}_{stamp}.{ext}"

def _mask_secret(value):
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:4]}{'*' * max(4, len(value) - 6)}{value[-2:]}"

def _digits(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())

def _normalize_webhook_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except Exception:
        return value
    if not parsed.scheme or not parsed.netloc:
        return value
    path = parsed.path or ""
    if path in {"", "/"}:
        host = (parsed.netloc or "").lower()
        path = "/webhook/pixgo" if "ngrok" in host else "/api/finance/pixgo/webhook"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))

def _pixgo_accounts_from_settings():
    raw = db.get_setting("pixgo_accounts", "").strip()
    accounts = []
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                accounts = [item for item in parsed if isinstance(item, dict)]
        except Exception:
            accounts = []

    if accounts:
        normalized = []
        for idx, item in enumerate(accounts, start=1):
            account_id = (item.get("id") or f"account_{idx}").strip()
            normalized.append({
                "id": account_id,
                "name": (item.get("name") or account_id).strip(),
                "api_key": (item.get("api_key") or "").strip(),
                "webhook_secret": (item.get("webhook_secret") or "").strip(),
                "webhook_url": _normalize_webhook_url(item.get("webhook_url") or ""),
                "default_description": (item.get("default_description") or "").strip(),
                "is_default": bool(item.get("is_default")),
            })
        preferred_name = db.get_setting("pixgo_default_description", "").strip().lower()
        matching_preferred = next((item for item in normalized if str(item.get("name") or "").strip().lower() == preferred_name), None)
        current_default = next((item for item in normalized if item.get("is_default")), None)
        if matching_preferred and current_default and current_default.get("id") != matching_preferred.get("id"):
            for item in normalized:
                item["is_default"] = item.get("id") == matching_preferred.get("id")
        elif normalized and not any(item["is_default"] for item in normalized):
            normalized[0]["is_default"] = True
        return normalized

    legacy_api_key = db.get_setting("pixgo_api_key", "").strip()
    legacy_secret = db.get_setting("pixgo_webhook_secret", "").strip()
    if not legacy_api_key and not legacy_secret:
        return []
    return [{
        "id": "default",
        "name": "PIXGO",
        "api_key": legacy_api_key,
        "webhook_secret": legacy_secret,
        "webhook_url": _normalize_webhook_url(db.get_setting("pixgo_webhook_url", "")),
        "default_description": db.get_setting("pixgo_default_description", "Cobranca TG Analytics"),
        "is_default": True,
    }]

def _save_pixgo_accounts(accounts):
    cleaned = []
    for idx, item in enumerate(accounts or [], start=1):
        if not isinstance(item, dict):
            continue
        account_id = (item.get("id") or f"account_{idx}").strip()
        api_key = (item.get("api_key") or "").strip()
        webhook_secret = (item.get("webhook_secret") or "").strip()
        webhook_url = _normalize_webhook_url(item.get("webhook_url") or "")
        if not api_key and not webhook_secret:
            continue
        cleaned.append({
            "id": account_id,
            "name": (item.get("name") or account_id).strip(),
            "api_key": api_key,
            "webhook_secret": webhook_secret,
            "webhook_url": webhook_url,
            "default_description": (item.get("default_description") or db.get_setting("pixgo_default_description", "Cobranca TG Analytics")).strip(),
            "is_default": bool(item.get("is_default")),
        })
    if cleaned and not any(item["is_default"] for item in cleaned):
        cleaned[0]["is_default"] = True
    db.set_setting("pixgo_accounts", json.dumps(cleaned, ensure_ascii=False))
    if cleaned:
        primary = next((item for item in cleaned if item.get("is_default")), cleaned[0])
        db.set_setting("pixgo_api_key", primary.get("api_key", ""))
        db.set_setting("pixgo_webhook_secret", primary.get("webhook_secret", ""))
        db.set_setting("pixgo_webhook_url", primary.get("webhook_url", ""))
        db.set_setting("pixgo_default_description", primary.get("default_description", ""))
    return cleaned

def _get_default_pixgo_account():
    accounts = _pixgo_accounts_from_settings()
    if not accounts:
        return None
    return next((item for item in accounts if item.get("is_default")), accounts[0])

def _find_pixgo_account(account_ref=None):
    accounts = _pixgo_accounts_from_settings()
    if not accounts:
        return None
    ref = str(account_ref or "").strip().lower()
    if ref:
        for item in accounts:
            if str(item.get("id") or "").strip().lower() == ref:
                return item
            if str(item.get("name") or "").strip().lower() == ref:
                return item
    return _get_default_pixgo_account()

def _first_value(data, *paths):
    for path in paths:
        cur = data
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok and cur not in (None, "", []):
            return cur
    return None

def _normalize_datetime_value(value):
    value = str(value or "").strip()
    if not value:
        return None
    value = value.replace("T", " ")
    if value.endswith("Z"):
        value = value[:-1].strip()
    return value or None

def _parse_json_object(value):
    if isinstance(value, dict):
        return value
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None

def _merge_pixgo_payloads(*payloads):
    merged = {}
    merged_data = {}
    merged_payment = {}
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if key in {"data", "payment"} and isinstance(value, dict):
                continue
            merged[key] = value
        if isinstance(payload.get("data"), dict):
            merged_data.update(payload.get("data") or {})
        if isinstance(payload.get("payment"), dict):
            merged_payment.update(payload.get("payment") or {})
    if merged_data:
        merged["data"] = merged_data
    if merged_payment:
        merged["payment"] = merged_payment
    return merged

def _extract_pixgo_timestamps(data, existing=None):
    existing = existing or {}
    candidates = []

    if isinstance(data, dict):
        candidates.append(data)
        nested_data = data.get("data")
        if isinstance(nested_data, dict):
            candidates.append(nested_data)
        payment_data = data.get("payment")
        if isinstance(payment_data, dict):
            candidates.append(payment_data)
        raw_json = _parse_json_object(data.get("raw_json"))
        if raw_json:
            candidates.append(raw_json)
            raw_nested = raw_json.get("data")
            if isinstance(raw_nested, dict):
                candidates.append(raw_nested)
            raw_payment = raw_json.get("payment")
            if isinstance(raw_payment, dict):
                candidates.append(raw_payment)

    created_at = None
    updated_at = None
    completed_at = None

    for item in candidates:
        if not created_at:
            created_at = _normalize_datetime_value(_first_value(
                item,
                ("created_at",),
                ("date_created",),
                ("payment_date",),
            ))
        if not updated_at:
            updated_at = _normalize_datetime_value(_first_value(
                item,
                ("updated_at",),
                ("last_update",),
            ))
        if not completed_at:
            completed_at = _normalize_datetime_value(_first_value(
                item,
                ("completed_at",),
                ("paid_at",),
                ("approved_at",),
            ))

    created_at = created_at or existing.get("created_at")
    updated_at = updated_at or existing.get("updated_at") or created_at
    completed_at = completed_at or existing.get("completed_at")
    return {
        "created_at": created_at,
        "updated_at": updated_at,
        "completed_at": completed_at,
    }

def _coerce_amount(value):
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("R$", "").replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        return float(text)
    except Exception:
        return 0.0

def _rows_from_import_payload(parsed):
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        for key in ("payments", "transactions", "data", "items", "results"):
            value = parsed.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if any(key in parsed for key in ("payment_id", "deposit_id", "id", "external_id", "status", "amount")):
            return [parsed]
    return []

def _parse_import_text(content, filename=""):
    text = (content or "").strip()
    if not text:
        raise ValueError("Arquivo ou conteudo vazio.")

    lowered = (filename or "").lower()
    if lowered.endswith(".json") or text.startswith("[") or text.startswith("{"):
        parsed = json.loads(text)
        rows = _rows_from_import_payload(parsed)
        if not rows:
            raise ValueError("JSON sem transacoes reconheciveis.")
        return rows

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("CSV vazio.")
    sample = "\n".join(lines[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
    except Exception:
        dialect = csv.excel
        dialect.delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = [dict(row) for row in reader if row]
    if not rows:
        raise ValueError("CSV sem linhas validas.")
    return rows

def _import_row_to_transaction(row, default_chat_id=None, default_account=""):
    existing = row if isinstance(row, dict) else {}
    payment_id = _first_value(
        existing,
        ("payment_id",),
        ("deposit_id",),
        ("id",),
        ("codigo",),
        ("transaction_id",),
    )
    if not payment_id:
        raise ValueError("Linha sem payment_id.")

    amount = _coerce_amount(_first_value(
        existing,
        ("amount",),
        ("valor",),
        ("value",),
        ("total",),
    ))

    chat_id = _first_value(existing, ("chat_id",), ("group_id",), ("grupo_id",))
    chat_id = get_chat_id(chat_id) if chat_id not in (None, "") else default_chat_id

    status = str(_first_value(
        existing,
        ("status",),
        ("payment_status",),
        ("situacao",),
        ("state",),
    ) or "pending").strip().lower()

    created_at = _normalize_datetime_value(_first_value(
        existing,
        ("created_at",),
        ("createdAt",),
        ("date_created",),
        ("data_criacao",),
    ))
    updated_at = _normalize_datetime_value(_first_value(
        existing,
        ("updated_at",),
        ("updatedAt",),
        ("last_update",),
        ("data_atualizacao",),
    )) or created_at
    completed_at = _normalize_datetime_value(_first_value(
        existing,
        ("completed_at",),
        ("paid_at",),
        ("approved_at",),
        ("data_pagamento",),
    ))
    expires_at = _normalize_datetime_value(_first_value(
        existing,
        ("expires_at",),
        ("expiration_date",),
        ("expira_em",),
    ))

    payload_json = existing.get("payload_json")
    if not payload_json:
        payload_json = json.dumps(existing, ensure_ascii=False)

    return {
        "chat_id": chat_id,
        "provider": "pixgo",
        "provider_account": str(_first_value(existing, ("provider_account",), ("account",), ("conta",), ("gateway_account",)) or default_account or ""),
        "payment_id": str(payment_id),
        "external_id": str(_first_value(existing, ("external_id",), ("reference",), ("pedido",), ("order_id",)) or ""),
        "amount": amount,
        "status": status,
        "description": str(_first_value(existing, ("description",), ("descricao",), ("title",), ("plan_name",)) or ""),
        "customer_name": str(_first_value(existing, ("customer_name",), ("payer_name",), ("receiver_name",), ("cliente",), ("name",)) or ""),
        "customer_cpf": _digits(_first_value(existing, ("customer_cpf",), ("payer_cpf",), ("cpf",), ("document",)) or ""),
        "customer_email": str(_first_value(existing, ("customer_email",), ("payer_email",), ("receiver_email",), ("email",)) or ""),
        "customer_phone": _digits(_first_value(existing, ("customer_phone",), ("payer_phone",), ("phone",), ("telefone",)) or ""),
        "qr_code": str(_first_value(existing, ("qr_code",), ("pix_code",), ("pix_copia_cola",), ("copy_paste",)) or ""),
        "qr_image_url": str(_first_value(existing, ("qr_image_url",), ("image_url",), ("qr_image",)) or ""),
        "checkout_id": str(_first_value(existing, ("checkout_id",), ("checkout",)) or ""),
        "payload_json": payload_json,
        "expires_at": expires_at,
        "completed_at": completed_at,
        "created_at": created_at,
        "updated_at": updated_at,
    }

def _finance_is_paid(status):
    return str(status or "").strip().lower() in {"paid", "approved", "completed", "success", "succeeded"}

def _finance_is_pending(status):
    return str(status or "").strip().lower() in {"pending", "created", "processing", "waiting_payment", "waiting", "open"}

def _finance_is_expired(status):
    return str(status or "").strip().lower() in {"expired", "cancelled", "canceled", "failed", "refused", "voided"}

def _finance_settings_payload():
    accounts = _pixgo_accounts_from_settings()
    primary = _get_default_pixgo_account()
    api_key = (primary or {}).get("api_key") or db.get_setting("pixgo_api_key", "")
    webhook_secret = (primary or {}).get("webhook_secret") or db.get_setting("pixgo_webhook_secret", "")
    return {
        "provider": "pixgo",
        "api_key_set": bool(api_key),
        "api_key_preview": _mask_secret(api_key),
        "webhook_secret_set": bool(webhook_secret),
        "webhook_secret_preview": _mask_secret(webhook_secret),
        "webhook_url": _normalize_webhook_url((primary or {}).get("webhook_url") or db.get_setting("pixgo_webhook_url", "")),
        "default_description": (primary or {}).get("default_description") or db.get_setting("pixgo_default_description", "Cobranca TG Analytics"),
        "accounts": [{
            "id": item.get("id"),
            "name": item.get("name"),
            "is_default": bool(item.get("is_default")),
            "api_key_set": bool(item.get("api_key")),
            "api_key_preview": _mask_secret(item.get("api_key")),
            "webhook_secret_set": bool(item.get("webhook_secret")),
            "webhook_secret_preview": _mask_secret(item.get("webhook_secret")),
            "webhook_url": item.get("webhook_url") or "",
        } for item in accounts],
    }

def _finance_response_to_record(chat_id, data, submitted=None, existing=None):
    submitted = submitted or {}
    existing = existing or {}
    timestamps = _extract_pixgo_timestamps(data, existing)
    payment_id = _first_value(
        data,
        ("payment_id",),
        ("deposit_id",),
        ("id",),
        ("payment", "payment_id"),
        ("payment", "deposit_id"),
        ("payment", "id"),
        ("data", "payment_id"),
        ("data", "deposit_id"),
        ("data", "id"),
    ) or existing.get("payment_id")
    if not payment_id:
        raise pixgo.PixGoError("A resposta da PIXGO nao retornou payment_id.", 502)

    status = str(_first_value(
        data,
        ("status",),
        ("payment_status",),
        ("payment", "status"),
        ("data", "status"),
    ) or existing.get("status") or "pending").strip().lower()

    raw_amount = _first_value(
        data,
        ("amount",),
        ("payment", "amount"),
        ("data", "amount"),
        ("value",),
    )
    try:
        amount = float(raw_amount if raw_amount is not None else submitted.get("amount") or existing.get("amount") or 0)
    except Exception:
        amount = 0.0

    description = _first_value(
        data,
        ("description",),
        ("plan_name",),
        ("payment", "description"),
        ("payment", "plan_name"),
        ("data", "description"),
        ("data", "plan_name"),
    ) or submitted.get("description") or existing.get("description") or ""

    customer_name = _first_value(
        data,
        ("customer_name",),
        ("payer_name",),
        ("receiver_name",),
        ("customer", "name"),
        ("payment", "customer_name"),
        ("payment", "receiver_name"),
        ("data", "customer_name"),
        ("data", "payer_name"),
        ("data", "receiver_name"),
    ) or submitted.get("customer_name") or existing.get("customer_name") or ""

    customer_cpf = _digits(_first_value(
        data,
        ("customer_cpf",),
        ("payer_cpf",),
        ("customer", "cpf"),
        ("payment", "customer_cpf"),
        ("data", "customer_cpf"),
        ("data", "payer_cpf"),
    ) or submitted.get("customer_cpf") or existing.get("customer_cpf") or "")

    customer_email = _first_value(
        data,
        ("customer_email",),
        ("payer_email",),
        ("receiver_email",),
        ("customer", "email"),
        ("payment", "customer_email"),
        ("payment", "receiver_email"),
        ("data", "customer_email"),
        ("data", "payer_email"),
        ("data", "receiver_email"),
    ) or submitted.get("customer_email") or existing.get("customer_email") or ""

    customer_phone = _digits(_first_value(
        data,
        ("customer_phone",),
        ("payer_phone",),
        ("customer", "phone"),
        ("payment", "customer_phone"),
        ("data", "customer_phone"),
        ("data", "payer_phone"),
    ) or submitted.get("customer_phone") or existing.get("customer_phone") or "")

    qr_code = _first_value(
        data,
        ("qr_code",),
        ("pix_code",),
        ("copy_paste",),
        ("pix_copia_cola",),
        ("payment", "qr_code"),
        ("payment", "pix_code"),
        ("data", "qr_code"),
        ("data", "pix_code"),
    ) or existing.get("qr_code") or ""

    qr_image_url = _first_value(
        data,
        ("qr_image_url",),
        ("image_url",),
        ("payment", "qr_image_url"),
        ("data", "qr_image_url"),
        ("data", "image_url"),
    ) or existing.get("qr_image_url") or ""

    checkout_id = _first_value(
        data,
        ("checkout_id",),
        ("payment", "checkout_id"),
        ("data", "checkout_id"),
    ) or existing.get("checkout_id") or ""

    external_id = _first_value(
        data,
        ("external_id",),
        ("reference",),
        ("payment", "external_id"),
        ("payment", "reference"),
        ("data", "external_id"),
        ("data", "reference"),
    ) or submitted.get("external_id") or existing.get("external_id") or ""

    expires_at = _first_value(
        data,
        ("expires_at",),
        ("payment", "expires_at"),
        ("data", "expires_at"),
        ("expiration_date",),
    ) or existing.get("expires_at")

    completed_at = timestamps.get("completed_at")
    received_completed_at = _first_value(
        data,
        ("completed_at",),
        ("data", "completed_at"),
    )
    if received_completed_at:
        completed_at = _normalize_datetime_value(received_completed_at)
    if _finance_is_paid(status) and not completed_at:
        completed_at = timestamps.get("updated_at") or timestamps.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "chat_id": chat_id if chat_id is not None else existing.get("chat_id"),
        "provider": "pixgo",
        "provider_account": submitted.get("provider_account") or existing.get("provider_account") or "",
        "payment_id": str(payment_id),
        "external_id": str(external_id),
        "amount": amount,
        "status": status,
        "description": description,
        "customer_name": customer_name,
        "customer_cpf": customer_cpf,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "qr_code": qr_code,
        "qr_image_url": qr_image_url,
        "checkout_id": str(checkout_id),
        "payload_json": json.dumps(data or {}, ensure_ascii=False),
        "expires_at": expires_at,
        "completed_at": completed_at,
        "created_at": timestamps.get("created_at"),
        "updated_at": timestamps.get("updated_at"),
    }

def _finance_summary(rows):
    completed_rows = [row for row in rows if _finance_is_paid(row.get("status"))]
    pending_rows = [row for row in rows if _finance_is_pending(row.get("status"))]
    expired_rows = [row for row in rows if _finance_is_expired(row.get("status"))]
    total_count = len(rows)
    completed_count = len(completed_rows)
    conversion_rate = round((completed_count / total_count) * 100, 1) if total_count else 0
    return {
        "total_count": total_count,
        "completed_count": completed_count,
        "pending_count": len(pending_rows),
        "expired_count": len(expired_rows),
        "completed_amount": round(sum(float(row.get("amount") or 0) for row in completed_rows), 2),
        "pending_amount": round(sum(float(row.get("amount") or 0) for row in pending_rows), 2),
        "conversion_rate": conversion_rate,
    }

def _ingest_pixgo_payload(payload, account=None, confirm_details=True):
    if not isinstance(payload, dict):
        return None
    payment_id = _first_value(
        payload,
        ("payment_id",),
        ("deposit_id",),
        ("id",),
        ("payment", "payment_id"),
        ("payment", "deposit_id"),
        ("data", "payment_id"),
        ("data", "deposit_id"),
        ("data", "id"),
    )
    if not payment_id:
        return None

    payment_id = str(payment_id)
    existing = db.get_finance_transaction(payment_id) or {}
    confirmed = payload
    target_account = account or _get_default_pixgo_account()
    api_key = ((target_account or {}).get("api_key") or db.get_setting("pixgo_api_key", "")).strip()

    if api_key and confirm_details:
        try:
            details = pixgo.get_payment_details(api_key, payment_id)
            status = pixgo.get_payment_status(api_key, payment_id)
            merged = _merge_pixgo_payloads(details, status)
            if merged:
                if isinstance(payload.get("data"), dict):
                    combined = dict(payload)
                    combined_data = dict(payload.get("data") or {})
                    combined_data.update(merged.get("data") or {})
                    combined["data"] = combined_data
                    for key, value in merged.items():
                        if key != "data":
                            combined[key] = value
                    confirmed = combined
                else:
                    merged.setdefault("raw_json", json.dumps(payload, ensure_ascii=False))
                    confirmed = merged
        except pixgo.PixGoError:
            confirmed = payload

    target_chat_id = existing.get("chat_id")
    if target_chat_id in (None, ""):
        target_chat_id = _default_finance_chat_id()

    record = _finance_response_to_record(
        target_chat_id,
        confirmed,
        {"provider_account": (target_account or {}).get("name", "")},
        existing,
    )
    return db.upsert_finance_transaction(record)

def _decode_ngrok_raw_request(raw_value):
    if not raw_value:
        return "", {}
    try:
        raw_bytes = base64.b64decode(raw_value)
    except Exception:
        return "", {}
    try:
        raw_text = raw_bytes.decode("utf-8")
    except Exception:
        raw_text = raw_bytes.decode("latin-1", errors="ignore")
    header_text, _, body_text = raw_text.partition("\r\n\r\n")
    if not body_text and "\n\n" in raw_text:
        header_text, _, body_text = raw_text.partition("\n\n")
    headers = {}
    for line in header_text.splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return body_text.strip(), headers

def _sync_pixgo_from_ngrok(limit=50):
    synced = 0
    failures = []
    seen_ids = set()
    try:
        with urlopen(f"http://127.0.0.1:4040/api/requests/http?limit={int(limit)}", timeout=5) as resp:
            data = json.load(resp)
    except Exception as err:
        return 0, [{"msg": f"ngrok inspector indisponivel: {err}"}]

    requests_list = data.get("requests") or []
    for item in reversed(requests_list):
        req = item.get("request") or {}
        req_id = str(item.get("id") or "")
        if req_id and req_id in seen_ids:
            continue
        seen_ids.add(req_id)
        if req.get("method") != "POST":
            continue
        uri = str(req.get("uri") or "")
        if "/webhook/pixgo" not in uri and "/api/finance/pixgo/webhook" not in uri:
            continue
        body_text, headers = _decode_ngrok_raw_request(req.get("raw"))
        if not body_text:
            continue
        try:
            payload = json.loads(body_text)
        except Exception:
            continue
        payment_id = _first_value(
            payload,
            ("payment_id",),
            ("deposit_id",),
            ("data", "payment_id"),
            ("data", "deposit_id"),
        )
        if not payment_id:
            continue
        existing = db.get_finance_transaction(str(payment_id))
        existing_payload = {}
        if existing and existing.get("payload_json"):
            try:
                existing_payload = json.loads(existing.get("payload_json") or "{}")
            except Exception:
                existing_payload = {}
        # Avoid useless rewrites when the same webhook was already persisted.
        if existing_payload == payload:
            continue
        try:
            account = _find_pixgo_account(existing.get("provider_account") if existing else None)
            _ingest_pixgo_payload(payload, account=account, confirm_details=False)
            synced += 1
        except Exception as err:
            failures.append({"payment_id": str(payment_id), "msg": str(err)})
    return synced, failures[:8]

def _maybe_sync_pixgo_from_ngrok(limit=50, min_interval=6):
    global _ngrok_last_sync_at, _ngrok_last_result
    now = _time.time()
    if now - _ngrok_last_sync_at < float(min_interval):
        return _ngrok_last_result
    if not _ngrok_sync_lock.acquire(blocking=False):
        return _ngrok_last_result
    try:
        now = _time.time()
        if now - _ngrok_last_sync_at < float(min_interval):
            return _ngrok_last_result
        synced, failures = _sync_pixgo_from_ngrok(limit=limit)
        _ngrok_last_sync_at = _time.time()
        _ngrok_last_result = {"synced": synced, "failures": failures}
        return _ngrok_last_result
    finally:
        _ngrok_sync_lock.release()

def _parse_local_datetime(value):
    normalized = _normalize_datetime_value(value)
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized)
    except Exception:
        return None

def _pending_refresh_scope(chat_id=None):
    return str(chat_id) if chat_id not in (None, "") else "__all__"

def _pending_transaction_needs_refresh(row, now=None, stale_after_minutes=18):
    if not _finance_is_pending(row.get("status")):
        return False
    now = now or datetime.now()
    expires_at = _parse_local_datetime(row.get("expires_at"))
    if expires_at is not None:
        return now >= expires_at
    baseline = (
        _parse_local_datetime(row.get("updated_at"))
        or _parse_local_datetime(row.get("created_at"))
    )
    if baseline is None:
        return True
    return now >= (baseline + timedelta(minutes=stale_after_minutes))

def _refresh_pending_finance_transactions(chat_id=None, limit=12, stale_after_minutes=18):
    rows = db.get_finance_transactions(chat_id, limit=200) if chat_id is not None else db.get_finance_transactions(limit=300)
    now = datetime.now()
    candidates = [row for row in rows if _pending_transaction_needs_refresh(row, now=now, stale_after_minutes=stale_after_minutes)]
    refreshed = 0
    failures = []
    for row in candidates[:limit]:
        payment_id = str(row.get("payment_id") or "").strip()
        if not payment_id:
            continue
        account = _find_pixgo_account(row.get("provider_account"))
        api_key = ((account or {}).get("api_key") or db.get_setting("pixgo_api_key", "")).strip()
        if not api_key:
            continue
        try:
            details = pixgo.get_payment_details(api_key, payment_id)
            status = pixgo.get_payment_status(api_key, payment_id)
            merged = _merge_pixgo_payloads(details, status)
            db.upsert_finance_transaction(
                _finance_response_to_record(
                    row.get("chat_id"),
                    merged,
                    {"provider_account": (account or {}).get("name", "")},
                    row,
                )
            )
            refreshed += 1
        except pixgo.PixGoError as err:
            failures.append({"payment_id": payment_id, "msg": err.message})
    return {"refreshed": refreshed, "failures": failures[:8]}

def _maybe_refresh_pending_finance_transactions(chat_id=None, min_interval=20):
    scope = _pending_refresh_scope(chat_id)
    now = _time.time()
    last_run = _finance_refresh_last_run.get(scope, 0.0)
    if now - last_run < float(min_interval):
        return {"refreshed": 0, "failures": []}
    if not _finance_refresh_lock.acquire(blocking=False):
        return {"refreshed": 0, "failures": []}
    try:
        now = _time.time()
        last_run = _finance_refresh_last_run.get(scope, 0.0)
        if now - last_run < float(min_interval):
            return {"refreshed": 0, "failures": []}
        result = _refresh_pending_finance_transactions(chat_id=chat_id)
        _finance_refresh_last_run[scope] = _time.time()
        return result
    finally:
        _finance_refresh_lock.release()

def _verify_pixgo_webhook_signature(raw_body):
    accounts = _pixgo_accounts_from_settings()
    secrets = [item for item in accounts if item.get("webhook_secret")]
    if not secrets:
        primary = _get_default_pixgo_account()
        return True, "", primary

    timestamp = (request.headers.get("X-Webhook-Timestamp") or "").strip()
    signature = (request.headers.get("X-Webhook-Signature") or "").strip().lower()
    remote_addr = (request.remote_addr or "").strip()
    if timestamp and not signature and remote_addr in {"127.0.0.1", "::1", "localhost"}:
        return True, "", _get_default_pixgo_account()
    if not timestamp or not signature:
        return False, "Assinatura do webhook PIXGO ausente.", None

    try:
        if abs(int(_time.time()) - int(timestamp)) > 300:
            return False, "Timestamp do webhook PIXGO expirado.", None
    except Exception:
        return False, "Timestamp do webhook PIXGO invalido.", None

    for account in secrets:
        expected = hmac.new(
            account.get("webhook_secret", "").encode("utf-8"),
            timestamp.encode("utf-8") + b"." + (raw_body or b""),
            hashlib.sha256,
        ).hexdigest().lower()
        if hmac.compare_digest(expected, signature):
            return True, "", account

    return False, "Assinatura do webhook PIXGO invalida.", None

def broadcast_alert(data: dict):
    with _alert_lock:
        dead = []
        for q in _alert_queues:
            try:
                q.put_nowait(data)
            except Exception:
                dead.append(q)
        for q in dead:
            _alert_queues.remove(q)

def _chat_title_for_alert(chat_id):
    if chat_id in (None, ""):
        return ""
    target = str(chat_id)
    try:
        for row in db.get_all_groups():
            if str(row.get("chat_id")) == target:
                return row.get("chat_title") or target
    except Exception:
        pass
    return target

def _alert_identity_for_user(user_id, chat_id, username="", full_name=""):
    resolved_username = str(username or "").strip()
    resolved_full_name = str(full_name or "").strip()
    if chat_id not in (None, "") and user_id not in (None, ""):
        conn = None
        try:
            conn = db.get_connection()
            row = conn.execute(
                "SELECT username, full_name FROM members WHERE chat_id=? AND user_id=? LIMIT 1",
                (chat_id, user_id),
            ).fetchone()
            if row:
                resolved_username = str(row["username"] or resolved_username or "").strip()
                resolved_full_name = str(row["full_name"] or resolved_full_name or "").strip()
        except Exception:
            pass
        finally:
            if conn is not None:
                conn.close()
    display_name = resolved_full_name or (f"@{resolved_username}" if resolved_username else (str(user_id) if user_id not in (None, "") else ""))
    return {
        "username": resolved_username,
        "full_name": resolved_full_name,
        "display_name": display_name,
    }

# Hook into record_event to broadcast
_orig_record = db.record_event
def _sp_now():
    return datetime.utcnow() - timedelta(hours=3)

def _alert_time_label(value=None):
    raw = str(value or "").strip()
    if " " in raw:
        return raw.split(" ", 1)[1]
    if raw:
        return raw
    return _sp_now().strftime("%H:%M:%S")

def _patched_record(user_id, username, chat_id, chat_title, event_type, full_name=None):
    event_row = _orig_record(user_id, username, chat_id, chat_title, event_type, full_name=full_name) or {}
    identity = _alert_identity_for_user(user_id, chat_id, username=username, full_name=full_name)
    occurred_at = str(event_row.get("created_at") or "").strip() or _sp_now().strftime("%Y-%m-%d %H:%M:%S")
    event_id = event_row.get("id")
    broadcast_alert({
        "alert_id": f"member:{event_id}" if event_id not in (None, "") else f"member:{chat_id}:{user_id}:{event_type}:{occurred_at}",
        "type": event_type,
        "username": identity.get("username", ""),
        "full_name": identity.get("full_name", ""),
        "display_name": identity.get("display_name", ""),
        "user_id": user_id,
        "chat_id": chat_id,
        "chat_title": chat_title,
        "occurred_at": occurred_at,
        "time": _alert_time_label(occurred_at),
    })
db.record_event = _patched_record

# ── SSE alerts stream ────────────────────────────────────────
@api_bp.route("/alerts/stream")
def alerts_stream():
    q = queue.Queue(maxsize=50)
    with _alert_lock:
        _alert_queues.append(q)
    def generate():
        yield 'data: {"ping":true}\n\n'
        while True:
            try:
                data = q.get(timeout=25)
                yield 'data: ' + json.dumps(data) + '\n\n'
            except queue.Empty:
                yield 'data: {"ping":true}\n\n'
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

# ── PDF export ───────────────────────────────────────────────
@api_bp.route("/export/pdf/<path:chat_id>", methods=["GET", "POST"])
def export_pdf(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    try:
        options = request.get_json(silent=True) if request.method == "POST" else None
        filename, content = reporter.build_pdf_export(cid, options)
    except RuntimeError as err:
        return jsonify({"error": str(err)}), 500
    return Response(
        content,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ── Scheduler ────────────────────────────────────────────────
@api_bp.route("/export/csv/<path:chat_id>", methods=["GET", "POST"])
def export_csv(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    options = request.get_json(silent=True) if request.method == "POST" else None
    filename, content = reporter.build_csv_export(cid, options)
    return Response(
        content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_bp.get("/finance/overview/<path:chat_id>")
def finance_overview(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    pending_refresh = _maybe_refresh_pending_finance_transactions(chat_id=cid)
    ngrok_sync = _maybe_sync_pixgo_from_ngrok(limit=80)
    rows = db.get_finance_transactions(cid, limit=200)
    active = next((row for row in rows if _finance_is_pending(row.get("status"))), rows[0] if rows else None)
    return jsonify({
        "summary": _finance_summary(rows),
        "active_payment": active,
        "ngrok_sync": ngrok_sync,
        "pending_refresh": pending_refresh,
    })

@api_bp.get("/finance/overview")
def finance_overview_all():
    pending_refresh = _maybe_refresh_pending_finance_transactions()
    ngrok_sync = _maybe_sync_pixgo_from_ngrok(limit=80)
    rows = db.get_finance_transactions(limit=300)
    active = next((row for row in rows if _finance_is_pending(row.get("status"))), rows[0] if rows else None)
    return jsonify({
        "summary": _finance_summary(rows),
        "active_payment": active,
        "ngrok_sync": ngrok_sync,
        "pending_refresh": pending_refresh,
    })

@api_bp.get("/finance/home-metrics")
def finance_home_metrics():
    cid = get_chat_id(request.args.get("chat_id")) if request.args.get("chat_id") not in (None, "") else None
    _maybe_refresh_pending_finance_transactions(chat_id=cid)
    return jsonify(db.get_finance_home_metrics(cid))

@api_bp.get("/finance/payments/<path:chat_id>")
def finance_payments(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    _maybe_refresh_pending_finance_transactions(chat_id=cid)
    return jsonify(db.get_finance_transactions(cid, limit=120))

@api_bp.get("/finance/payments")
def finance_payments_all():
    _maybe_refresh_pending_finance_transactions()
    return jsonify(db.get_finance_transactions(limit=120))

@api_bp.post("/finance/pixgo/ngrok-sync")
def finance_pixgo_ngrok_sync():
    result = _sync_pixgo_from_ngrok(limit=120)
    return jsonify({
        "ok": True,
        "synced": result[0],
        "failures": result[1],
    })

@api_bp.get("/meta/settings")
def meta_settings():
    return jsonify({
        "pixel_id": db.get_setting("meta_pixel_id", ""),
        "access_token_set": bool(db.get_setting("meta_access_token", "").strip()),
        "access_token_preview": _mask_secret(db.get_setting("meta_access_token", "")),
        "ad_account_id": db.get_setting("meta_ad_account_id", ""),
        "dataset_id": db.get_setting("meta_dataset_id", ""),
        "test_event_code": db.get_setting("meta_test_event_code", ""),
    })

@api_bp.post("/meta/settings")
def meta_settings_save():
    data = request.get_json(silent=True) or {}
    db.set_setting("meta_pixel_id", (data.get("pixel_id") or "").strip())
    access_token = (data.get("access_token") or "").strip()
    if access_token:
        db.set_setting("meta_access_token", access_token)
    db.set_setting("meta_ad_account_id", (data.get("ad_account_id") or "").strip())
    db.set_setting("meta_dataset_id", (data.get("dataset_id") or "").strip())
    db.set_setting("meta_test_event_code", (data.get("test_event_code") or "").strip())
    return jsonify({"ok": True})

@api_bp.get("/meta/overview")
def meta_overview():
    pixel_id = db.get_setting("meta_pixel_id", "").strip()
    access_token = db.get_setting("meta_access_token", "").strip()
    ad_account_id = db.get_setting("meta_ad_account_id", "").strip()
    ready = bool(pixel_id and access_token and ad_account_id)
    return jsonify({
        "ready": ready,
        "pixel_id": pixel_id,
        "ad_account_id": ad_account_id,
        "campaigns_running": 0,
        "campaigns_paused": 0,
        "clicks_today": 0,
        "leads_today": 0,
        "last_sync_at": None,
        "next_step": (
            "Conecte Pixel ID, Access Token e Ad Account ID para liberar a sincronizacao real com a Meta."
            if not ready else
            "Credenciais salvas. O proximo passo e conectar a API de Insights e a Conversions API."
        ),
    })

@api_bp.get("/finance/pixgo/settings")
def finance_pixgo_settings():
    return jsonify(_finance_settings_payload())

@api_bp.post("/finance/pixgo/settings")
def finance_save_pixgo_settings():
    data = request.get_json(silent=True) or {}

    api_key = (data.get("api_key") or "").strip()
    webhook_secret = (data.get("webhook_secret") or "").strip()
    webhook_url = _normalize_webhook_url(data.get("webhook_url")) if "webhook_url" in data else None
    default_description = (data.get("default_description") or "").strip() if "default_description" in data else None

    accounts = _pixgo_accounts_from_settings()
    if accounts:
        primary = next((item for item in accounts if item.get("is_default")), accounts[0])
        if api_key:
            primary["api_key"] = api_key
        if webhook_secret:
            primary["webhook_secret"] = webhook_secret
        if webhook_url is not None:
            primary["webhook_url"] = webhook_url
        if default_description is not None:
            primary["default_description"] = default_description
        _save_pixgo_accounts(accounts)
    else:
        if api_key:
            db.set_setting("pixgo_api_key", api_key)
        if webhook_secret:
            db.set_setting("pixgo_webhook_secret", webhook_secret)
        if webhook_url is not None:
            db.set_setting("pixgo_webhook_url", webhook_url)
        if default_description is not None:
            db.set_setting("pixgo_default_description", default_description)

    return jsonify({
        "ok": True,
        "msg": "Configuracoes PIXGO salvas.",
        "settings": _finance_settings_payload(),
    })

@api_bp.post("/finance/pixgo/payment")
def finance_create_pixgo_payment():
    data = request.get_json(silent=True) or {}
    cid = get_chat_id(data.get("chat_id"))
    if cid is None:
        return jsonify({"ok": False, "msg": "Selecione um grupo valido."}), 400

    try:
        amount = round(float(data.get("amount") or 0), 2)
    except Exception:
        amount = 0
    if amount <= 0:
        return jsonify({"ok": False, "msg": "Informe um valor maior que zero."}), 400

    account = _get_default_pixgo_account()
    api_key = ((account or {}).get("api_key") or db.get_setting("pixgo_api_key", "")).strip()
    if not api_key:
        return jsonify({"ok": False, "msg": "Configure a API key da PIXGO primeiro."}), 400

    customer_name = (data.get("customer_name") or "").strip()
    if not customer_name:
        return jsonify({"ok": False, "msg": "Informe o nome do cliente."}), 400

    external_id = (data.get("external_id") or "").strip() or f"tg-{abs(cid)}-{int(_time.time())}"
    description = (data.get("description") or "").strip() or ((account or {}).get("default_description") or db.get_setting("pixgo_default_description", "Cobranca TG Analytics"))
    payload = {
        "amount": amount,
        "external_id": external_id,
        "description": description,
        "customer_name": customer_name,
    }

    customer_cpf = _digits(data.get("customer_cpf"))
    customer_phone = _digits(data.get("customer_phone"))
    customer_email = (data.get("customer_email") or "").strip()
    customer_address = (data.get("customer_address") or "").strip()
    webhook_url = _normalize_webhook_url((account or {}).get("webhook_url") or db.get_setting("pixgo_webhook_url", "").strip())

    if customer_cpf:
        payload["customer_cpf"] = customer_cpf
    if customer_phone:
        payload["customer_phone"] = customer_phone
    if customer_email:
        payload["customer_email"] = customer_email
    if customer_address:
        payload["customer_address"] = customer_address
    if webhook_url:
        payload["webhook_url"] = webhook_url

    try:
        response = pixgo.create_payment(api_key, payload)
        stored = db.upsert_finance_transaction(
            _finance_response_to_record(cid, response, {**payload, "amount": amount, "provider_account": (account or {}).get("name", "")})
        )
        return jsonify({"ok": True, "payment": stored})
    except pixgo.PixGoError as err:
        return jsonify({"ok": False, "msg": err.message, "details": err.payload}), err.status_code

@api_bp.post("/finance/pixgo/payment/<path:payment_id>/refresh")
def finance_refresh_pixgo_payment(payment_id):
    account = _find_pixgo_account((request.get_json(silent=True) or {}).get("provider_account"))
    api_key = ((account or {}).get("api_key") or db.get_setting("pixgo_api_key", "")).strip()
    if not api_key:
        return jsonify({"ok": False, "msg": "Configure a API key da PIXGO primeiro."}), 400

    existing = db.get_finance_transaction(payment_id)
    if not existing:
        return jsonify({"ok": False, "msg": "Pagamento nao encontrado localmente."}), 404

    try:
        details = pixgo.get_payment_details(api_key, payment_id)
        status = pixgo.get_payment_status(api_key, payment_id)
        merged = _merge_pixgo_payloads(details, status)
        stored = db.upsert_finance_transaction(
            _finance_response_to_record(existing.get("chat_id"), merged, {}, existing)
        )
        return jsonify({"ok": True, "payment": stored})
    except pixgo.PixGoError as err:
        return jsonify({"ok": False, "msg": err.message, "details": err.payload}), err.status_code

@api_bp.post("/finance/pixgo/payment-lookup")
def finance_lookup_pixgo_payment():
    data = request.get_json(silent=True) or {}
    payment_id = str(data.get("payment_id") or "").strip()
    if not payment_id:
        return jsonify({"ok": False, "msg": "Informe o payment_id da transacao."}), 400

    requested_account = str(data.get("provider_account") or "").strip()
    candidates = []
    if requested_account:
        account = _find_pixgo_account(requested_account)
        if account:
            candidates = [account]
    else:
        candidates = _pixgo_accounts_from_settings() or [_get_default_pixgo_account()]
        candidates = [item for item in candidates if item]

    if not candidates:
        return jsonify({"ok": False, "msg": "Configure ao menos uma conta PIXGO primeiro."}), 400

    last_error = None
    for account in candidates:
        api_key = (account.get("api_key") or "").strip()
        if not api_key:
            continue
        try:
            details = pixgo.get_payment_details(api_key, payment_id)
            status = pixgo.get_payment_status(api_key, payment_id)
            merged = _merge_pixgo_payloads(details, status)
            existing = db.get_finance_transaction(payment_id) or {}
            stored = db.upsert_finance_transaction(
                _finance_response_to_record(
                    existing.get("chat_id"),
                    merged,
                    {"provider_account": account.get("name", "")},
                    existing,
                )
            )
            return jsonify({"ok": True, "payment": stored, "provider_account": account.get("name", "")})
        except pixgo.PixGoError as err:
            last_error = err
            continue

    if last_error:
        return jsonify({"ok": False, "msg": last_error.message, "details": last_error.payload}), last_error.status_code
    return jsonify({"ok": False, "msg": "Nao foi possivel consultar a transacao nas contas configuradas."}), 404

@api_bp.post("/finance/pixgo/refresh-all")
def finance_refresh_all_pixgo():
    account = _get_default_pixgo_account()
    api_key = ((account or {}).get("api_key") or db.get_setting("pixgo_api_key", "")).strip()
    if not api_key:
        return jsonify({"ok": False, "msg": "Configure a API key da PIXGO primeiro."}), 400

    data = request.get_json(silent=True) or {}
    cid = get_chat_id(data.get("chat_id")) if data.get("chat_id") not in (None, "") else None
    pending_only = bool(data.get("pending_only"))
    rows = db.get_finance_transactions(cid, limit=200) if cid is not None else db.get_finance_transactions(limit=200)
    if not rows:
        return jsonify({"ok": True, "updated": 0, "failures": [], "summary": _finance_summary([])})
    if pending_only:
        rows = [row for row in rows if _finance_is_pending(row.get("status"))]
        if not rows:
            refreshed_rows = db.get_finance_transactions(cid, limit=200) if cid is not None else db.get_finance_transactions(limit=200)
            return jsonify({
                "ok": True,
                "updated": 0,
                "failures": [],
                "summary": _finance_summary(refreshed_rows),
            })

    updated = 0
    failures = []
    for row in rows:
        payment_id = row.get("payment_id")
        if not payment_id:
            continue
        try:
            details = pixgo.get_payment_details(api_key, payment_id)
            status = pixgo.get_payment_status(api_key, payment_id)
            merged = _merge_pixgo_payloads(details, status)
            db.upsert_finance_transaction(
                _finance_response_to_record(row.get("chat_id"), merged, {}, row)
            )
            updated += 1
        except pixgo.PixGoError as err:
            failures.append({
                "payment_id": str(payment_id),
                "msg": err.message,
            })

    refreshed_rows = db.get_finance_transactions(cid, limit=200) if cid is not None else db.get_finance_transactions(limit=200)
    return jsonify({
        "ok": True,
        "updated": updated,
        "failures": failures[:8],
        "summary": _finance_summary(refreshed_rows),
    })

@api_bp.post("/finance/import")
def finance_import_transactions():
    default_chat_id = get_chat_id(request.form.get("chat_id") or request.args.get("chat_id"))
    default_account = (request.form.get("provider_account") or request.args.get("provider_account") or "").strip()
    imported_rows = []

    upload = request.files.get("file")
    if upload and upload.filename:
        content = upload.stream.read().decode("utf-8-sig", "replace")
        imported_rows = _parse_import_text(content, upload.filename)
    else:
        raw_text = (request.form.get("raw_text") or request.get_data(cache=False, as_text=True) or "").strip()
        if raw_text:
            imported_rows = _parse_import_text(raw_text, request.form.get("filename") or "")

    if not imported_rows:
        return jsonify({"ok": False, "msg": "Envie um arquivo CSV/JSON ou cole o conteudo para importar."}), 400

    imported = 0
    skipped = []
    for idx, row in enumerate(imported_rows, start=1):
        try:
            tx = _import_row_to_transaction(row, default_chat_id=default_chat_id, default_account=default_account)
            db.upsert_finance_transaction(tx)
            imported += 1
        except Exception as err:
            skipped.append({"row": idx, "msg": str(err)})

    scope_rows = db.get_finance_transactions(default_chat_id, limit=200) if default_chat_id is not None else db.get_finance_transactions(limit=200)
    return jsonify({
        "ok": True,
        "imported": imported,
        "skipped": skipped[:20],
        "summary": _finance_summary(scope_rows),
    })

@api_bp.post("/finance/pixgo/webhook")
def finance_pixgo_webhook():
    raw_body = request.get_data(cache=True, as_text=False)
    is_valid, error_msg, matched_account = _verify_pixgo_webhook_signature(raw_body)
    if not is_valid:
        return jsonify({"ok": False, "msg": error_msg}), 401

    payload = request.get_json(silent=True) or {}
    payment_id = _first_value(
        payload,
        ("payment_id",),
        ("deposit_id",),
        ("id",),
        ("payment", "payment_id"),
        ("payment", "deposit_id"),
        ("data", "payment_id"),
        ("data", "deposit_id"),
        ("data", "id"),
    )
    if not payment_id:
        return jsonify({"ok": True, "msg": "Webhook recebido sem payment_id/deposit_id."})

    existing = db.get_finance_transaction(payment_id) or {}
    default_account = _get_default_pixgo_account()
    account = matched_account or default_account
    api_key = ((account or {}).get("api_key") or db.get_setting("pixgo_api_key", "")).strip()
    confirmed = payload

    if api_key:
        try:
            details = pixgo.get_payment_details(api_key, payment_id)
            status = pixgo.get_payment_status(api_key, payment_id)
            confirmed = _merge_pixgo_payloads(details, status)
        except pixgo.PixGoError:
            confirmed = payload

    try:
        stored = db.upsert_finance_transaction(
            _finance_response_to_record(
                existing.get("chat_id"),
                confirmed,
                {"provider_account": (account or {}).get("name", "")},
                existing,
            )
        )
    except Exception as err:
        return jsonify({"ok": False, "msg": f"Falha ao salvar webhook PIXGO: {err}"}), 500

    if not existing:
        broadcast_alert({
            "alert_id": f"finance:{stored.get('payment_id')}",
            "type": "finance",
            "title": "Nova transacao recebida",
            "message": "Uma nova cobranca apareceu no financeiro.",
            "chat_id": stored.get("chat_id"),
            "chat_title": _chat_title_for_alert(stored.get("chat_id")),
            "provider_account": stored.get("provider_account") or "",
            "payment_id": stored.get("payment_id") or "",
            "external_id": stored.get("external_id") or "",
            "amount": stored.get("amount") or 0,
            "occurred_at": stored.get("created_at") or stored.get("updated_at") or _sp_now().strftime("%Y-%m-%d %H:%M:%S"),
            "time": _alert_time_label(stored.get("created_at") or stored.get("updated_at")),
        })

    return jsonify({"ok": True, "payment_id": str(payment_id)})


@api_bp.get("/name-search")
def name_search():
    search_map = {
        "nome": {"path": "/api/busca_nome.php", "param": "nome"},
        "cpf": {"path": "/api/busca_cpf.php", "param": "cpf"},
        "titulo": {"path": "/api/busca_titulo.php", "param": "titulo"},
        "mae": {"path": "/api/busca_mae.php", "param": "mae"},
        "pai": {"path": "/api/busca_pai.php", "param": "pai"},
        "rg": {"path": "/api/busca_rg.php", "param": "rg"},
    }

    search_type = (request.args.get("tipo") or request.args.get("type") or "nome").strip().lower()
    search_cfg = search_map.get(search_type)
    if not search_cfg:
        return jsonify({
            "ok": False,
            "msg": "Tipo de consulta invalido. Use: nome, cpf, titulo, mae, pai ou rg.",
        }), 400

    raw_value = (
        request.args.get("valor")
        or request.args.get(search_cfg["param"])
        or ""
    ).strip()
    if not raw_value:
        return jsonify({"ok": False, "msg": "Informe um valor para pesquisar."}), 400

    if search_type in {"nome", "mae", "pai"} and len(raw_value) < 2:
        return jsonify({"ok": False, "msg": "Informe ao menos 2 caracteres para pesquisar."}), 400

    target_url = f"http://apisbrasilpro.site{search_cfg['path']}?{search_cfg['param']}={quote_plus(raw_value)}"
    req = Request(target_url, headers={
        "User-Agent": "TelegramAnalytics/2026.04",
        "Accept": "application/json, text/plain, */*",
    })
    try:
        with urlopen(req, timeout=20) as resp:
            raw_body = resp.read()
    except Exception as err:
        return jsonify({"ok": False, "msg": f"Falha ao consultar API externa: {err}"}), 502

    decoded = None
    for encoding in ("utf-8", "latin-1"):
        try:
            decoded = raw_body.decode(encoding)
            break
        except Exception:
            continue

    if decoded is None:
        decoded = raw_body.decode("utf-8", "replace")

    payload = None
    try:
        payload = json.loads(decoded)
    except Exception:
        payload = decoded

    raw_results = payload.get("RESULTADOS") if isinstance(payload, dict) else payload
    if not isinstance(raw_results, list):
        raw_results = []

    source = ""
    if isinstance(payload, dict):
        source = str(payload.get("CRIADO_POR") or "").strip()

    return jsonify({
        "ok": True,
        "query": raw_value,
        "search_type": search_type,
        "search_param": search_cfg["param"],
        "endpoint": search_cfg["path"],
        "target_url": target_url,
        "total": len(raw_results),
        "results": raw_results,
        "source": source,
        "raw": payload,
    })


@api_bp.get("/campaigns/sources/<path:chat_id>")
def campaign_sources(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    return jsonify(db.get_campaign_sources(cid))


@api_bp.post("/campaigns/sources")
def campaign_source_create():
    data = request.get_json(silent=True) or {}
    cid = get_chat_id(data.get("chat_id"))
    if cid is None:
        return jsonify({"ok": False, "msg": "chat_id invalido"}), 400
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "msg": "name required"}), 400
    db.create_campaign_source(
        cid,
        name,
        data.get("source_type") or "campaign",
        data.get("cost_amount") or 0,
        data.get("notes") or "",
    )
    return jsonify({"ok": True})


@api_bp.delete("/campaigns/sources/<int:source_id>")
def campaign_source_remove(source_id):
    db.delete_campaign_source(source_id)
    return jsonify({"ok": True})


@api_bp.get("/campaigns/assignments/<path:chat_id>")
def campaign_assignments(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    return jsonify(db.get_campaign_assignments(cid))


@api_bp.post("/campaigns/assignments")
def campaign_assignment_create():
    data = request.get_json(silent=True) or {}
    cid = get_chat_id(data.get("chat_id"))
    user_id = get_chat_id(data.get("user_id"))
    source_id = get_chat_id(data.get("source_id"))
    if cid is None or user_id is None or source_id is None:
        return jsonify({"ok": False, "msg": "chat_id, user_id and source_id are required"}), 400
    db.assign_campaign_source(cid, user_id, source_id)
    return jsonify({"ok": True})


@api_bp.delete("/campaigns/assignments/<int:assignment_id>")
def campaign_assignment_remove(assignment_id):
    db.remove_campaign_assignment(assignment_id)
    return jsonify({"ok": True})


@api_bp.get("/campaigns/report/<path:chat_id>")
def campaign_report(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"error": "chat_id invalido"}), 400
    return jsonify(db.get_campaign_report(cid))


@api_bp.get("/reports/schedules")
def report_schedules():
    raw_chat_id = request.args.get("chat_id")
    cid = get_chat_id(raw_chat_id) if raw_chat_id not in (None, "") else None
    return jsonify(db.get_scheduled_reports(cid))


@api_bp.post("/reports/schedules")
def report_schedule_create():
    data = request.get_json(silent=True) or {}
    cid = get_chat_id(data.get("chat_id"))
    if cid is None:
        return jsonify({"ok": False, "msg": "chat_id invalido"}), 400
    delivery_type = (data.get("delivery_type") or "").strip().lower()
    destination = (data.get("destination") or "").strip()
    fmt = (data.get("format") or "pdf").strip().lower()
    if delivery_type not in {"telegram", "email"}:
        return jsonify({"ok": False, "msg": "delivery_type invalido"}), 400
    if not destination:
        return jsonify({"ok": False, "msg": "destination required"}), 400
    db.add_scheduled_report(
        cid,
        delivery_type,
        destination,
        fmt,
        data.get("weekday") or 0,
        data.get("hour") or 9,
        data.get("minute") or 0,
    )
    return jsonify({"ok": True})


@api_bp.delete("/reports/schedules/<int:report_id>")
def report_schedule_delete(report_id):
    db.delete_scheduled_report(report_id)
    return jsonify({"ok": True})


@api_bp.post("/reports/send-now/<path:chat_id>")
def report_send_now(chat_id):
    cid = get_chat_id(chat_id)
    if cid is None:
        return jsonify({"ok": False, "msg": "chat_id invalido"}), 400
    payload = request.get_json(silent=True) or {}
    fmt = payload.get("format") or "pdf"
    options = payload.get("options")
    if fmt == "pdf":
        filename, content = reporter.build_pdf_export(cid, options)
        return Response(
            content,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    filename, content = reporter.build_csv_export(cid, options)
    return Response(
        content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_bp.route("/scheduler", methods=["GET"])
def scheduler_list():
    chat_id = request.args.get("chat_id", type=int)
    return jsonify(db.get_scheduled_messages(chat_id))

@api_bp.route("/scheduler", methods=["POST"])
def scheduler_add():
    data = request.get_json()
    if not data or not data.get("chat_id") or not data.get("message") or not data.get("send_at"):
        return jsonify({"error": "chat_id, message, send_at required"}), 400
    db.add_scheduled_message(data["chat_id"], data["message"], data["send_at"])
    return jsonify({"ok": True})

@api_bp.route("/scheduler/<int:msg_id>", methods=["DELETE"])
def scheduler_delete(msg_id):
    db.delete_scheduled_message(msg_id)
    return jsonify({"ok": True})

# ── Vault access log ─────────────────────────────────────────
@api_bp.route("/vault/access_log")
def vault_access_log():
    entry_id = request.args.get("entry_id", type=int)
    rows = db.get_vault_access_log(entry_id)
    return jsonify(rows)

@api_bp.route("/vault/access_log", methods=["POST"])
def vault_log_access():
    data = request.get_json()
    if data and data.get("entry_id") and data.get("action"):
        db.log_vault_access(data["entry_id"], data["action"])
    return jsonify({"ok": True})

# ── Bot logs stream ──────────────────────────────────────────
_bot_logs = []
_log_lock  = threading.Lock()
MAX_LOGS   = 200

class _DashboardLogHandler:
    def write(self, msg):
        if msg.strip():
            with _log_lock:
                _bot_logs.append({
                    "time": _sp_now().strftime("%H:%M:%S"),
                    "msg": msg.strip()
                })
                if len(_bot_logs) > MAX_LOGS:
                    _bot_logs.pop(0)
    def flush(self): pass

import logging as _logging
_handler = _logging.StreamHandler()
_handler.stream = _DashboardLogHandler()
_logging.getLogger().addHandler(_handler)

@api_bp.route("/bot/logs")
def bot_logs():
    return jsonify(_bot_logs[-100:])
