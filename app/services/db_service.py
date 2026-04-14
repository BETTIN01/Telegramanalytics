import json
import sqlite3, os
import re
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
from config import DATABASE_PATH

def _c():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    c = sqlite3.connect(DATABASE_PATH, check_same_thread=False, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c

def get_connection():
    return _c()

def init_db():
    sql = (Path(__file__).parent.parent.parent / "database" / "schema.sql").read_text()
    c = _c(); c.executescript(sql); c.commit(); c.close()
    ensure_finance_schema()
    ensure_dashboard_user_schema()
    ensure_login_security_schema()
    ensure_saas_schema()
    ensure_performance_schema()
    ensure_default_dashboard_user()


def ensure_finance_schema():
    conn = get_connection()
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(finance_transactions)").fetchall()}
    if "provider_account" not in cols:
        conn.execute("ALTER TABLE finance_transactions ADD COLUMN provider_account TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.close()


def ensure_dashboard_user_schema():
    conn = get_connection()
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(dashboard_users)").fetchall()}
    if "password_hash" not in cols:
        conn.execute("ALTER TABLE dashboard_users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''")
    if "role" not in cols:
        conn.execute("ALTER TABLE dashboard_users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    if "is_active" not in cols:
        conn.execute("ALTER TABLE dashboard_users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
    if "last_login_at" not in cols:
        conn.execute("ALTER TABLE dashboard_users ADD COLUMN last_login_at DATETIME")
    pref_cols = {row["name"] for row in conn.execute("PRAGMA table_info(dashboard_user_preferences)").fetchall()}
    if "avatar_url" not in pref_cols:
        conn.execute("ALTER TABLE dashboard_user_preferences ADD COLUMN avatar_url TEXT NOT NULL DEFAULT ''")
    if "profile_title" not in pref_cols:
        conn.execute("ALTER TABLE dashboard_user_preferences ADD COLUMN profile_title TEXT NOT NULL DEFAULT ''")
    if "profile_bio" not in pref_cols:
        conn.execute("ALTER TABLE dashboard_user_preferences ADD COLUMN profile_bio TEXT NOT NULL DEFAULT ''")
    if "motion_level" not in pref_cols:
        conn.execute("ALTER TABLE dashboard_user_preferences ADD COLUMN motion_level TEXT NOT NULL DEFAULT 'standard'")
    conn.commit()
    conn.close()

def ensure_login_security_schema():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dashboard_login_attempts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL DEFAULT '',
            ip_address    TEXT    NOT NULL DEFAULT '',
            success       INTEGER NOT NULL DEFAULT 0,
            attempted_at  DATETIME NOT NULL DEFAULT (datetime('now','-3 hours'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dashboard_login_attempts_lookup ON dashboard_login_attempts(username, ip_address, attempted_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dashboard_login_attempts_ip ON dashboard_login_attempts(ip_address, attempted_at)"
    )
    conn.execute(
        "DELETE FROM dashboard_login_attempts WHERE attempted_at < datetime('now','-3 hours','-30 days')"
    )
    conn.commit()
    conn.close()

def ensure_performance_schema():
    conn = get_connection()
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_groups_last_event ON groups(last_event DESC)",
        "CREATE INDEX IF NOT EXISTS idx_events_chat_created ON events(chat_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_events_chat_type_created ON events(chat_id, event_type, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_members_chat_admin_username ON members(chat_id, is_admin DESC, username ASC)",
        "CREATE INDEX IF NOT EXISTS idx_finance_chat_status_created ON finance_transactions(chat_id, status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_finance_status_created ON finance_transactions(status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_dashboard_users_role_active ON dashboard_users(role, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_scheduled_reports_due_lookup ON scheduled_reports(active, weekday, hour, minute, last_sent_at)",
        "CREATE INDEX IF NOT EXISTS idx_groups_org_last_event ON groups(organization_id, last_event DESC)",
        "CREATE INDEX IF NOT EXISTS idx_events_org_chat_created ON events(organization_id, chat_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_members_org_chat_admin ON members(organization_id, chat_id, is_admin DESC)",
        "CREATE INDEX IF NOT EXISTS idx_finance_org_status_created ON finance_transactions(organization_id, status, created_at DESC)",
    ]
    for sql in statements:
        conn.execute(sql)
    conn.commit()
    conn.close()

def ensure_saas_schema():
    conn = get_connection()
    tables = {
        row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "groups" in tables:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(groups)").fetchall()}
        if "organization_id" not in cols:
            conn.execute("ALTER TABLE groups ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1")
    if "events" in tables:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
        if "organization_id" not in cols:
            conn.execute("ALTER TABLE events ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1")
    if "members" in tables:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(members)").fetchall()}
        if "organization_id" not in cols:
            conn.execute("ALTER TABLE members ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1")
    if "finance_transactions" in tables:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(finance_transactions)").fetchall()}
        if "organization_id" not in cols:
            conn.execute("ALTER TABLE finance_transactions ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1")
    if "scheduled_reports" in tables:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(scheduled_reports)").fetchall()}
        if "organization_id" not in cols:
            conn.execute("ALTER TABLE scheduled_reports ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            slug          TEXT NOT NULL UNIQUE,
            status        TEXT NOT NULL DEFAULT 'active',
            created_at    DATETIME NOT NULL DEFAULT (datetime('now','-3 hours'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_memberships (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            role            TEXT NOT NULL DEFAULT 'member',
            created_at      DATETIME NOT NULL DEFAULT (datetime('now','-3 hours')),
            UNIQUE(organization_id, user_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS saas_plans (
            code                TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            tagline             TEXT NOT NULL DEFAULT '',
            monthly_price_cents INTEGER NOT NULL DEFAULT 0,
            yearly_price_cents  INTEGER NOT NULL DEFAULT 0,
            limits_json         TEXT NOT NULL DEFAULT '{}',
            features_json       TEXT NOT NULL DEFAULT '[]',
            is_active           INTEGER NOT NULL DEFAULT 1,
            sort_order          INTEGER NOT NULL DEFAULT 0,
            created_at          DATETIME NOT NULL DEFAULT (datetime('now','-3 hours'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_subscriptions (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id        INTEGER NOT NULL UNIQUE,
            plan_code              TEXT NOT NULL,
            billing_cycle          TEXT NOT NULL DEFAULT 'monthly',
            status                 TEXT NOT NULL DEFAULT 'trialing',
            seats                  INTEGER NOT NULL DEFAULT 1,
            cancel_at_period_end   INTEGER NOT NULL DEFAULT 0,
            started_at             DATETIME NOT NULL DEFAULT (datetime('now','-3 hours')),
            renews_at              DATETIME,
            trial_ends_at          DATETIME,
            stripe_customer_id     TEXT NOT NULL DEFAULT '',
            stripe_subscription_id TEXT NOT NULL DEFAULT '',
            updated_at             DATETIME NOT NULL DEFAULT (datetime('now','-3 hours'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_usage_counters (
            organization_id INTEGER PRIMARY KEY,
            groups_count    INTEGER NOT NULL DEFAULT 0,
            events_count    INTEGER NOT NULL DEFAULT 0,
            automations_count INTEGER NOT NULL DEFAULT 0,
            integrations_count INTEGER NOT NULL DEFAULT 0,
            updated_at      DATETIME NOT NULL DEFAULT (datetime('now','-3 hours'))
        )
        """
    )

    plan_rows = [
        (
            "free",
            "Free",
            "Primeiros sinais do grupo",
            0,
            0,
            json.dumps({"groups": 1, "events_per_month": 1000, "automations": 1, "team_members": 1, "integrations": 1}),
            json.dumps(["overview", "events", "basic_reports"]),
            0,
        ),
        (
            "pro",
            "Pro",
            "Operação com automações e exportações",
            9900,
            99000,
            json.dumps({"groups": 5, "events_per_month": 25000, "automations": 10, "team_members": 5, "integrations": 3}),
            json.dumps(["overview", "events", "charts", "finance", "pixel", "scheduled_reports", "team_access", "csv_pdf_exports"]),
            1,
        ),
        (
            "premium",
            "Premium",
            "Escala com inteligência e integrações",
            29900,
            299000,
            json.dumps({"groups": 25, "events_per_month": 250000, "automations": 100, "team_members": 25, "integrations": 10}),
            json.dumps(["overview", "events", "charts", "finance", "pixel", "scheduled_reports", "team_access", "csv_pdf_exports", "smart_alerts", "ai_insights", "growth_forecast", "webhooks", "priority_support"]),
            2,
        ),
    ]
    conn.executemany(
        """
        INSERT INTO saas_plans(code, name, tagline, monthly_price_cents, yearly_price_cents, limits_json, features_json, sort_order)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(code) DO UPDATE SET
            name=excluded.name,
            tagline=excluded.tagline,
            monthly_price_cents=excluded.monthly_price_cents,
            yearly_price_cents=excluded.yearly_price_cents,
            limits_json=excluded.limits_json,
            features_json=excluded.features_json,
            sort_order=excluded.sort_order,
            is_active=1
        """,
        plan_rows,
    )

    conn.execute(
        "INSERT OR IGNORE INTO organizations(id, name, slug, status) VALUES (1, 'Velatura Workspace', 'velatura-workspace', 'active')"
    )
    user_rows = conn.execute("SELECT id, role FROM dashboard_users").fetchall()
    for row in user_rows:
        member_role = "owner" if (row["role"] or "user") == "admin" else "member"
        conn.execute(
            """
            INSERT OR IGNORE INTO organization_memberships(organization_id, user_id, role)
            VALUES (?,?,?)
            """,
            (1, row["id"], member_role),
        )
    conn.execute(
        """
        INSERT OR IGNORE INTO organization_subscriptions(
            organization_id, plan_code, billing_cycle, status, seats, started_at, trial_ends_at, updated_at
        )
        VALUES (
            1, 'premium', 'monthly', 'active',
            COALESCE((SELECT COUNT(*) FROM dashboard_users WHERE is_active=1), 1),
            datetime('now','-3 hours'),
            datetime('now','-3 hours','+14 days'),
            datetime('now','-3 hours')
        )
        """
    )
    conn.commit()
    conn.close()

def _normalize_login_identity(value):
    return (value or "").strip().lower()

def _normalize_ip_address(value):
    raw = (value or "").strip()
    if "," in raw:
        raw = raw.split(",", 1)[0].strip()
    return raw[:64]

def _parse_db_datetime(value):
    if not value:
        return None
    text = str(value).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None

def record_dashboard_login_attempt(username, ip_address, success):
    ensure_login_security_schema()
    normalized_username = _normalize_login_identity(username)
    normalized_ip = _normalize_ip_address(ip_address)
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO dashboard_login_attempts(username, ip_address, success, attempted_at)
        VALUES (?,?,?,datetime('now','-3 hours'))
        """,
        (normalized_username, normalized_ip, 1 if success else 0),
    )
    if success:
        conn.execute(
            """
            DELETE FROM dashboard_login_attempts
            WHERE success=0 AND (username=? OR ip_address=?)
            """,
            (normalized_username, normalized_ip),
        )
    conn.execute(
        "DELETE FROM dashboard_login_attempts WHERE attempted_at < datetime('now','-3 hours','-30 days')"
    )
    conn.commit()
    conn.close()

def get_dashboard_login_lock(username, ip_address, window_minutes=15, max_user_ip_failures=5, max_ip_failures=15):
    ensure_login_security_schema()
    normalized_username = _normalize_login_identity(username)
    normalized_ip = _normalize_ip_address(ip_address)
    conn = get_connection()
    user_ip_rows = conn.execute(
        """
        SELECT attempted_at
        FROM dashboard_login_attempts
        WHERE success=0
          AND username=?
          AND ip_address=?
          AND attempted_at >= datetime('now','-3 hours', ?)
        ORDER BY attempted_at ASC
        """,
        (normalized_username, normalized_ip, f"-{int(window_minutes)} minutes"),
    ).fetchall()
    ip_rows = conn.execute(
        """
        SELECT attempted_at
        FROM dashboard_login_attempts
        WHERE success=0
          AND ip_address=?
          AND attempted_at >= datetime('now','-3 hours', ?)
        ORDER BY attempted_at ASC
        """,
        (normalized_ip, f"-{int(window_minutes)} minutes"),
    ).fetchall()
    conn.close()

    blocked_rows = None
    if normalized_username and normalized_ip and len(user_ip_rows) >= int(max_user_ip_failures):
        blocked_rows = user_ip_rows
    elif normalized_ip and len(ip_rows) >= int(max_ip_failures):
        blocked_rows = ip_rows

    if not blocked_rows:
        return {
            "blocked": False,
            "retry_after_seconds": 0,
            "remaining_attempts": max(0, int(max_user_ip_failures) - len(user_ip_rows)),
        }

    oldest = _parse_db_datetime(blocked_rows[0]["attempted_at"] if blocked_rows else None)
    retry_after_seconds = 0
    if oldest is not None:
        unlock_at = oldest + timedelta(minutes=int(window_minutes))
        retry_after_seconds = max(0, int((unlock_at - datetime.now()).total_seconds()))
    return {
        "blocked": True,
        "retry_after_seconds": retry_after_seconds,
        "remaining_attempts": 0,
    }

def get_setting(key, default=""):
    c = _c()
    row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    c.close()
    return row["value"] if row else default

def set_setting(key, value):
    c = _c()
    c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
              "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    c.commit(); c.close()

def upsert_group(chat_id, chat_title):
    c = _c()
    c.execute("INSERT INTO groups(chat_id,chat_title,last_event) VALUES(?,?,datetime('now','-3 hours')) "
              "ON CONFLICT(chat_id) DO UPDATE SET chat_title=excluded.chat_title,"
              "last_event=datetime('now','-3 hours')", (chat_id, chat_title))
    c.commit(); c.close()

def get_all_groups():
    c = _c()
    rows = c.execute("SELECT chat_id,chat_title,first_seen,last_event "
                     "FROM groups ORDER BY last_event DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]

def delete_group(chat_id):
    c = _c()
    c.execute("DELETE FROM groups WHERE chat_id=?", (chat_id,))
    c.execute("DELETE FROM events WHERE chat_id=?", (chat_id,))
    c.commit(); c.close()

def record_event(user_id, username, chat_id, chat_title, event_type, full_name=None):
    c = _c()
    inserted = c.execute(
        "INSERT INTO events(user_id,username,chat_id,chat_title,event_type,created_at) "
        "VALUES(?,?,?,?,?,datetime('now','-3 hours'))",
        (user_id, username, chat_id, chat_title, event_type)
    )
    event_id = inserted.lastrowid
    c.execute(
        "INSERT INTO groups(chat_id,chat_title,last_event) VALUES(?,?,datetime('now','-3 hours')) "
        "ON CONFLICT(chat_id) DO UPDATE SET "
        "chat_title=excluded.chat_title, last_event=datetime('now','-3 hours')",
        (chat_id, chat_title)
    )
    c.commit()
    row = c.execute(
        "SELECT id,user_id,username,chat_id,chat_title,event_type,created_at "
        "FROM events WHERE id=?",
        (event_id,)
    ).fetchone()
    c.close()
    return dict(row) if row else None

def get_summary(chat_id):
    c = _c()
    row = c.execute(
        "SELECT SUM(CASE WHEN event_type='join'  THEN 1 ELSE 0 END) AS total_joins,"
        "       SUM(CASE WHEN event_type='leave' THEN 1 ELSE 0 END) AS total_leaves,"
        "       MIN(created_at) AS first_event, MAX(created_at) AS last_event "
        "FROM events WHERE chat_id=?", (chat_id,)).fetchone()
    c.close()
    return dict(row) if row else {}

def get_timeseries(chat_id):
    c = _c()
    rows = c.execute(
        "SELECT date(created_at) AS day,"
        "  SUM(CASE WHEN event_type='join'  THEN 1 ELSE 0 END) AS joins,"
        "  SUM(CASE WHEN event_type='leave' THEN 1 ELSE 0 END) AS leaves "
        "FROM events WHERE chat_id=? GROUP BY day ORDER BY day ASC", (chat_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_raw_timeseries(chat_id):
    return get_timeseries(chat_id)

def get_hourly(chat_id):
    c = _c()
    rows = c.execute(
        "SELECT strftime('%H',created_at) AS hour, COUNT(*) AS total "
        "FROM events WHERE chat_id=? AND event_type='join' "
        "GROUP BY hour ORDER BY hour", (chat_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_weekday(chat_id):
    c = _c()
    rows = c.execute(
        "SELECT strftime('%w',created_at) AS weekday, COUNT(*) AS total "
        "FROM events WHERE chat_id=? AND event_type='join' "
        "GROUP BY weekday ORDER BY weekday", (chat_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_events_page(chat_id, page, size):
    offset = (page-1)*size
    c = _c()
    rows = c.execute(
        "SELECT id,user_id,username,event_type,created_at "
        "FROM events WHERE chat_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (chat_id, size, offset)).fetchall()
    total = c.execute("SELECT COUNT(*) FROM events WHERE chat_id=?",(chat_id,)).fetchone()[0]
    c.close()
    return [dict(r) for r in rows], total

def get_recent(chat_id, limit=10):
    c = _c()
    rows = c.execute(
        "SELECT user_id,username,event_type,created_at "
        "FROM events WHERE chat_id=? ORDER BY created_at DESC LIMIT ?",
        (chat_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def remove_member(chat_id, user_id):
    c = _c()
    c.execute("DELETE FROM members WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    c.commit(); c.close()

def upsert_member(chat_id, user_id, username, full_name, is_admin=False):
    c = _c()
    c.execute(
        "INSERT INTO members(chat_id,user_id,username,full_name,is_admin,last_seen) "
        "VALUES(?,?,?,?,?,datetime('now','-3 hours')) "
        "ON CONFLICT(chat_id,user_id) DO UPDATE SET "
        "username=excluded.username, full_name=excluded.full_name, "
        "is_admin=excluded.is_admin, last_seen=datetime('now','-3 hours')",
        (chat_id, user_id, username, full_name, is_admin)
    )
    c.commit()
    c.close()

def get_members(chat_id):
    c = _c()
    rows = c.execute(
        "SELECT user_id, username, full_name, is_admin, last_seen "
        "FROM members WHERE chat_id=? ORDER BY is_admin DESC, username ASC",
        (chat_id,)
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_member_count(chat_id):
    c = _c()
    row = c.execute(
        "SELECT COUNT(*) as total, "
        "SUM(CASE WHEN is_admin=1 THEN 1 ELSE 0 END) as admins "
        "FROM members WHERE chat_id=?", (chat_id,)
    ).fetchone()
    c.close()
    return dict(row) if row else {"total": 0, "admins": 0}

def replace_member_admins(chat_id, admin_ids):
    admin_ids = [int(uid) for uid in (admin_ids or [])]
    conn = get_connection()
    conn.execute("UPDATE members SET is_admin=0 WHERE chat_id=?", (chat_id,))
    if admin_ids:
        conn.executemany(
            "UPDATE members SET is_admin=1 WHERE chat_id=? AND user_id=?",
            [(chat_id, uid) for uid in admin_ids]
        )
    conn.commit()
    conn.close()

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

def get_finance_transaction(payment_id):
    ensure_finance_schema()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM finance_transactions WHERE payment_id=?",
        (payment_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_finance_transactions(chat_id=None, limit=100):
    ensure_finance_schema()
    conn = get_connection()
    if chat_id is None:
        rows = conn.execute(
            "SELECT * FROM finance_transactions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM finance_transactions WHERE chat_id=? ORDER BY created_at DESC LIMIT ?",
            (chat_id, limit)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_finance_home_metrics(chat_id=None):
    ensure_finance_schema()
    conn = get_connection()
    where_clause = ""
    params = []
    if chat_id is not None:
        where_clause = "WHERE chat_id=?"
        params.append(chat_id)

    paid_statuses = ("paid", "approved", "completed", "success", "succeeded", "delivered")
    paid_placeholders = ",".join("?" for _ in paid_statuses)

    total_revenue = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) FROM finance_transactions {where_clause} AND status IN ({paid_placeholders})" if where_clause else
        f"SELECT COALESCE(SUM(amount), 0) FROM finance_transactions WHERE status IN ({paid_placeholders})",
        params + list(paid_statuses)
    ).fetchone()[0]

    last_24h_total = conn.execute(
        f"SELECT COUNT(*) FROM finance_transactions {where_clause} AND created_at >= datetime('now','-3 hours','-24 hours')" if where_clause else
        "SELECT COUNT(*) FROM finance_transactions WHERE created_at >= datetime('now','-3 hours','-24 hours')",
        params
    ).fetchone()[0]

    last_24h_completed = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM finance_transactions
        {where_clause} AND status IN ({paid_placeholders})
          AND COALESCE(completed_at, updated_at, created_at) >= datetime('now','-3 hours','-24 hours')
        """ if where_clause else
        f"""
        SELECT COUNT(*)
        FROM finance_transactions
        WHERE status IN ({paid_placeholders})
          AND COALESCE(completed_at, updated_at, created_at) >= datetime('now','-3 hours','-24 hours')
        """,
        params + list(paid_statuses)
    ).fetchone()[0]

    week_completed = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM finance_transactions
        {where_clause} AND status IN ({paid_placeholders})
          AND COALESCE(completed_at, updated_at, created_at) >= datetime('now','-3 hours','weekday 1','-7 days')
        """ if where_clause else
        f"""
        SELECT COUNT(*)
        FROM finance_transactions
        WHERE status IN ({paid_placeholders})
          AND COALESCE(completed_at, updated_at, created_at) >= datetime('now','-3 hours','weekday 1','-7 days')
        """,
        params + list(paid_statuses)
    ).fetchone()[0]

    conn.close()
    return {
        "total_revenue": float(total_revenue or 0),
        "transactions_last_24h": int(last_24h_total or 0),
        "approved_last_24h": int(last_24h_completed or 0),
        "approved_this_week": int(week_completed or 0),
    }

def upsert_finance_transaction(tx):
    ensure_finance_schema()
    conn = get_connection()
    payload_json = tx.get("payload_json")
    if payload_json is None:
        payload_json = "{}"
    created_at = tx.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_at = tx.get("updated_at") or created_at
    conn.execute(
        """
        INSERT INTO finance_transactions (
            chat_id, provider, provider_account, payment_id, external_id, amount, status, description,
            customer_name, customer_cpf, customer_email, customer_phone,
            qr_code, qr_image_url, checkout_id, payload_json, expires_at, completed_at, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(payment_id) DO UPDATE SET
            chat_id        = COALESCE(excluded.chat_id, finance_transactions.chat_id),
            provider       = excluded.provider,
            provider_account = COALESCE(NULLIF(excluded.provider_account, ''), finance_transactions.provider_account),
            external_id    = COALESCE(NULLIF(excluded.external_id, ''), finance_transactions.external_id),
            amount         = excluded.amount,
            status         = excluded.status,
            description    = COALESCE(NULLIF(excluded.description, ''), finance_transactions.description),
            customer_name  = COALESCE(NULLIF(excluded.customer_name, ''), finance_transactions.customer_name),
            customer_cpf   = COALESCE(NULLIF(excluded.customer_cpf, ''), finance_transactions.customer_cpf),
            customer_email = COALESCE(NULLIF(excluded.customer_email, ''), finance_transactions.customer_email),
            customer_phone = COALESCE(NULLIF(excluded.customer_phone, ''), finance_transactions.customer_phone),
            qr_code        = COALESCE(NULLIF(excluded.qr_code, ''), finance_transactions.qr_code),
            qr_image_url   = COALESCE(NULLIF(excluded.qr_image_url, ''), finance_transactions.qr_image_url),
            checkout_id    = COALESCE(NULLIF(excluded.checkout_id, ''), finance_transactions.checkout_id),
            payload_json   = COALESCE(NULLIF(excluded.payload_json, ''), finance_transactions.payload_json),
            expires_at     = COALESCE(excluded.expires_at, finance_transactions.expires_at),
            completed_at   = COALESCE(excluded.completed_at, finance_transactions.completed_at),
            created_at     = COALESCE(excluded.created_at, finance_transactions.created_at),
            updated_at     = COALESCE(excluded.updated_at, datetime('now','-3 hours'))
        """,
        (
            tx.get("chat_id"),
            tx.get("provider", "pixgo"),
            tx.get("provider_account", ""),
            tx.get("payment_id"),
            tx.get("external_id", ""),
            float(tx.get("amount") or 0),
            tx.get("status", "pending"),
            tx.get("description", ""),
            tx.get("customer_name", ""),
            tx.get("customer_cpf", ""),
            tx.get("customer_email", ""),
            tx.get("customer_phone", ""),
            tx.get("qr_code", ""),
            tx.get("qr_image_url", ""),
            tx.get("checkout_id", ""),
            payload_json,
            tx.get("expires_at"),
            tx.get("completed_at"),
            created_at,
            updated_at,
        )
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM finance_transactions WHERE payment_id=?",
        (tx.get("payment_id"),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def ensure_default_dashboard_user():
    conn = get_connection()
    ensure_dashboard_user_schema()
    active_admin = conn.execute(
        """
        SELECT id
        FROM dashboard_users
        WHERE role='admin' AND is_active=1
        ORDER BY created_at ASC, id ASC
        LIMIT 1
        """
    ).fetchone()
    if not active_admin:
        candidate = conn.execute(
            """
            SELECT id
            FROM dashboard_users
            WHERE is_active=1
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """
        ).fetchone()
        if candidate:
            conn.execute(
                "UPDATE dashboard_users SET role='admin' WHERE id=?",
                (candidate["id"],),
            )

    legacy_admin = conn.execute(
        "SELECT id FROM dashboard_users WHERE lower(username)='admin'",
    ).fetchone()
    if legacy_admin:
        other_admin = conn.execute(
            """
            SELECT id
            FROM dashboard_users
            WHERE role='admin' AND is_active=1 AND id<>?
            LIMIT 1
            """,
            (legacy_admin["id"],),
        ).fetchone()
        if other_admin:
            conn.execute(
                "UPDATE dashboard_users SET is_active=0 WHERE id=?",
                (legacy_admin["id"],),
            )

    rows = conn.execute("SELECT id FROM dashboard_users").fetchall()
    for row in rows:
        conn.execute(
            """
            INSERT OR IGNORE INTO dashboard_user_preferences(user_id, language, theme_mode, theme_preset, avatar_url, profile_title, profile_bio, motion_level)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (row["id"], "pt", "light", "corporate", "", "", "", "standard"),
        )
    conn.commit()
    conn.close()


def serialize_dashboard_user(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "role": row["role"],
        "is_active": row["is_active"],
        "created_at": row["created_at"],
        "last_login_at": row["last_login_at"],
    }


def get_dashboard_user_by_id(user_id):
    ensure_default_dashboard_user()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, username, display_name, password_hash, role, is_active, created_at, last_login_at
        FROM dashboard_users
        WHERE id=?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_dashboard_user_by_username(username):
    ensure_default_dashboard_user()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, username, display_name, password_hash, role, is_active, created_at, last_login_at
        FROM dashboard_users
        WHERE lower(username)=lower(?)
        """,
        (username.strip(),),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def touch_dashboard_user_login(user_id):
    conn = get_connection()
    conn.execute(
        "UPDATE dashboard_users SET last_login_at=datetime('now','-3 hours') WHERE id=?",
        (user_id,),
    )
    conn.commit()
    conn.close()


def authenticate_dashboard_user(username, password):
    if not username or not password:
        return None
    row = get_dashboard_user_by_username(username)
    if not row or not int(row.get("is_active") or 0):
        return None
    if not row.get("password_hash") or not check_password_hash(row["password_hash"], password):
        return None
    touch_dashboard_user_login(row["id"])
    return serialize_dashboard_user(get_dashboard_user_by_id(row["id"]))


def get_dashboard_users():
    ensure_default_dashboard_user()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, username, display_name, role, is_active, created_at, last_login_at
        FROM dashboard_users
        ORDER BY created_at ASC, id ASC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _slugify_org_name(value):
    raw = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return raw.strip("-") or "workspace"


def get_saas_plans(active_only=False):
    ensure_saas_schema()
    conn = get_connection()
    sql = """
        SELECT code, name, tagline, monthly_price_cents, yearly_price_cents, limits_json, features_json, is_active, sort_order
        FROM saas_plans
    """
    if active_only:
        sql += " WHERE is_active=1"
    sql += " ORDER BY sort_order ASC, monthly_price_cents ASC, code ASC"
    rows = conn.execute(sql).fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item["limits"] = json.loads(item.pop("limits_json") or "{}")
        item["features"] = json.loads(item.pop("features_json") or "[]")
        result.append(item)
    return result


def get_organization_by_id(organization_id):
    ensure_saas_schema()
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name, slug, status, created_at FROM organizations WHERE id=?",
        (organization_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_primary_organization_for_user(user_id):
    ensure_saas_schema()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT o.id, o.name, o.slug, o.status, o.created_at, m.role AS membership_role
        FROM organization_memberships m
        JOIN organizations o ON o.id=m.organization_id
        WHERE m.user_id=?
        ORDER BY CASE m.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END, m.id ASC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def refresh_organization_usage(organization_id):
    ensure_saas_schema()
    conn = get_connection()
    groups_count = conn.execute(
        "SELECT COUNT(*) FROM groups WHERE organization_id=?",
        (organization_id,),
    ).fetchone()[0]
    events_count = conn.execute(
        "SELECT COUNT(*) FROM events WHERE organization_id=? AND created_at >= datetime('now','-3 hours','start of month')",
        (organization_id,),
    ).fetchone()[0]
    automations_count = 0
    tables = {
        row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    if "scheduled_reports" in tables:
        automations_count = conn.execute(
            "SELECT COUNT(*) FROM scheduled_reports WHERE organization_id=? AND active=1",
            (organization_id,),
        ).fetchone()[0]
    integrations_count = 0
    settings_keys = {"meta_access_token", "pixgo_api_key", "smtp_host"}
    if "settings" in tables:
        integrations_count = conn.execute(
            f"SELECT COUNT(*) FROM settings WHERE key IN ({','.join(['?']*len(settings_keys))}) AND trim(COALESCE(value,''))<>''",
            tuple(settings_keys),
        ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO organization_usage_counters(organization_id, groups_count, events_count, automations_count, integrations_count, updated_at)
        VALUES (?,?,?,?,?,datetime('now','-3 hours'))
        ON CONFLICT(organization_id) DO UPDATE SET
            groups_count=excluded.groups_count,
            events_count=excluded.events_count,
            automations_count=excluded.automations_count,
            integrations_count=excluded.integrations_count,
            updated_at=datetime('now','-3 hours')
        """,
        (organization_id, groups_count, events_count, automations_count, integrations_count),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM organization_usage_counters WHERE organization_id=?",
        (organization_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else {
        "organization_id": organization_id,
        "groups_count": 0,
        "events_count": 0,
        "automations_count": 0,
        "integrations_count": 0,
        "updated_at": None,
    }


def get_organization_subscription(organization_id):
    ensure_saas_schema()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT s.id, s.organization_id, s.plan_code, s.billing_cycle, s.status, s.seats,
               s.cancel_at_period_end, s.started_at, s.renews_at, s.trial_ends_at,
               s.stripe_customer_id, s.stripe_subscription_id, s.updated_at,
               p.name AS plan_name, p.tagline AS plan_tagline, p.monthly_price_cents, p.yearly_price_cents,
               p.limits_json, p.features_json
        FROM organization_subscriptions s
        LEFT JOIN saas_plans p ON p.code=s.plan_code
        WHERE s.organization_id=?
        LIMIT 1
        """,
        (organization_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["limits"] = json.loads(data.pop("limits_json") or "{}")
    data["features"] = json.loads(data.pop("features_json") or "[]")
    return data


def update_organization_subscription(organization_id, plan_code, billing_cycle="monthly", status="active", seats=None):
    ensure_saas_schema()
    billing_cycle = "yearly" if str(billing_cycle).strip().lower() == "yearly" else "monthly"
    status = (status or "active").strip().lower()
    plan_codes = {plan["code"] for plan in get_saas_plans(active_only=False)}
    if plan_code not in plan_codes:
        raise ValueError("invalid-plan")
    conn = get_connection()
    if seats is None:
        seats = conn.execute(
            """
            SELECT COUNT(*)
            FROM organization_memberships m
            JOIN dashboard_users u ON u.id=m.user_id
            WHERE m.organization_id=? AND u.is_active=1
            """,
            (organization_id,),
        ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO organization_subscriptions(
            organization_id, plan_code, billing_cycle, status, seats, started_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, datetime('now','-3 hours'), datetime('now','-3 hours'))
        ON CONFLICT(organization_id) DO UPDATE SET
            plan_code=excluded.plan_code,
            billing_cycle=excluded.billing_cycle,
            status=excluded.status,
            seats=excluded.seats,
            updated_at=datetime('now','-3 hours')
        """,
        (organization_id, plan_code, billing_cycle, status, max(1, int(seats or 1))),
    )
    conn.commit()
    conn.close()
    return get_organization_subscription(organization_id)


def get_saas_context_for_user(user_id):
    ensure_saas_schema()
    org = get_primary_organization_for_user(user_id)
    if not org:
        return None
    usage = refresh_organization_usage(org["id"])
    subscription = get_organization_subscription(org["id"])
    limits = dict(subscription.get("limits") or {}) if subscription else {}
    current_features = list(subscription.get("features") or []) if subscription else []
    seats_used = 0
    conn = get_connection()
    seats_used = conn.execute(
        """
        SELECT COUNT(*)
        FROM organization_memberships m
        JOIN dashboard_users u ON u.id=m.user_id
        WHERE m.organization_id=? AND u.is_active=1
        """,
        (org["id"],),
    ).fetchone()[0]
    active_groups = usage.get("groups_count", 0)
    monthly_events = usage.get("events_count", 0)
    active_automations = usage.get("automations_count", 0)
    active_integrations = usage.get("integrations_count", 0)
    conn.close()
    usage_cards = {
        "groups": {"used": active_groups, "limit": limits.get("groups")},
        "events_per_month": {"used": monthly_events, "limit": limits.get("events_per_month")},
        "automations": {"used": active_automations, "limit": limits.get("automations")},
        "team_members": {"used": seats_used, "limit": limits.get("team_members")},
        "integrations": {"used": active_integrations, "limit": limits.get("integrations")},
    }
    return {
        "organization": org,
        "subscription": subscription,
        "usage": usage_cards,
        "features": current_features,
        "feature_access": {feature: True for feature in current_features},
    }


def get_saas_admin_overview():
    ensure_saas_schema()
    conn = get_connection()
    org_count = conn.execute("SELECT COUNT(*) FROM organizations WHERE status='active'").fetchone()[0]
    active_subs = conn.execute(
        "SELECT COUNT(*) FROM organization_subscriptions WHERE status IN ('active','trialing','past_due')"
    ).fetchone()[0]
    paying_rows = conn.execute(
        """
        SELECT s.billing_cycle, p.monthly_price_cents, p.yearly_price_cents
        FROM organization_subscriptions s
        JOIN saas_plans p ON p.code=s.plan_code
        WHERE s.status IN ('active','past_due') AND p.monthly_price_cents > 0
        """
    ).fetchall()
    mrr_cents = 0
    arr_cents = 0
    for row in paying_rows:
        monthly = int(row["monthly_price_cents"] or 0)
        yearly = int(row["yearly_price_cents"] or 0)
        if row["billing_cycle"] == "yearly":
            mrr_cents += int(round(yearly / 12.0))
            arr_cents += yearly
        else:
            mrr_cents += monthly
            arr_cents += monthly * 12
    team_members = conn.execute("SELECT COUNT(*) FROM dashboard_users WHERE is_active=1").fetchone()[0]
    groups_monitored = conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    events_this_month = conn.execute(
        "SELECT COUNT(*) FROM events WHERE created_at >= datetime('now','-3 hours','start of month')"
    ).fetchone()[0]
    conn.close()
    return {
        "organizations": org_count,
        "active_subscriptions": active_subs,
        "mrr_cents": mrr_cents,
        "arr_cents": arr_cents,
        "team_members": team_members,
        "groups_monitored": groups_monitored,
        "events_this_month": events_this_month,
    }


def create_dashboard_user(username, display_name="", password="", role="user"):
    ensure_saas_schema()
    username = (username or "").strip()
    display_name = (display_name or username).strip()
    password = password or ""
    role = "admin" if str(role).strip().lower() == "admin" else "user"
    if not username:
        raise ValueError("username-required")
    if not password:
        raise ValueError("password-required")
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM dashboard_users WHERE lower(username)=lower(?)",
        (username,),
    ).fetchone()
    if existing:
        conn.close()
        raise ValueError("username-exists")
    conn.execute(
        """
        INSERT INTO dashboard_users(username, display_name, password_hash, role, is_active)
        VALUES (?,?,?,?,?)
        """,
        (username, display_name, generate_password_hash(password), role, 1),
    )
    user_id = conn.execute("SELECT id FROM dashboard_users WHERE username=?", (username,)).fetchone()[0]
    conn.execute(
        "INSERT OR IGNORE INTO dashboard_user_preferences(user_id, language, theme_mode, theme_preset) VALUES (?,?,?,?)",
        (user_id, "pt", "light", "corporate"),
    )
    org = get_primary_organization_for_user(1) or {"id": 1}
    membership_role = "owner" if role == "admin" else "member"
    conn.execute(
        """
        INSERT OR IGNORE INTO organization_memberships(organization_id, user_id, role)
        VALUES (?,?,?)
        """,
        (org["id"], user_id, membership_role),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT id, username, display_name, role, is_active, created_at, last_login_at
        FROM dashboard_users WHERE id=?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_dashboard_user(user_id):
    ensure_saas_schema()
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM dashboard_users").fetchone()[0]
    if total <= 1:
        conn.close()
        raise ValueError("last-user")
    current = conn.execute(
        "SELECT role FROM dashboard_users WHERE id=?",
        (user_id,),
    ).fetchone()
    if current and current["role"] == "admin":
        total_admins = conn.execute(
            "SELECT COUNT(*) FROM dashboard_users WHERE role='admin' AND is_active=1"
        ).fetchone()[0]
        if total_admins <= 1:
            conn.close()
            raise ValueError("last-admin")
    conn.execute("DELETE FROM dashboard_user_preferences WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM organization_memberships WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM dashboard_users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def get_dashboard_user_preferences(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT language, theme_mode, theme_preset, avatar_url, profile_title, profile_bio, motion_level, updated_at FROM dashboard_user_preferences WHERE user_id=?",
        (user_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {
            "language": "pt",
            "theme_mode": "light",
            "theme_preset": "corporate",
            "avatar_url": "",
            "profile_title": "",
            "profile_bio": "",
            "motion_level": "standard",
        }
    return dict(row)


def save_dashboard_user_preferences(user_id, language=None, theme_mode=None, theme_preset=None, avatar_url=None, profile_title=None, profile_bio=None, motion_level=None):
    current = get_dashboard_user_preferences(user_id)
    language = (language or current.get("language") or "pt").strip().lower()
    theme_mode = (theme_mode or current.get("theme_mode") or "light").strip().lower()
    theme_preset = (theme_preset or current.get("theme_preset") or "corporate").strip().lower()
    avatar_url = (avatar_url if avatar_url is not None else current.get("avatar_url") or "").strip()
    profile_title = (profile_title if profile_title is not None else current.get("profile_title") or "").strip()
    profile_bio = (profile_bio if profile_bio is not None else current.get("profile_bio") or "").strip()
    motion_level = (motion_level if motion_level is not None else current.get("motion_level") or "standard").strip().lower()
    if motion_level not in {"calm", "standard", "expressive"}:
        motion_level = "standard"
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO dashboard_user_preferences(user_id, language, theme_mode, theme_preset, avatar_url, profile_title, profile_bio, motion_level, updated_at)
        VALUES (?,?,?,?,?,?,?,?,datetime('now','-3 hours'))
        ON CONFLICT(user_id) DO UPDATE SET
            language=excluded.language,
            theme_mode=excluded.theme_mode,
            theme_preset=excluded.theme_preset,
            avatar_url=excluded.avatar_url,
            profile_title=excluded.profile_title,
            profile_bio=excluded.profile_bio,
            motion_level=excluded.motion_level,
            updated_at=datetime('now','-3 hours')
        """,
        (user_id, language, theme_mode, theme_preset, avatar_url[:500], profile_title[:120], profile_bio[:280], motion_level),
    )
    conn.commit()
    conn.close()
    return get_dashboard_user_preferences(user_id)


def create_campaign_source(chat_id, name, source_type="campaign", cost_amount=0, notes=""):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO campaign_sources(chat_id, name, source_type, cost_amount, notes)
        VALUES (?,?,?,?,?)
        """,
        (chat_id, name.strip(), (source_type or "campaign").strip(), float(cost_amount or 0), notes or ""),
    )
    conn.commit()
    conn.close()


def get_campaign_sources(chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM campaign_sources WHERE chat_id=? ORDER BY created_at DESC, id DESC",
        (chat_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_campaign_source(source_id):
    conn = get_connection()
    conn.execute("DELETE FROM campaign_assignments WHERE source_id=?", (source_id,))
    conn.execute("DELETE FROM campaign_sources WHERE id=?", (source_id,))
    conn.commit()
    conn.close()


def assign_campaign_source(chat_id, user_id, source_id):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO campaign_assignments(chat_id, user_id, source_id, assigned_at, created_at)
        VALUES (?,?,?,datetime('now','-3 hours'),datetime('now','-3 hours'))
        ON CONFLICT(chat_id, user_id) DO UPDATE SET
            source_id=excluded.source_id,
            assigned_at=datetime('now','-3 hours')
        """,
        (chat_id, user_id, source_id),
    )
    conn.commit()
    conn.close()


def remove_campaign_assignment(assignment_id):
    conn = get_connection()
    conn.execute("DELETE FROM campaign_assignments WHERE id=?", (assignment_id,))
    conn.commit()
    conn.close()


def get_campaign_assignments(chat_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT ca.id, ca.chat_id, ca.user_id, ca.source_id, ca.assigned_at,
               cs.name AS source_name, cs.source_type, cs.cost_amount,
               m.username, m.full_name, m.is_admin
        FROM campaign_assignments ca
        JOIN campaign_sources cs ON cs.id = ca.source_id
        LEFT JOIN members m ON m.chat_id = ca.chat_id AND m.user_id = ca.user_id
        WHERE ca.chat_id=?
        ORDER BY ca.assigned_at DESC, ca.id DESC
        """,
        (chat_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_campaign_report(chat_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            cs.id,
            cs.name,
            cs.source_type,
            cs.cost_amount,
            cs.notes,
            COUNT(DISTINCT ca.user_id) AS assigned_members,
            COUNT(DISTINCT CASE WHEN e.event_type='join' THEN e.user_id END) AS joined_members,
            COUNT(DISTINCT CASE WHEN e.event_type='leave' THEN e.user_id END) AS left_members
        FROM campaign_sources cs
        LEFT JOIN campaign_assignments ca
          ON ca.source_id = cs.id AND ca.chat_id = cs.chat_id
        LEFT JOIN events e
          ON e.chat_id = ca.chat_id AND e.user_id = ca.user_id
        WHERE cs.chat_id=?
        GROUP BY cs.id, cs.name, cs.source_type, cs.cost_amount, cs.notes
        ORDER BY assigned_members DESC, cs.created_at DESC
        """,
        (chat_id,),
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        members = int(item.get("assigned_members") or 0)
        cost = float(item.get("cost_amount") or 0)
        item["cost_per_member"] = round(cost / members, 2) if members else 0
        result.append(item)
    return result


def get_top_members(chat_id, limit=10):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT username,
               SUM(CASE WHEN event_type='join' THEN 1 ELSE 0 END) AS joins,
               SUM(CASE WHEN event_type='leave' THEN 1 ELSE 0 END) AS leaves,
               COUNT(*) AS total_events
        FROM events
        WHERE chat_id=?
        GROUP BY username
        ORDER BY total_events DESC, joins DESC, username ASC
        LIMIT ?
        """,
        (chat_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_scheduled_reports(chat_id=None):
    conn = get_connection()
    if chat_id is None:
        rows = conn.execute("SELECT * FROM scheduled_reports ORDER BY created_at DESC, id DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scheduled_reports WHERE chat_id=? ORDER BY created_at DESC, id DESC",
            (chat_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_scheduled_report(chat_id, delivery_type, destination, fmt, weekday, hour, minute):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO scheduled_reports(chat_id, delivery_type, destination, format, weekday, hour, minute)
        VALUES (?,?,?,?,?,?,?)
        """,
        (chat_id, delivery_type, destination.strip(), fmt, int(weekday), int(hour), int(minute)),
    )
    conn.commit()
    conn.close()


def delete_scheduled_report(report_id):
    conn = get_connection()
    conn.execute("DELETE FROM scheduled_reports WHERE id=?", (report_id,))
    conn.commit()
    conn.close()


def get_due_scheduled_reports(weekday, hour, minute):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT *
        FROM scheduled_reports
        WHERE active=1
          AND weekday=?
          AND hour=?
          AND minute=?
          AND (
            last_sent_at IS NULL OR
            datetime(last_sent_at) < datetime('now', '-6 days')
          )
        ORDER BY id ASC
        """,
        (int(weekday), int(hour), int(minute)),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_scheduled_report_sent(report_id, error=""):
    conn = get_connection()
    conn.execute(
        "UPDATE scheduled_reports SET last_sent_at=datetime('now','-3 hours'), last_error=? WHERE id=?",
        (error or "", report_id),
    )
    conn.commit()
    conn.close()


def mark_scheduled_report_error(report_id, error):
    conn = get_connection()
    conn.execute(
        "UPDATE scheduled_reports SET last_error=? WHERE id=?",
        (str(error or ""), report_id),
    )
    conn.commit()
    conn.close()
