CREATE TABLE IF NOT EXISTS events (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER  NOT NULL,
    username    TEXT     NOT NULL,
    chat_id     INTEGER  NOT NULL,
    chat_title  TEXT     NOT NULL DEFAULT '',
    event_type  TEXT     NOT NULL CHECK(event_type IN ('join','leave')),
    created_at  DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chat ON events(chat_id);
CREATE INDEX IF NOT EXISTS idx_time ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_type ON events(event_type);

CREATE TABLE IF NOT EXISTS groups (
    chat_id    INTEGER  PRIMARY KEY,
    chat_title TEXT     NOT NULL DEFAULT '',
    first_seen DATETIME NOT NULL DEFAULT (datetime('now')),
    last_event DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS members (
    chat_id   INTEGER  NOT NULL,
    user_id   INTEGER  NOT NULL,
    username  TEXT     NOT NULL DEFAULT '',
    full_name TEXT     NOT NULL DEFAULT '',
    is_admin  INTEGER  NOT NULL DEFAULT 0,
    last_seen DATETIME NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (chat_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_members_chat ON members(chat_id);
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL,
    message    TEXT    NOT NULL,
    send_at    DATETIME NOT NULL,
    sent       INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vault_categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    icon       TEXT NOT NULL DEFAULT '',
    color      TEXT NOT NULL DEFAULT '#58a6ff',
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vault_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    title       TEXT NOT NULL,
    fields      TEXT NOT NULL DEFAULT '[]',
    notes       TEXT NOT NULL DEFAULT '',
    created_at  DATETIME DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_vault_entries_category ON vault_entries(category_id);

CREATE TABLE IF NOT EXISTS vault_access_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id   INTEGER NOT NULL,
    action     TEXT    NOT NULL,
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS finance_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER,
    provider        TEXT    NOT NULL DEFAULT 'pixgo',
    provider_account TEXT   NOT NULL DEFAULT '',
    payment_id      TEXT    NOT NULL UNIQUE,
    external_id     TEXT    NOT NULL DEFAULT '',
    amount          REAL    NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'pending',
    description     TEXT    NOT NULL DEFAULT '',
    customer_name   TEXT    NOT NULL DEFAULT '',
    customer_cpf    TEXT    NOT NULL DEFAULT '',
    customer_email  TEXT    NOT NULL DEFAULT '',
    customer_phone  TEXT    NOT NULL DEFAULT '',
    qr_code         TEXT    NOT NULL DEFAULT '',
    qr_image_url    TEXT    NOT NULL DEFAULT '',
    checkout_id     TEXT    NOT NULL DEFAULT '',
    payload_json    TEXT    NOT NULL DEFAULT '{}',
    expires_at      DATETIME,
    completed_at    DATETIME,
    created_at      DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_finance_chat ON finance_transactions(chat_id);
CREATE INDEX IF NOT EXISTS idx_finance_status ON finance_transactions(status);
CREATE INDEX IF NOT EXISTS idx_finance_created ON finance_transactions(created_at);

CREATE TABLE IF NOT EXISTS dashboard_users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT    NOT NULL UNIQUE,
    display_name TEXT    NOT NULL DEFAULT '',
    password_hash TEXT   NOT NULL DEFAULT '',
    role         TEXT    NOT NULL DEFAULT 'user',
    is_active    INTEGER NOT NULL DEFAULT 1,
    last_login_at DATETIME,
    created_at   DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dashboard_user_preferences (
    user_id       INTEGER PRIMARY KEY,
    language      TEXT    NOT NULL DEFAULT 'pt',
    theme_mode    TEXT    NOT NULL DEFAULT 'light',
    theme_preset  TEXT    NOT NULL DEFAULT 'corporate',
    updated_at    DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS campaign_sources (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id      INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    source_type  TEXT    NOT NULL DEFAULT 'campaign',
    cost_amount  REAL    NOT NULL DEFAULT 0,
    notes        TEXT    NOT NULL DEFAULT '',
    created_at   DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_campaign_sources_chat ON campaign_sources(chat_id);

CREATE TABLE IF NOT EXISTS campaign_assignments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id      INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    source_id    INTEGER NOT NULL,
    assigned_at  DATETIME NOT NULL DEFAULT (datetime('now')),
    created_at   DATETIME NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chat_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_campaign_assignments_chat ON campaign_assignments(chat_id);
CREATE INDEX IF NOT EXISTS idx_campaign_assignments_source ON campaign_assignments(source_id);

CREATE TABLE IF NOT EXISTS scheduled_reports (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id        INTEGER NOT NULL,
    delivery_type  TEXT    NOT NULL CHECK(delivery_type IN ('telegram','email')),
    destination    TEXT    NOT NULL,
    format         TEXT    NOT NULL CHECK(format IN ('pdf','csv')),
    weekday        INTEGER NOT NULL DEFAULT 0,
    hour           INTEGER NOT NULL DEFAULT 9,
    minute         INTEGER NOT NULL DEFAULT 0,
    active         INTEGER NOT NULL DEFAULT 1,
    last_sent_at   DATETIME,
    last_error     TEXT    NOT NULL DEFAULT '',
    created_at     DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_chat ON scheduled_reports(chat_id);
