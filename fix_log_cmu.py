with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

old = '    old_status = cmu.old_chat_member.status\n    new_status = cmu.new_chat_member.status'
new = '    old_status = cmu.old_chat_member.status\n    new_status = cmu.new_chat_member.status\n    log.warning("[CMU-DEBUG] @%s: %s -> %s", cmu.new_chat_member.user.username or cmu.new_chat_member.user.id, old_status, new_status)'

content = content.replace(old, new)
open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
print('OK')