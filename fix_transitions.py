with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

old = '''    if old_status in ("left", "kicked") and new_status == "member":
        record_event(m.id, name, chat_id, chat_title, "join")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[JOIN-CMU] @%s -> %s", name, chat_title)
    elif old_status == "member" and new_status in ("left", "kicked"):
        record_event(m.id, name, chat_id, chat_title, "leave")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)'''

new = '''    JOINED  = {"member", "administrator", "creator"}
    LEFT    = {"left", "kicked"}
    was_in  = old_status in JOINED
    now_in  = new_status in JOINED
    was_out = old_status in LEFT
    now_out = new_status in LEFT

    if was_out and now_in:
        record_event(m.id, name, chat_id, chat_title, "join")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[JOIN-CMU] @%s -> %s", name, chat_title)
    elif was_in and now_out:
        record_event(m.id, name, chat_id, chat_title, "leave")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)
    else:
        log.debug("[SKIP-CMU] %s->%s @%s", old_status, new_status, name)'''

if old in content:
    content = content.replace(old, new)
    open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
    print('OK')
else:
    print('Trecho não encontrado')
    for i, l in enumerate(content.split('\n'), 1):
        if 'old_status' in l:
            print(i, repr(l))