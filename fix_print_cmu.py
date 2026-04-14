with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'log.warning("[CMU-DEBUG] @%s: %s -> %s", cmu.new_chat_member.user.username or cmu.new_chat_member.user.id, old_status, new_status)',
    'print(f"[CMU-DEBUG] @{cmu.new_chat_member.user.username or cmu.new_chat_member.user.id}: {old_status} -> {new_status}", flush=True)'
)

open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
print('OK')