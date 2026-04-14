import sqlite3
conn = sqlite3.connect('database/analytics.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, username, event_type, created_at FROM events WHERE username='Dede_neto'").fetchall()
for r in rows:
    print(dict(r))

conn.execute("DELETE FROM events WHERE username='Dede_neto'")
conn.commit()
conn.close()
print('OK - todos os eventos do Dede_neto removidos')