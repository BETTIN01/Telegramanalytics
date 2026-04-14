with open('app/static/js/dashboard.js', encoding='utf-8') as f:
    content = f.read()

old = '_sseSource = new EventSource(\'/api/alerts/stream\');'
# Acha o bloco onmessage e adiciona guard
content = content.replace(
    "e.data && e.data !== '{}'",
    "e.data && e.data !== '{}' && e.data !== '{\"ping\":true}'"
)

# Protege username e chat_title undefined no alert
content = content.replace(
    'msg = `🟢 @${d.username} entrou em ${d.chat_title}',
    'msg = `🟢 @${d.username || "?"} entrou em ${d.chat_title || "grupo"}'
).replace(
    'msg = `🔴 @${d.username} saiu em ${d.chat_title}',
    'msg = `🔴 @${d.username || "?"} saiu em ${d.chat_title || "grupo"}'
)

open('app/static/js/dashboard.js', 'w', encoding='utf-8').write(content)
print('OK')