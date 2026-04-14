import re

files = {
    'app/services/db_service.py': [
        (
            '"INSERT INTO events(user_id,username,chat_id,chat_title,event_type) "',
            '"INSERT INTO events(user_id,username,chat_id,chat_title,event_type,created_at) "'
        ),
    ],
    'app/routes/api.py': [
        (
            'datetime.utcnow().strftime("%H:%M:%S")',
            '__import__("datetime").datetime.now(__import__("datetime").timezone(__import__("datetime").timedelta(hours=-3))).strftime("%H:%M:%S")'
        ),
    ],
}

# Fix db_service.py — adiciona created_at no INSERT
path = 'app/services/db_service.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

old = (
    '"INSERT INTO events(user_id,username,chat_id,chat_title,event_type) "\n'
    '        "VALUES(?,?,?,?,?)",'
)
new = (
    '"INSERT INTO events(user_id,username,chat_id,chat_title,event_type,created_at) "\n'
    '        "VALUES(?,?,?,?,?,datetime(\'now\',\'-3 hours\'))",'
)
if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ db_service.py corrigido")
else:
    print("⚠️  Trecho não encontrado no db_service.py — mostre as linhas 50-60")

# Fix banco — corrige registros já gravados
import sqlite3
conn = sqlite3.connect('database/analytics.db')
affected = conn.execute(
    "UPDATE events SET created_at = datetime(created_at, '-3 hours') WHERE created_at > '2026-01-01'"
).rowcount
conn.commit()
conn.close()
print(f"✅ {affected} eventos corrigidos no banco")