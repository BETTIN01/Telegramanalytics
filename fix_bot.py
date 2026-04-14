with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

# 1. Adicionar import do ChatMemberUpdated handler
content = content.replace(
    'from telegram.ext import Application, MessageHandler, filters, ContextTypes',
    'from telegram.ext import Application, MessageHandler, ChatMemberHandler, filters, ContextTypes'
)

# 2. Adicionar handler function após _on_member
new_handler = '''

async def _on_chat_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    chat_id    = cmu.chat.id
    chat_title = cmu.chat.title or str(chat_id)
    m          = cmu.new_chat_member.user
    old_status = cmu.old_chat_member.status
    new_status = cmu.new_chat_member.status
    if m.is_bot:
        return
    name = m.username or m.first_name or str(m.id)
    full = (m.first_name or "") + (" " + m.last_name if m.last_name else "")
    if old_status in ("left", "kicked") and new_status == "member":
        record_event(m.id, name, chat_id, chat_title, "join")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[JOIN-CMU] @%s -> %s", name, chat_title)
    elif old_status == "member" and new_status in ("left", "kicked"):
        record_event(m.id, name, chat_id, chat_title, "leave")
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)
'''

content = content.replace(
    'def _run_loop(loop):',
    new_handler + '\ndef _run_loop(loop):'
)

# 3. Registrar o novo handler no _boot e permitir chat_member nos allowed_updates
content = content.replace(
    '                    await application.updater.start_polling(\n                        poll_interval=2,\n                        timeout=20,\n                        drop_pending_updates=True,\n                        allowed_updates=["message"],\n                    )',
    '                    await application.updater.start_polling(\n                        poll_interval=2,\n                        timeout=20,\n                        drop_pending_updates=True,\n                        allowed_updates=["message", "chat_member"],\n                    )'
)

content = content.replace(
    '                    application.add_handler(\n                        MessageHandler(\n                            filters.StatusUpdate.NEW_CHAT_MEMBERS |\n                            filters.StatusUpdate.LEFT_CHAT_MEMBER,\n                            _on_member,\n                        )\n                    )',
    '                    application.add_handler(\n                        MessageHandler(\n                            filters.StatusUpdate.NEW_CHAT_MEMBERS |\n                            filters.StatusUpdate.LEFT_CHAT_MEMBER,\n                            _on_member,\n                        )\n                    )\n                    application.add_handler(\n                        ChatMemberHandler(_on_chat_member, ChatMemberHandler.CHAT_MEMBER)\n                    )'
)

with open('app/services/bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK! Verificando handlers registrados...')
for i, l in enumerate(content.split('\n'), 1):
    if 'add_handler' in l or 'allowed_updates' in l:
        print(i, l)