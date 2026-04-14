with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

old = '''        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)'''

new = '''        db.remove_member(chat_id, m.id)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)'''

if old in content:
    content = content.replace(old, new)
    open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
    print('OK')
else:
    print('Trecho não encontrado - mostrando linhas com upsert_member:')
    for i, l in enumerate(content.split('\n'), 1):
        if 'upsert_member' in l or 'LEAVE' in l:
            print(i, repr(l))