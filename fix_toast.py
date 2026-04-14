with open('app/static/js/dashboard.js', encoding='utf-8') as f:
    content = f.read()

old = "        if (!data || data.ping) return;\n        const icon  = data.type === 'join' ? '🟢' : '🔴';\n        const label = data.type === 'join' ? 'entrou' : 'saiu';\n        showToast(`${icon} @${data.username} ${label} em ${data.chat_title}`, data.type === 'join' ? 'success' : 'warning', 5000);"

new = "        if (!data || data.ping) return;\n        if (!data.username || !data.chat_title) return;\n        const icon  = data.type === 'join' ? '🟢' : '🔴';\n        const label = data.type === 'join' ? 'entrou' : 'saiu';\n        showToast(`${icon} @${data.username} ${label} em ${data.chat_title}`, data.type === 'join' ? 'success' : 'warning', 5000);"

if old in content:
    content = content.replace(old, new)
    open('app/static/js/dashboard.js', 'w', encoding='utf-8').write(content)
    print('OK')
else:
    print('Trecho não encontrado')