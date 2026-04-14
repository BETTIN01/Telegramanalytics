import sqlite3
conn = sqlite3.connect('database/analytics.db')
conn.execute(
    "INSERT INTO events (user_id, username, chat_id, chat_title, event_type, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
    (0, 'Calvin', -1003677743182, 'PRIVATE - Hot Casais Plus 🔞', 'join')
)
conn.commit()
conn.close()
print('OK')