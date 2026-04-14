async function loadMembers() {
  if (!chatId) {
    el('members-body').innerHTML = '<tr><td colspan="5" class="muted" style="padding:20px;text-align:center">Selecione um grupo.</td></tr>';
    el('m-total').textContent = '–';
    el('m-admins').textContent = '–';
    el('m-common').textContent = '–';
    return;
  }
  const data = await api('/api/members/' + chatId);
  allMembers = data.members || [];
  el('m-total').textContent  = data.count.total  || 0;
  el('m-admins').textContent = data.count.admins || 0;
  el('m-common').textContent = (data.count.total || 0) - (data.count.admins || 0);
  renderMembersTable(allMembers);
}

function renderMembersTable(members) {
  const tbody = el('members-body');
  const empty = el('members-empty');
  tbody.innerHTML = '';
  if (!members.length) {
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  members.forEach(function(m, i) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + (i + 1) + '</td>' +
      '<td>@' + (m.username || '–') + '</td>' +
      '<td>' + (m.full_name || '–') + '</td>' +
      '<td>' + (m.is_admin ? '<span style="color:var(--yellow);font-weight:600">⭐ Admin</span>' : '<span class="muted">Membro</span>') + '</td>' +
      '<td class="muted small">' + (m.last_seen ? fmt(m.last_seen) : '–') + '</td>';
    tbody.appendChild(tr);
  });
}

window.filterMembers = function() {
  const q = (el('member-search').value || '').toLowerCase();
  if (!q) { renderMembersTable(allMembers); return; }
  renderMembersTable(allMembers.filter(function(m) {
    return (m.username  || '').toLowerCase().includes(q) ||
           (m.full_name || '').toLowerCase().includes(q);
  }));
};

window.syncMembers = async function() {
  if (!chatId) { showMsg('sync-msg', 'Selecione um grupo primeiro.', false); return; }
  showMsg('sync-msg', 'Sincronizando...', true);
  try {
    const r = await api('/api/members/' + chatId + '/sync', { method: 'POST' });
    showMsg('sync-msg', r.msg, r.ok);
    if (r.ok) await loadMembers();
  } catch(e) { showMsg('sync-msg', 'Erro: ' + e.message, false); }
};