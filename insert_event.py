import sqlite3
conn = sqlite3.connect('database/analytics.db')
conn.execute("""
    INSERT INTO events (user_id, username, chat_id, chat_title, event_type, created_at)
    VALUES (?, ?, ?, ?, 'join', datetime('now'))
""", (
    0,                        # user_id (coloque o real se souber)
    'username_do_usuario',    # username sem @
    -1003677743182,           # chat_id do grupo
    'PRIVATE - Hot Casais Plus 🔞'
))
conn.commit()
conn.close()
print('OK')