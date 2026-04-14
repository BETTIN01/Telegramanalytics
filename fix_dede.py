import sqlite3
conn = sqlite3.connect('database/analytics.db')
conn.row_factory = sqlite3.Row

# Mostra eventos do Dede
rows = conn.execute("SELECT * FROM events WHERE username='Dede_neto' ORDER BY created_at").fetchall()
for r in rows:
    print(dict(r))

# Remove todos e mantém só o primeiro join
ids = [r['id'] for r in rows]
if len(ids) > 1:
    conn.execute(f"DELETE FROM events WHERE username='Dede_neto' AND id NOT IN ({ids[0]})")
    conn.commit()
    print(f'Removidos {len(ids)-1} eventos duplicados.')
conn.close()