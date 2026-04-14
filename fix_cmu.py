with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

old = '''    name = m.username or m.first_name or str(m.id)
    full = (m.first_name or "") + (" " + m.last_name if m.last_name else "")
    if old_status in ("left", "kicked") and new_status == "member":'''

new = '''    name       = m.username or m.first_name or str(m.id)
    full       = (m.first_name or "") + (" " + m.last_name if m.last_name else "")
    chat_title = chat_title or str(chat_id)
    if not name or name == "None":
        return
    if old_status in ("left", "kicked") and new_status == "member":'''

content = content.replace(old, new)
open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
print('OK')