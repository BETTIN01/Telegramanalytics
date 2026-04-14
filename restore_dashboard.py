js = r"""'use strict';

let chatId     = null;
let activeView = 'overview';
let activePage = 1;
let timer      = null;
let charts     = {};
let prevJoins  = 0;
let audioCtx   = null;
let allMembers = [];

function el(id) { return document.getElementById(id); }
function fmt(d) { return new Date(d + 'Z').toLocaleString('pt-BR'); }
function fmtT(d) { return new Date(d + 'Z').toLocaleTimeString('pt-BR'); }

function showMsg(elId, text, isOk) {
  const m = el(elId);
  if (!m) return;
  m.textContent = text;
  m.className = 'msg ' + (isOk ? 'ok' : 'err');
}

async function api(path, opts) {
  const r = await fetch(path, opts || {});
  if (!r.ok) throw new Error(r.status + ': ' + r.statusText);
  return r.json();
}

const COPT = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#8b949e', font: { size: 12 } } } },
  scales: {
    x: { ticks: { color:'#8b949e', maxTicksLimit:14 }, grid: { color:'#21262d' } },
    y: { ticks: { color:'#8b949e' }, grid: { color:'#21262d' } }
  }
};

function mkChart(id, type, data, extra) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
  const ctx = document.getElementById(id);
  if (!ctx) return;
  charts[id] = new Chart(ctx.getContext('2d'), {
    type: type, data: data, options: Object.assign({}, COPT, extra || {})
  });
}

async function loadGroups() {
  const groups = await api('/api/groups');
  const sel    = el('group-select');
  const prev   = sel.value;
  sel.innerHTML = '<option value="">— Selecione o grupo —</option>';
  groups.forEach(function(g) {
    const o = document.createElement('option');
    o.value = String(g.chat_id);
    o.text  = g.chat_title || String(g.chat_id);
    sel.appendChild(o);
  });
  if (prev && Array.from(sel.options).some(function(o) { return o.value === prev; })) {
    sel.value = prev;
  } else if (groups.length) {
    sel.value = String(groups[0].chat_id);
    chatId    = String(groups[0].chat_id);
  }
}

async function checkBotStatus() {
  try {
    const s = await api('/api/settings');
    const d = el('bot-status');
    if (s.bot_running) {
      d.className = 'bot-st ok'; d.textContent = 'Bot Ativo';
    } else if (s.token_set) {
      d.className = 'bot-st warn'; d.textContent = 'Bot Parado';
    } else {
      d.className = 'bot-st err'; d.textContent = 'Sem Token';
    }
  } catch(_) {}
}

async function loadOverview() {
  if (!chatId) {
    ['c-joins','c-leaves','c-net','c-churn'].forEach(function(id) { el(id).textContent = '-'; });
    el('insights').innerHTML = '<li>Selecione um grupo.</li>';
    el('feed').innerHTML = '';
    return;
  }
  const results = await Promise.all([
    api('/api/stats/'   + chatId),
    api('/api/reports/' + chatId),
    api('/api/recent/'  + chatId)
  ]);
  const stats = results[0], report = results[1], recent = results[2];
  el('c-joins').textContent  = stats.total_joins  || 0;
  el('c-leaves').textContent = stats.total_leaves || 0;
  const net = stats.net_growth || 0;
  el('c-net').textContent = (net >= 0 ? '+' : '') + net;
  el('c-net').style.color = net >= 0 ? '#3fb950' : '#f85149';
  el('c-churn').textContent = (stats.churn_rate || 0) + '%';
  const ul = el('insights');
  ul.innerHTML = '';
  (report.insights || []).forEach(function(t) {
    const li = document.createElement('li'); li.textContent = t; ul.appendChild(li);
  });
  const feed = el('feed');
  feed.innerHTML = '';
  (recent || []).forEach(function(ev) {
    const li = document.createElement('li');
    li.innerHTML =
      '<span class="badge ' + ev.event_type + '">' + (ev.event_type === 'join' ? 'ENTROU' : 'SAIU') + '</span>' +
      '<span class="feed-user">@' + ev.username + '</span>' +
      '<span class="feed-time">' + fmtT(ev.created_at) + '</span>';
    feed.appendChild(li);
  });
}

async function loadCharts() {
  if (!chatId) return;
  const ts = await api('/api/timeseries/' + chatId);
  if (!ts.labels || !ts.labels.length) return;
  const joins = ts.joins || [], leaves = ts.leaves || [];
  mkChart('chart-line', 'line', {
    labels: ts.labels,
    datasets: [
      { label:'Entradas',     data:joins,         borderColor:'#3fb950', tension:.35, fill:false },
      { label:'Saidas',       data:leaves,        borderColor:'#f85149', tension:.35, fill:false },
      { label:'Entradas MA7', data:ts.joins_ma7,  borderColor:'#58a6ff', borderDash:[5,4], pointRadius:0, tension:.35, fill:false },
      { label:'Saidas MA7',   data:ts.leaves_ma7, borderColor:'#d29922', borderDash:[5,4], pointRadius:0, tension:.35, fill:false }
    ]
  });
  const netArr = joins.map(function(j,i){ return j-(leaves[i]||0); });
  mkChart('chart-bar', 'bar', {
    labels: ts.labels,
    datasets: [{ label:'Crescimento Liquido', data:netArr, borderRadius:4,
      backgroundColor: netArr.map(function(v){ return v>=0?'rgba(63,185,80,.65)':'rgba(248,81,73,.65)'; }) }]
  });
  mkChart('chart-area', 'line', {
    labels: ts.labels,
    datasets: [{ label:'Membros Estimados', data:ts.net_members||[],
      borderColor:'#58a6ff', backgroundColor:'rgba(88,166,255,.13)', tension:.4, fill:true }]
  });
}

async function loadEvents(page) {
  if (!chatId) {
    el('ev-body').innerHTML = '<tr><td colspan="4" style="padding:20px;text-align:center">Selecione um grupo.</td></tr>';
    el('pagination').innerHTML = '';
    return;
  }
  page = page || activePage;
  const data = await api('/api/events/' + chatId + '?page=' + page);
  activePage = data.page;
  const tbody = el('ev-body');
  tbody.innerHTML = '';
  if (!data.events || !data.events.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="padding:20px;text-align:center">Nenhum evento.</td></tr>';
    el('pagination').innerHTML = '';
    return;
  }
  data.events.forEach(function(ev, i) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + ((page-1)*50+i+1) + '</td>' +
      '<td>@' + ev.username + '</td>' +
      '<td style="color:' + (ev.event_type==='join'?'#3fb950':'#f85149') + '">' + (ev.event_type==='join'?'ENTROU':'SAIU') + '</td>' +
      '<td>' + fmt(ev.created_at) + '</td>';
    tbody.appendChild(tr);
  });
  const pg = el('pagination');
  pg.innerHTML = '';
  for (let p = 1; p <= Math.min(data.total_pages||1, 10); p++) {
    const btn = document.createElement('button');
    btn.textContent = p;
    if (p === page) btn.classList.add('current');
    btn.onclick = (function(pp){ return function(){ loadEvents(pp); }; })(p);
    pg.appendChild(btn);
  }
}

async function loadReports() {
  if (!chatId) {
    ['weekly-body','monthly-body'].forEach(function(id){
      el(id).innerHTML = '<tr><td colspan="4" style="padding:16px;text-align:center">Selecione um grupo.</td></tr>';
    });
    el('anomalies').innerHTML = '';
    return;
  }
  const r = await api('/api/reports/' + chatId);
  function fillTable(tbodyId, rows, keys) {
    const tbody = el(tbodyId);
    tbody.innerHTML = '';
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="padding:14px;text-align:center">Sem dados.</td></tr>';
      return;
    }
    rows.forEach(function(row) {
      const tr = document.createElement('tr');
      tr.innerHTML = keys.map(function(k) {
        if (k === 'net') {
          const v = row[k]||0;
          return '<td style="color:'+(v>=0?'#3fb950':'#f85149')+';font-weight:600">'+(v>=0?'+':'')+v+'</td>';
        }
        return '<td>'+(row[k]!==undefined?row[k]:'-')+'</td>';
      }).join('');
      tbody.appendChild(tr);
    });
  }
  fillTable('weekly-body',  r.weekly,  ['week',  'joins','leaves','net']);
  fillTable('monthly-body', r.monthly, ['month', 'joins','leaves','net']);
  const box = el('anomalies');
  box.innerHTML = '';
  (r.spikes||[]).forEach(function(s){
    const d = document.createElement('div');
    d.className = 'anom spike';
    d.innerHTML = '<strong>Pico</strong><br>'+s.day+'<br>'+s.joins+' entradas ('+s.vs_avg+'x media)';
    box.appendChild(d);
  });
  (r.drops||[]).forEach(function(s){
    const d = document.createElement('div');
    d.className = 'anom drop';
    d.innerHTML = '<strong>Queda</strong><br>'+s.day+'<br>'+s.leaves+' saidas vs '+s.joins+' entradas';
    box.appendChild(d);
  });
  if (!box.children.length) box.innerHTML = '<p style="color:#8b949e">Nenhuma anomalia detectada.</p>';
}

async function loadMembers() {
  if (!chatId) {
    el('members-body').innerHTML = '<tr><td colspan="5" class="muted" style="padding:20px;text-align:center">Selecione um grupo.</td></tr>';
    el('m-total').textContent  = '-';
    el('m-admins').textContent = '-';
    el('m-common').textContent = '-';
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
      '<td>@' + (m.username || '-') + '</td>' +
      '<td>' + (m.full_name || '-') + '</td>' +
      '<td>' + (m.is_admin ? '<span style="color:var(--yellow);font-weight:600">Admin</span>' : '<span class="muted">Membro</span>') + '</td>' +
      '<td class="muted small">' + (m.last_seen ? fmt(m.last_seen) : '-') + '</td>';
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

window.syncFull = async function() {
  if (!chatId) { showMsg('sync-msg', 'Selecione um grupo primeiro.', false); return; }
  showMsg('sync-msg', 'Sincronizando todos os membros... pode demorar.', true);
  try {
    const r = await api('/api/members/' + chatId + '/sync-full', { method: 'POST' });
    showMsg('sync-msg', r.msg, r.ok);
    if (r.ok) await loadMembers();
  } catch(e) { showMsg('sync-msg', 'Erro: ' + e.message, false); }
};

async function loadSettings() {
  const s = await api('/api/settings');
  el('inp-token').placeholder = s.token_set ? 'token ja configurado' : '1234567890:ABCdef...';
  renderGroupsTable(s.groups || []);
}

function renderGroupsTable(groups) {
  const tbody = el('groups-body');
  tbody.innerHTML = '';
  if (!groups.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="padding:16px;text-align:center;color:#8b949e">Nenhum grupo monitorado.</td></tr>';
    return;
  }
  groups.forEach(function(g) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td><code>'+g.chat_id+'</code></td>' +
      '<td>'+(g.chat_title||'-')+'</td>' +
      '<td style="color:#8b949e;font-size:12px">'+(g.first_seen?fmt(g.first_seen.replace(' ','T')):'-')+'</td>' +
      '<td style="color:#8b949e;font-size:12px">'+(g.last_event?fmt(g.last_event.replace(' ','T')):'-')+'</td>' +
      '<td><button class="btn-del" onclick="removeGroup('+g.chat_id+')">Remover</button></td>';
    tbody.appendChild(tr);
  });
}

window.toggleTokenVis = function() {
  const inp = el('inp-token');
  inp.type = inp.type === 'password' ? 'text' : 'password';
};

window.saveToken = async function() {
  const token = el('inp-token').value.trim();
  if (!token) { showMsg('token-msg','Digite o token.',false); return; }
  try {
    const r = await api('/api/settings/token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:token})});
    showMsg('token-msg',r.msg,r.ok);
    if (r.ok) { el('inp-token').value=''; await checkBotStatus(); }
  } catch(e) { showMsg('token-msg','Erro: '+e.message,false); }
};

window.restartBot = async function() {
  try {
    const r = await api('/api/settings/bot/restart',{method:'POST'});
    showMsg('token-msg',r.msg,r.ok);
    await checkBotStatus();
  } catch(e) { showMsg('token-msg','Erro: '+e.message,false); }
};

window.stopBot = async function() {
  try {
    const r = await api('/api/settings/bot/stop',{method:'POST'});
    showMsg('token-msg',r.msg,r.ok);
    await checkBotStatus();
  } catch(e) { showMsg('token-msg','Erro: '+e.message,false); }
};

window.addGroup = async function() {
  const cid = el('inp-chatid').value.trim();
  const title = el('inp-title').value.trim();
  if (!cid) { showMsg('group-msg','Digite o chat_id.',false); return; }
  try {
    const r = await api('/api/settings/groups/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:cid,title:title})});
    showMsg('group-msg',r.msg,r.ok);
    if (r.ok) { el('inp-chatid').value=''; el('inp-title').value=''; await loadGroups(); await loadSettings(); }
  } catch(e) { showMsg('group-msg','Erro: '+e.message,false); }
};

window.removeGroup = async function(cid) {
  if (!confirm('Remover grupo '+cid+' e todos os dados?')) return;
  try {
    await api('/api/settings/groups/'+cid,{method:'DELETE'});
    await loadGroups(); await loadSettings();
  } catch(e) { alert('Erro: '+e.message); }
};

// ── COFRE ────────────────────────────────────────────────────
var vaultCatId  = null;
var vaultEditId = null;

async function loadVault() {
  var cats = [];
  try { cats = await api('/api/vault/categories'); } catch(e) { return; }
  var ul = el('vault-cats');
  ul.innerHTML = '';
  if (!cats.length) {
    ul.innerHTML = '<li class="muted" style="padding:12px">Nenhuma categoria.</li>';
    return;
  }
  cats.forEach(function(c) {
    var li   = document.createElement('li');
    li.className = 'vault-cat-item' + (c.id === vaultCatId ? ' active' : '');
    var span = document.createElement('span');
    span.textContent = (c.icon || '') + ' ' + (c.name || '');
    span.onclick = (function(cid,cname){ return function(){ vaultSelectCat(cid,cname); }; })(c.id, c.name||'');
    var btn  = document.createElement('button');
    btn.className   = 'btn-icon-sm';
    btn.textContent = 'X';
    btn.onclick = (function(cid){ return function(){ vaultDeleteCat(cid); }; })(c.id);
    li.appendChild(span); li.appendChild(btn);
    ul.appendChild(li);
  });
}

window.vaultSelectCat = async function(id, name) {
  vaultCatId = id;
  el('vault-cat-title').textContent = name;
  el('btn-new-entry').style.display = '';
  await loadVault();
  var entries = [];
  try { entries = await api('/api/vault/entries/' + id); } catch(e) { return; }
  var box = el('vault-entries');
  box.innerHTML = '';
  if (!entries.length) {
    box.innerHTML = '<p class="muted" style="padding:20px">Nenhuma entrada ainda.</p>';
    return;
  }
  entries.forEach(function(e) {
    var card   = document.createElement('div');
    card.className = 'vault-card';
    var hdr    = document.createElement('div');
    hdr.className  = 'vault-card-header';
    var strong = document.createElement('strong');
    strong.textContent = e.title || '';
    var acts   = document.createElement('div');
    var bEdit  = document.createElement('button');
    bEdit.className   = 'btn-icon-sm';
    bEdit.textContent = 'Editar';
    bEdit.onclick = (function(eid){ return function(){ vaultEditEntry(eid); }; })(e.id);
    var bDel   = document.createElement('button');
    bDel.className   = 'btn-icon-sm';
    bDel.textContent = 'Del';
    bDel.onclick = (function(eid){ return function(){ vaultDeleteEntry(eid); }; })(e.id);
    acts.appendChild(bEdit); acts.appendChild(bDel);
    hdr.appendChild(strong); hdr.appendChild(acts);
    card.appendChild(hdr);
    (e.fields || []).forEach(function(f) {
      var row = document.createElement('div');
      row.className = 'vault-field';
      var lbl = document.createElement('span');
      lbl.className   = 'vault-field-label';
      lbl.textContent = f.label || '';
      var val = document.createElement('span');
      val.className   = 'vault-field-value';
      val.textContent = (f.value || '') + ' [copiar]';
      val.style.cursor = 'pointer';
      val.onclick = (function(v){ return function(){
        navigator.clipboard.writeText(v).then(function(){ alert('Copiado!'); });
      }; })(f.value || '');
      row.appendChild(lbl); row.appendChild(val);
      card.appendChild(row);
    });
    if (e.notes) {
      var p = document.createElement('p');
      p.className   = 'vault-notes';
      p.textContent = e.notes;
      card.appendChild(p);
    }
    box.appendChild(card);
  });
};

window.vaultNewCategory = function() {
  el('vc-name').value  = '';
  el('vc-icon').value  = '';
  el('vc-color').value = '#58a6ff';
  el('vault-cat-modal').style.display = 'flex';
};

window.vaultSaveCat = async function() {
  var name  = el('vc-name').value.trim();
  var icon  = el('vc-icon').value.trim() || '';
  var color = el('vc-color').value       || '#58a6ff';
  if (!name) { alert('Digite um nome.'); return; }
  await api('/api/vault/categories', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name:name, icon:icon, color:color})
  });
  el('vault-cat-modal').style.display = 'none';
  await loadVault();
};

window.vaultDeleteCat = async function(id) {
  if (!confirm('Remover categoria e todas as entradas?')) return;
  await api('/api/vault/categories/' + id, {method:'DELETE'});
  vaultCatId = null;
  el('vault-cat-title').textContent  = 'Selecione uma categoria';
  el('btn-new-entry').style.display  = 'none';
  el('vault-entries').innerHTML      = '<p class="muted" style="padding:20px">Selecione uma categoria.</p>';
  await loadVault();
};

window.vaultNewEntry = function() {
  vaultEditId = null;
  el('vault-modal-title').textContent = 'Nova Entrada';
  el('vm-title').value  = '';
  el('vm-notes').value  = '';
  el('vm-fields').innerHTML = '';
  vaultAddField();
  el('vault-modal').style.display = 'flex';
};

window.vaultEditEntry = async function(id) {
  var entries = [];
  try { entries = await api('/api/vault/entries/' + vaultCatId); } catch(e) { return; }
  var entry = null;
  for (var i=0; i<entries.length; i++) { if (entries[i].id === id) { entry = entries[i]; break; } }
  if (!entry) return;
  vaultEditId = id;
  el('vault-modal-title').textContent = 'Editar Entrada';
  el('vm-title').value = entry.title || '';
  el('vm-notes').value = entry.notes || '';
  el('vm-fields').innerHTML = '';
  (entry.fields || []).forEach(function(f) { vaultAddField(f.label, f.value); });
  el('vault-modal').style.display = 'flex';
};

window.vaultAddField = function(label, value) {
  var div = document.createElement('div');
  div.className = 'vault-field-row';
  var lbl = document.createElement('input');
  lbl.type = 'text'; lbl.placeholder = 'Label'; lbl.className = 'vf-label'; lbl.value = label || '';
  var val = document.createElement('input');
  val.type = 'text'; val.placeholder = 'Valor'; val.className = 'vf-value'; val.value = value || '';
  var btn = document.createElement('button');
  btn.className = 'btn-icon-sm'; btn.textContent = 'X';
  btn.onclick = function() { div.remove(); };
  div.appendChild(lbl); div.appendChild(val); div.appendChild(btn);
  el('vm-fields').appendChild(div);
};

window.vaultCloseModal = function() {
  el('vault-modal').style.display = 'none';
};

window.vaultSaveEntry = async function() {
  var title = el('vm-title').value.trim();
  var notes = el('vm-notes').value.trim();
  if (!title) { alert('Digite um titulo.'); return; }
  var fields = [];
  document.querySelectorAll('.vault-field-row').forEach(function(row) {
    var l = row.querySelector('.vf-label').value.trim();
    var v = row.querySelector('.vf-value').value.trim();
    if (l) fields.push({label:l, value:v});
  });
  var body = {title:title, notes:notes, fields:fields, category_id:vaultCatId};
  if (vaultEditId) {
    await api('/api/vault/entries/'+vaultEditId, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  } else {
    await api('/api/vault/entries', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  }
  el('vault-modal').style.display = 'none';
  await vaultSelectCat(vaultCatId, el('vault-cat-title').textContent);
};

window.vaultDeleteEntry = async function(id) {
  if (!confirm('Remover esta entrada?')) return;
  await api('/api/vault/entries/' + id, {method:'DELETE'});
  await vaultSelectCat(vaultCatId, el('vault-cat-title').textContent);
};
// ── FIM COFRE ────────────────────────────────────────────────

const LOADERS = {
  vault:    loadVault,
  overview: loadOverview,
  charts:   loadCharts,
  events:   loadEvents,
  reports:  loadReports,
  members:  loadMembers,
  settings: loadSettings,
};

async function refresh() {
  try {
    await loadGroups();
    await checkBotStatus();
    if (activeView !== 'settings') await LOADERS[activeView]();
    el('last-refresh').textContent = 'Atualizado ' + new Date().toLocaleTimeString('pt-BR');
  } catch(e) { console.error('refresh error:', e); }
}

document.querySelectorAll('.nav-item').forEach(function(a) {
  a.addEventListener('click', async function(e) {
    e.preventDefault();
    document.querySelectorAll('.nav-item').forEach(function(x){ x.classList.remove('active'); });
    a.classList.add('active');
    activeView = a.dataset.view;
    const spans = a.querySelectorAll('span');
    el('page-title').textContent = spans[spans.length-1].textContent;
    document.querySelectorAll('.view').forEach(function(v){ v.classList.remove('active'); });
    el('view-'+activeView).classList.add('active');
    await LOADERS[activeView]();
  });
});

el('group-select').addEventListener('change', async function(e) {
  chatId     = e.target.value ? e.target.value : null;
  prevJoins  = 0;
  activePage = 1;
  await LOADERS[activeView]();
});

(async function() {
  await refresh();
  timer = setInterval(refresh, 5000);
})();
"""

with open('app/static/js/dashboard.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('dashboard.js restaurado! Tamanho:', len(js))