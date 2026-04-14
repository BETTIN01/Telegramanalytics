import sqlite3
conn = sqlite3.connect('database/analytics.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT 20").fetchall()
for r in rows:
    print(dict(r))
conn.close()