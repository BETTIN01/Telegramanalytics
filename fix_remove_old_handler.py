with open('app/services/bot_service.py', encoding='utf-8') as f:
    content = f.read()

old = '''                    application.add_handler(
                        MessageHandler(
                            filters.StatusUpdate.NEW_CHAT_MEMBERS |
                            filters.StatusUpdate.LEFT_CHAT_MEMBER,
                            _on_member,
                        )
                    )
                    application.add_handler(
                        ChatMemberHandler(_on_chat_member, ChatMemberHandler.CHAT_MEMBER)
                    )'''

new = '''                    application.add_handler(
                        ChatMemberHandler(_on_chat_member, ChatMemberHandler.CHAT_MEMBER)
                    )'''

if old in content:
    content = content.replace(old, new)
    open('app/services/bot_service.py', 'w', encoding='utf-8').write(content)
    print('OK - MessageHandler removido, só ChatMemberHandler ativo')
else:
    print('Trecho não encontrado')
    for i, l in enumerate(content.split('\n'), 1):
        if 'add_handler' in l:
            print(i, repr(l))