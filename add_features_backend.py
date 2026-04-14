import os

# ── 1. requirements.txt ──────────────────────────────────────
reqs = open('requirements.txt', encoding='utf-8').read()
extras = '\nreportlab>=4.0.0\nflask-cors>=4.0.0\n'
if 'reportlab' not in reqs:
    open('requirements.txt', 'a').write(extras)
    print('requirements.txt atualizado')

# ── 2. database/schema.sql — novas tabelas ───────────────────
schema_extra = """
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL,
    message    TEXT    NOT NULL,
    send_at    DATETIME NOT NULL,
    sent       INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vault_access_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id   INTEGER NOT NULL,
    action     TEXT    NOT NULL,
    created_at DATETIME DEFAULT (datetime('now'))
);
"""
schema_path = 'database/schema.sql'
schema = open(schema_path, encoding='utf-8').read()
if 'scheduled_messages' not in schema:
    open(schema_path, 'a', encoding='utf-8').write(schema_extra)
    print('schema.sql atualizado')

# ── 3. app/services/db_service.py — novos métodos ────────────
db_extra = '''

def get_scheduled_messages(chat_id=None):
    conn = get_connection()
    if chat_id:
        rows = conn.execute(
            "SELECT * FROM scheduled_messages WHERE chat_id=? ORDER BY send_at ASC", (chat_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scheduled_messages ORDER BY send_at ASC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_scheduled_message(chat_id, message, send_at):
    conn = get_connection()
    conn.execute(
        "INSERT INTO scheduled_messages (chat_id, message, send_at) VALUES (?,?,?)",
        (chat_id, message, send_at)
    )
    conn.commit()
    conn.close()

def delete_scheduled_message(msg_id):
    conn = get_connection()
    conn.execute("DELETE FROM scheduled_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()

def log_vault_access(entry_id, action):
    conn = get_connection()
    conn.execute(
        "INSERT INTO vault_access_log (entry_id, action) VALUES (?,?)",
        (entry_id, action)
    )
    conn.commit()
    conn.close()

def get_vault_access_log(entry_id=None, limit=50):
    conn = get_connection()
    if entry_id:
        rows = conn.execute(
            "SELECT * FROM vault_access_log WHERE entry_id=? ORDER BY created_at DESC LIMIT ?",
            (entry_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM vault_access_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_events_for_export(chat_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, user_id, username, event_type, created_at
           FROM events WHERE chat_id=? ORDER BY created_at DESC""",
        (chat_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
'''

db_path = 'app/services/db_service.py'
db = open(db_path, encoding='utf-8').read()
if 'get_scheduled_messages' not in db:
    open(db_path, 'a', encoding='utf-8').write(db_extra)
    print('db_service.py atualizado')

# ── 4. app/routes/api.py — novos endpoints ───────────────────
api_extra = '''
import csv
import io
import json
import queue
import threading
import time as _time
from datetime import datetime
from flask import Response, stream_with_context

# SSE broadcast queue
_alert_queues = []
_alert_lock   = threading.Lock()

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

# Hook into record_event to broadcast
_orig_record = db.record_event
def _patched_record(user_id, username, chat_id, chat_title, event_type):
    _orig_record(user_id, username, chat_id, chat_title, event_type)
    broadcast_alert({
        "type": event_type,
        "username": username,
        "chat_id": chat_id,
        "chat_title": chat_title,
        "time": datetime.utcnow().strftime("%H:%M:%S")
    })
db.record_event = _patched_record

# ── SSE alerts stream ────────────────────────────────────────
@api_bp.route("/alerts/stream")
def alerts_stream():
    q = queue.Queue(maxsize=50)
    with _alert_lock:
        _alert_queues.append(q)
    def generate():
        yield "data: {}\\'ping\\'}\\'}\n\n".replace("{\\'ping\\'}\\'}", '{"ping":true}\n\n')
        while True:
            try:
                data = q.get(timeout=25)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                yield "data: {}\n\n"
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

# ── CSV export ───────────────────────────────────────────────
@api_bp.route("/export/csv/<int:chat_id>")
def export_csv(chat_id):
    events = db.get_all_events_for_export(chat_id)
    buf = io.StringIO()
    w   = csv.DictWriter(buf, fieldnames=["id","user_id","username","event_type","created_at"])
    w.writeheader()
    w.writerows(events)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=events_{chat_id}.csv"}
    )

# ── PDF export ───────────────────────────────────────────────
@api_bp.route("/export/pdf/<int:chat_id>")
def export_pdf(chat_id):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        return jsonify({"error": "reportlab not installed"}), 500

    summary = db.get_summary(chat_id)
    events  = db.get_all_events_for_export(chat_id)[:200]
    report  = db.get_raw_timeseries(chat_id)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story  = []

    story.append(Paragraph(f"TG Analytics — Report for Chat {chat_id}", styles["Title"]))
    story.append(Spacer(1, 12))

    tj = summary.get("total_joins",  0) or 0
    tl = summary.get("total_leaves", 0) or 0
    summary_data = [
        ["Metric", "Value"],
        ["Total Joins",  str(tj)],
        ["Total Leaves", str(tl)],
        ["Net Growth",   str(tj - tl)],
        ["Churn Rate",   f"{round(tl/tj*100,1) if tj else 0}%"],
    ]
    t = Table(summary_data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#161b22")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f0f0")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Recent Events (last 200)", styles["Heading2"]))
    story.append(Spacer(1, 8))

    ev_data = [["#", "Username", "Type", "Date"]]
    for i, ev in enumerate(events[:100], 1):
        ev_data.append([str(i), f"@{ev['username']}", ev["event_type"].upper(), ev["created_at"][:16]])

    t2 = Table(ev_data, colWidths=[30, 160, 80, 130])
    t2.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#0d1117")),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    story.append(t2)
    doc.build(story)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{chat_id}.pdf"}
    )

# ── Scheduler ────────────────────────────────────────────────
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
                    "time": datetime.utcnow().strftime("%H:%M:%S"),
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
'''

api_path = 'app/routes/api.py'
api = open(api_path, encoding='utf-8').read()
if 'alerts_stream' not in api:
    open(api_path, 'a', encoding='utf-8').write(api_extra)
    print('api.py atualizado com todos os novos endpoints')

print('\nBloco 1 concluído! Instale as dependências:')
print('pip install reportlab flask-cors')