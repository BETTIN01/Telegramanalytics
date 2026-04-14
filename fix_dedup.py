with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

# Adiciona cache de deduplicação após os imports
old = 'log = logging.getLogger(__name__)'
new = '''log = logging.getLogger(__name__)

# Deduplicação: evita registrar o mesmo evento 2x em 10 segundos
_event_cache = {}
_cache_lock  = threading.Lock()

def _is_duplicate(user_id, event_type):
    key = (user_id, event_type)
    now = time.time()
    with _cache_lock:
        last = _event_cache.get(key, 0)
        if now - last < 10:
            return True
        _event_cache[key] = now
        return False'''

content = content.replace(old, new)

# Adiciona checagem antes de registrar no _on_chat_member
old2 = '''    if was_out and now_in:
        record_event(m.id, name, chat_id, chat_title, "join")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[JOIN-CMU] @%s -> %s", name, chat_title)
    elif was_in and now_out:
        record_event(m.id, name, chat_id, chat_title, "leave")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)'''

new2 = '''    if was_out and now_in:
        if _is_duplicate(m.id, "join"): return
        record_event(m.id, name, chat_id, chat_title, "join")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[JOIN-CMU] @%s -> %s", name, chat_title)
    elif was_in and now_out:
        if _is_duplicate(m.id, "leave"): return
        record_event(m.id, name, chat_id, chat_title, "leave")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)'''

if old2 in content:
    content = content.replace(old2, new2)
    open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
    print('OK - deduplicador adicionado')
else:
    print('Trecho não encontrado')