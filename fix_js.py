with open('app/static/js/dashboard.js', encoding='utf-8') as f:
    content = f.read()

old = '''  } else if (groups.length) {
    sel.value = String(groups[0].chat_id);
    chatId    = String(groups[0].chat_id);
  }'''

new = '''  } else if (groups.length) {
    sel.value = String(groups[0].chat_id);
    chatId    = String(groups[0].chat_id);
    loadDashboard();
  }'''

if old in content:
    content = content.replace(old, new)
    open('app/static/js/dashboard.js', 'w', encoding='utf-8').write(content)
    print('OK - loadDashboard() adicionado')
else:
    print('Trecho não encontrado, mostrando linhas 57-65:')
    for i, l in enumerate(content.split('\n')[56:65], 57):
        print(i, repr(l))