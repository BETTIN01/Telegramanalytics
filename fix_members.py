# ── 1. Adiciona remove_member no db_service ──────────────────
with open('app/services/db_service.py', encoding='utf-8') as f:
    content = f.read()

if 'def remove_member' not in content:
    content = content.replace(
        'def upsert_member(chat_id, user_id, username, full_name, is_admin=False):',
        '''def remove_member(chat_id, user_id):
    c = _c()
    c.execute("DELETE FROM members WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    c.commit(); c.close()

def upsert_member(chat_id, user_id, username, full_name, is_admin=False):'''
    )
    open('app/services/db_service.py', 'w', encoding='utf-8').write(content)
    print('OK - remove_member adicionado')
else:
    print('remove_member já existe')

# ── 2. Fix do filtro sendo resetado pelo refresh ─────────────
with open('app/static/js/dashboard.js', encoding='utf-8') as f:
    content = f.read()

old = '  renderMembersTable(allMembers);\n}'
new = '''  const q = (el('member-search') && el('member-search').value || '').toLowerCase();
  if (q) {
    renderMembersTable(allMembers.filter(function(m) {
      return (m.username||'').toLowerCase().includes(q) || (m.full_name||'').toLowerCase().includes(q);
    }));
  } else {
    renderMembersTable(allMembers);
  }
}'''

if old in content:
    content = content.replace(old, new)
    open('app/static/js/dashboard.js', 'w', encoding='utf-8').write(content)
    print('OK - filtro preservado no refresh')
else:
    print('Trecho JS não encontrado')