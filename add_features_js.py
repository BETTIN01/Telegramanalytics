js_extra = r"""

// ═══════════════════════════════════════════════════════════
// BLOCO 3 — NOVAS FUNCIONALIDADES
// ═══════════════════════════════════════════════════════════

// ── i18n ────────────────────────────────────────────────────
const LANGS = {
  'pt': {
    nav_overview:'Overview', nav_charts:'Gráficos', nav_events:'Eventos',
    nav_reports:'Relatórios', nav_members:'Membros', nav_vault:'Cofre',
    nav_settings:'Configurações', nav_scheduler:'Agendador', nav_logs:'Logs',
    scheduler_title:'Agendador de Mensagens', sched_queue:'Fila de Mensagens',
    sched_empty:'Nenhuma mensagem agendada.',
    btn_schedule:'Agendar', btn_clear_logs:'Limpar',
    col_message:'Mensagem', col_date:'Data/Hora', col_status:'Status', col_action:'Ação',
    logs_title:'Log do Bot em Tempo Real', logs_empty:'Aguardando logs do bot...',
    overview_title:'Overview', charts_title:'Gráficos', events_title:'Eventos',
    reports_title:'Relatórios', members_title:'Membros', vault_title:'Cofre',
    settings_title:'Configurações', scheduler_page:'Agendador', logs_page:'Logs',
  },
  'en': {
    nav_overview:'Overview', nav_charts:'Charts', nav_events:'Events',
    nav_reports:'Reports', nav_members:'Members', nav_vault:'Vault',
    nav_settings:'Settings', nav_scheduler:'Scheduler', nav_logs:'Logs',
    scheduler_title:'Message Scheduler', sched_queue:'Message Queue',
    sched_empty:'No scheduled messages.',
    btn_schedule:'Schedule', btn_clear_logs:'Clear',
    col_message:'Message', col_date:'Date/Time', col_status:'Status', col_action:'Action',
    logs_title:'Bot Log (Live)', logs_empty:'Waiting for bot logs...',
    overview_title:'Overview', charts_title:'Charts', events_title:'Events',
    reports_title:'Reports', members_title:'Members', vault_title:'Vault',
    settings_title:'Settings', scheduler_page:'Scheduler', logs_page:'Logs',
  }
};

let currentLang = localStorage.getItem('lang') || 'pt';

function applyLang() {
  const t = LANGS[currentLang];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
  });
  const lbl = document.getElementById('lang-label');
  if (lbl) lbl.textContent = currentLang === 'pt' ? 'PT' : 'EN';
}

function toggleLang() {
  currentLang = currentLang === 'pt' ? 'en' : 'pt';
  localStorage.setItem('lang', currentLang);
  applyLang();
  showToast(currentLang === 'pt' ? 'Idioma: Português' : 'Language: English', 'info');
}

// ── Tema claro/escuro ────────────────────────────────────────
let currentTheme = localStorage.getItem('theme') || 'dark';

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const dark  = document.getElementById('theme-icon-dark');
  const light = document.getElementById('theme-icon-light');
  if (dark)  dark.style.display  = theme === 'dark'  ? 'block' : 'none';
  if (light) light.style.display = theme === 'light' ? 'block' : 'none';
  localStorage.setItem('theme', theme);
  currentTheme = theme;
}

function toggleTheme() {
  applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
  showToast(currentTheme === 'dark' ? '☀️ Tema claro ativado' : '🌙 Tema escuro ativado', 'info');
}

// ── Toast ────────────────────────────────────────────────────
function showToast(msg, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  const icons = {
    success: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    warning: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    info:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  };
  toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span class="toast-msg">${msg}</span><button class="toast-close" onclick="this.parentElement.remove()">×</button>`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    setTimeout(() => toast.remove(), 350);
  }, duration);
}

// ── Skeleton loading ─────────────────────────────────────────
function showSkeleton() {
  const sk = document.getElementById('skeleton-cards');
  const rc = document.getElementById('real-cards');
  if (sk) sk.style.display = 'grid';
  if (rc) rc.style.display = 'none';
}

function hideSkeleton() {
  const sk = document.getElementById('skeleton-cards');
  const rc = document.getElementById('real-cards');
  if (sk) sk.style.display = 'none';
  if (rc) rc.style.display = 'grid';
}

// ── SSE Alertas em tempo real ────────────────────────────────
let _sseSource = null;

function startSSE() {
  if (_sseSource) return;
  try {
    _sseSource = new EventSource('/api/alerts/stream');
    _sseSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (!data || data.ping) return;
        const icon  = data.type === 'join' ? '🟢' : '🔴';
        const label = data.type === 'join' ? 'entrou' : 'saiu';
        showToast(`${icon} @${data.username} ${label} em ${data.chat_title}`, data.type === 'join' ? 'success' : 'warning', 5000);
        // atualiza feed se estiver na overview
        if (activeView === 'overview') loadOverview();
      } catch(err) {}
    };
    _sseSource.onerror = () => {
      _sseSource = null;
      setTimeout(startSSE, 5000);
    };
  } catch(e) {}
}

// ── Export CSV/PDF ───────────────────────────────────────────
function exportCSV() {
  if (!currentChatId) { showToast('Selecione um grupo primeiro', 'warning'); return; }
  window.open(`/api/export/csv/${currentChatId}`, '_blank');
  showToast('CSV exportado!', 'success');
}

function exportPDF() {
  if (!currentChatId) { showToast('Selecione um grupo primeiro', 'warning'); return; }
  showToast('Gerando PDF...', 'info');
  window.open(`/api/export/pdf/${currentChatId}`, '_blank');
}

// ── Scheduler ────────────────────────────────────────────────
async function loadScheduler() {
  const tbody = document.getElementById('sched-tbody');
  const empty = document.getElementById('sched-empty');
  if (!tbody) return;
  try {
    const url  = currentChatId ? `/api/scheduler?chat_id=${currentChatId}` : '/api/scheduler';
    const rows = await api(url);
    tbody.innerHTML = '';
    if (!rows.length) {
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    rows.forEach((r, i) => {
      const tr = document.createElement('tr');
      const status = r.sent ? '<span style="color:var(--green);font-weight:600">✓ Enviado</span>' : '<span style="color:var(--yellow);font-weight:600">⏳ Pendente</span>';
      tr.innerHTML = `
        <td>${i+1}</td>
        <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.message}</td>
        <td style="white-space:nowrap">${r.send_at}</td>
        <td>${status}</td>
        <td><button class="btn-del" onclick="schedDelete(${r.id})">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
        </button></td>`;
      tbody.appendChild(tr);
    });
  } catch(e) { showToast('Erro ao carregar agendamentos', 'error'); }
}

async function schedAdd() {
  const msg = document.getElementById('sched-msg').value.trim();
  const dt  = document.getElementById('sched-dt').value;
  const fb  = document.getElementById('sched-msg-feedback');
  if (!currentChatId) { showToast('Selecione um grupo', 'warning'); return; }
  if (!msg)  { showToast('Digite uma mensagem', 'warning'); return; }
  if (!dt)   { showToast('Selecione data/hora', 'warning'); return; }
  try {
    await fetch('/api/scheduler', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ chat_id: currentChatId, message: msg, send_at: dt })
    });
    document.getElementById('sched-msg').value = '';
    document.getElementById('sched-dt').value  = '';
    showToast('Mensagem agendada!', 'success');
    await loadScheduler();
  } catch(e) { showToast('Erro ao agendar', 'error'); }
}

async function schedDelete(id) {
  await fetch(`/api/scheduler/${id}`, { method: 'DELETE' });
  showToast('Agendamento removido', 'info');
  await loadScheduler();
}

// ── Bot logs ─────────────────────────────────────────────────
let _logInterval = null;

async function loadLogs() {
  try {
    const logs = await api('/api/bot/logs');
    const box  = document.getElementById('log-container');
    if (!box) return;
    if (!logs.length) {
      box.innerHTML = '<div class="log-placeholder">Aguardando logs do bot...</div>';
      return;
    }
    const wasBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 30;
    box.innerHTML = logs.map(l =>
      `<div class="log-line"><span class="log-time">${l.time}</span><span class="log-msg">${escHtml(l.msg)}</span></div>`
    ).join('');
    if (wasBottom) box.scrollTop = box.scrollHeight;
  } catch(e) {}
}

function clearLogs() {
  const box = document.getElementById('log-container');
  if (box) box.innerHTML = '<div class="log-placeholder">Log limpo.</div>';
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Gerador de senhas ─────────────────────────────────────────
let _pwTargetField = null;

function pwGenUpdate() {
  const len   = parseInt(document.getElementById('pw-len').value);
  const upper = document.getElementById('pw-upper').checked;
  const num   = document.getElementById('pw-num').checked;
  const sym   = document.getElementById('pw-sym').checked;
  document.getElementById('pw-len-val').textContent = len;

  let chars = 'abcdefghijklmnopqrstuvwxyz';
  if (upper) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  if (num)   chars += '0123456789';
  if (sym)   chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';

  let pw = '';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  arr.forEach(v => pw += chars[v % chars.length]);

  document.getElementById('pw-result').value = pw;

  // força meter
  const score = (upper?1:0)+(num?1:0)+(sym?1:0)+(len>=16?1:0)+(len>=24?1:0);
  const colors = ['#ef4444','#f59e0b','#f59e0b','#22c55e','#22c55e'];
  const labels = ['Muito fraca','Fraca','Média','Forte','Muito forte'];
  const fill   = document.getElementById('pw-strength-fill');
  const label  = document.getElementById('pw-strength-label');
  if (fill)  { fill.style.width = `${(score/5)*100}%`; fill.style.background = colors[score-1]||'#ef4444'; }
  if (label) label.textContent = labels[score-1] || 'Muito fraca';
}

function pwCopy() {
  const val = document.getElementById('pw-result').value;
  if (!val) return;
  navigator.clipboard.writeText(val).then(() => showToast('Senha copiada!', 'success'));
}

function pwUseInField() {
  const val = document.getElementById('pw-result').value;
  if (!val) return;
  // Coloca no último campo de valor focado no modal de entrada
  const fields = document.querySelectorAll('#vm-fields input[type=text]');
  if (fields.length) {
    fields[fields.length-1].value = val;
    showToast('Senha inserida no campo!', 'success');
  }
  el('vault-pw-modal').style.display = 'none';
}

// ── Vault busca global ───────────────────────────────────────
function vaultGlobalSearch(q) {
  q = q.toLowerCase().trim();
  const cards = document.querySelectorAll('#vault-entries .vault-card');
  if (!q) { cards.forEach(c => c.style.display = ''); return; }
  cards.forEach(c => {
    const text = c.textContent.toLowerCase();
    c.style.display = text.includes(q) ? '' : 'none';
  });
}

// ── Vault histórico ──────────────────────────────────────────
async function showVaultHistory() {
  try {
    const logs = await api('/api/vault/access_log');
    const box  = document.getElementById('vault-history-list');
    if (!box) return;
    if (!logs.length) {
      box.innerHTML = '<p style="color:var(--muted);padding:10px">Nenhum acesso registrado.</p>';
    } else {
      box.innerHTML = logs.map(l =>
        `<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--border);font-size:13px">
          <span>${escHtml(l.action)}</span>
          <span style="color:var(--muted);font-size:11px">${l.created_at}</span>
        </div>`
      ).join('');
    }
    el('vault-history-modal').style.display = 'flex';
  } catch(e) { showToast('Erro ao carregar histórico', 'error'); }
}

// ── Hook no vaultCopyField para logar acesso ─────────────────
const _origCopy = window.vaultCopyField;
if (typeof vaultCopyField === 'function') {
  window.vaultCopyField = function(val, label, entryId) {
    if (entryId) fetch('/api/vault/access_log', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ entry_id: entryId, action: `Copiou campo "${label}"` })
    });
    navigator.clipboard.writeText(val).then(() => showToast(`"${label}" copiado!`, 'success'));
  };
}

// ── Dispatcher atualizado ─────────────────────────────────────
const _extraLoaders = {
  scheduler: loadScheduler,
  logs: loadLogs,
};

// ── Override da navegação para incluir novas views ────────────
document.querySelectorAll('.nav-item').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active'));
    a.classList.add('active');

    const view = a.dataset.view;
    activeView = view;

    const t = LANGS[currentLang];
    const titleKey = view + '_title';
    const titleEl  = document.getElementById('page-title');
    if (titleEl) titleEl.textContent = t[titleKey] || view.charAt(0).toUpperCase() + view.slice(1);

    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const viewEl = document.getElementById(`view-${view}`);
    if (viewEl) viewEl.classList.add('active');

    // Para logs, inicia polling
    if (view === 'logs') {
      if (_logInterval) clearInterval(_logInterval);
      await loadLogs();
      _logInterval = setInterval(loadLogs, 2000);
    } else {
      if (_logInterval) { clearInterval(_logInterval); _logInterval = null; }
    }

    if (_extraLoaders[view]) await _extraLoaders[view]();
    else await refreshAll();
  });
});

// ── Boot extras ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  applyTheme(currentTheme);
  applyLang();
  startSSE();
  pwGenUpdate();
});
"""

js_path = 'app/static/js/dashboard.js'
js = open(js_path, encoding='utf-8').read()

if 'showToast' not in js:
    open(js_path, 'a', encoding='utf-8').write(js_extra)
    print('✅ Bloco 3 (JavaScript) aplicado!')
else:
    print('⚠ já aplicado anteriormente')