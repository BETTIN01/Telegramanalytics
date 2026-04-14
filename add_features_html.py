html = open('app/templates/index.html', encoding='utf-8').read()

# ── 1. Adiciona meta tema + Inter font no <head> ─────────────
old_head = '<link rel="stylesheet" href="/static/css/dashboard.css"/>'
new_head = '''<link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="/static/css/dashboard.css"/>'''
html = html.replace(old_head, new_head)

# ── 2. Adiciona toast container + breadcrumb no body ─────────
# Insere logo após <body>
old_body = '<div class="layout" id="layout">'
new_body = '''<!-- TOAST CONTAINER -->
<div id="toast-container"></div>

<!-- ALERT BANNER -->
<div id="alert-banner" class="alert-banner" style="display:none"></div>

<div class="layout" id="layout">'''
html = html.replace(old_body, new_body)

# ── 3. Atualiza topbar com breadcrumb + controles ────────────
old_topbar = '''    <header class="topbar">
      <div class="topbar-left">
        <h1 id="page-title">Overview</h1>
      </div>
      <div class="topbar-right">
        <div class="select-wrap">
          <svg class="select-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          <select id="group-select"></select>
        </div>
      </div>
    </header>'''

new_topbar = '''    <header class="topbar">
      <div class="topbar-left">
        <div class="breadcrumb">
          <span class="breadcrumb-root">TG Analytics</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          <span id="page-title">Overview</span>
        </div>
      </div>
      <div class="topbar-right">
        <!-- i18n toggle -->
        <button class="btn-icon topbar-btn" id="lang-toggle" onclick="toggleLang()" title="Idioma">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          <span id="lang-label">PT</span>
        </button>
        <!-- theme toggle -->
        <button class="btn-icon topbar-btn" id="theme-toggle" onclick="toggleTheme()" title="Tema">
          <svg id="theme-icon-dark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          <svg id="theme-icon-light" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="display:none"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        </button>
        <!-- export buttons -->
        <button class="btn-icon topbar-btn" onclick="exportCSV()" title="Exportar CSV">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        </button>
        <button class="btn-icon topbar-btn" onclick="exportPDF()" title="Exportar PDF">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15h6M9 11h3"/></svg>
        </button>
        <!-- group select -->
        <div class="select-wrap">
          <svg class="select-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          <select id="group-select"></select>
        </div>
      </div>
    </header>'''

if old_topbar in html:
    html = html.replace(old_topbar, new_topbar)
    print('✓ Topbar com breadcrumb e controles')
else:
    print('✗ topbar não encontrado')

# ── 4. Adiciona skeleton nos cards ───────────────────────────
old_cards = '''      <div class="cards">
        <div class="card card--green">'''
new_cards = '''      <!-- SKELETON CARDS -->
      <div class="cards skeleton-cards" id="skeleton-cards">
        <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
        <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
        <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
        <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
      </div>
      <div class="cards" id="real-cards" style="display:none">
        <div class="card card--green">'''

old_cards_end = '''        </div>
      </div>
      <div class="two-col">'''
new_cards_end = '''        </div>
      </div>
      </div><!-- /real-cards -->
      <div class="two-col">'''

if old_cards in html:
    html = html.replace(old_cards, new_cards)
    print('✓ Skeleton cards adicionados')
else:
    print('✗ cards não encontrado')

if old_cards_end in html:
    html = html.replace(old_cards_end, new_cards_end, 1)
    print('✓ real-cards fechado')

# ── 5. Adiciona nav items para Scheduler e Logs ──────────────
old_nav_end = '''      <a class="nav-item" data-view="settings" href="#">
        <span class="nav-icon">'''
new_nav_pre = '''      <a class="nav-item" data-view="scheduler" href="#">
        <span class="nav-icon"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><polyline points="12 14 12 18 15 18"/></svg></span>
        <span class="nav-label" data-i18n="nav_scheduler">Agendador</span>
      </a>
      <a class="nav-item" data-view="logs" href="#">
        <span class="nav-icon"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
        <span class="nav-label" data-i18n="nav_logs">Logs</span>
      </a>
      <a class="nav-item" data-view="settings" href="#">
        <span class="nav-icon">'''

if old_nav_end in html:
    html = html.replace(old_nav_end, new_nav_pre, 1)
    print('✓ Nav items Scheduler e Logs adicionados')
else:
    print('✗ nav settings não encontrado')

# ── 6. Adiciona i18n nos nav-labels existentes ───────────────
replacements = [
    ('<span class="nav-label">Overview</span>',       '<span class="nav-label" data-i18n="nav_overview">Overview</span>'),
    ('<span class="nav-label">Gráficos</span>',       '<span class="nav-label" data-i18n="nav_charts">Gráficos</span>'),
    ('<span class="nav-label">Eventos</span>',        '<span class="nav-label" data-i18n="nav_events">Eventos</span>'),
    ('<span class="nav-label">Relatórios</span>',     '<span class="nav-label" data-i18n="nav_reports">Relatórios</span>'),
    ('<span class="nav-label">Membros</span>',        '<span class="nav-label" data-i18n="nav_members">Membros</span>'),
    ('<span class="nav-label">Cofre</span>',          '<span class="nav-label" data-i18n="nav_vault">Cofre</span>'),
    ('<span class="nav-label">Configurações</span>',  '<span class="nav-label" data-i18n="nav_settings">Configurações</span>'),
]
for old, new in replacements:
    html = html.replace(old, new)
print('✓ i18n attrs nos nav-labels')

# ── 7. Adiciona view-scheduler e view-logs antes de </div><!--/content--> ──
scheduler_view = '''
      <!-- SCHEDULER -->
      <section id="view-scheduler" class="view">
        <div class="settings-section">
          <div class="settings-header">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            <span data-i18n="scheduler_title">Agendador de Mensagens</span>
          </div>
          <div class="settings-body">
            <div class="input-row">
              <textarea id="sched-msg" placeholder="Mensagem a enviar..." rows="2" style="flex:1;resize:vertical"></textarea>
            </div>
            <div class="input-row">
              <label style="color:var(--muted);font-size:12px;font-weight:600">Data/Hora:</label>
              <input type="datetime-local" id="sched-dt" style="background:var(--surface2);border:1px solid var(--border2);border-radius:8px;color:var(--text);padding:7px 12px;font-family:inherit;font-size:13px;outline:none"/>
              <button class="btn-primary" onclick="schedAdd()">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span data-i18n="btn_schedule">Agendar</span>
              </button>
            </div>
            <span id="sched-msg-feedback" class="msg"></span>
          </div>
        </div>
        <div class="table-wrap">
          <div class="table-title" data-i18n="sched_queue">Fila de Mensagens</div>
          <table>
            <thead><tr><th>#</th><th data-i18n="col_message">Mensagem</th><th data-i18n="col_date">Data/Hora</th><th data-i18n="col_status">Status</th><th data-i18n="col_action">Ação</th></tr></thead>
            <tbody id="sched-tbody"></tbody>
          </table>
          <div id="sched-empty" style="padding:20px;text-align:center;color:var(--muted);display:none" data-i18n="sched_empty">Nenhuma mensagem agendada.</div>
        </div>
      </section>

      <!-- LOGS -->
      <section id="view-logs" class="view">
        <div class="table-wrap">
          <div class="table-title" style="display:flex;align-items:center;justify-content:space-between">
            <span data-i18n="logs_title">Log do Bot em Tempo Real</span>
            <div style="display:flex;gap:8px">
              <button class="btn-secondary" onclick="clearLogs()" style="padding:4px 12px;font-size:12px" data-i18n="btn_clear_logs">Limpar</button>
              <div class="live-dot"></div>
            </div>
          </div>
          <div id="log-container" class="log-container">
            <div class="log-placeholder" data-i18n="logs_empty">Aguardando logs do bot...</div>
          </div>
        </div>
      </section>
'''

html = html.replace('    </div><!-- /content -->', scheduler_view + '\n    </div><!-- /content -->')
print('✓ Views Scheduler e Logs adicionadas')

# ── 8. Atualiza cofre — adiciona busca global e histórico ────
old_vault_header = '''          <div class="vault-main-header">
            <span id="vault-cat-title">Selecione uma categoria</span>
            <button onclick="vaultNewEntry()" id="btn-new-entry" class="btn-primary" style="display:none">'''
new_vault_header = '''          <div class="vault-toolbar">
            <div class="search-wrap" style="flex:1">
              <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input id="vault-global-search" type="text" placeholder="Busca global no cofre..." oninput="vaultGlobalSearch(this.value)" style="width:100%"/>
            </div>
            <button class="btn-secondary" onclick="showVaultHistory()" style="white-space:nowrap">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              Histórico
            </button>
          </div>
          <div class="vault-main-header">
            <span id="vault-cat-title">Selecione uma categoria</span>
            <button onclick="vaultNewEntry()" id="btn-new-entry" class="btn-primary" style="display:none">'''

if old_vault_header in html:
    html = html.replace(old_vault_header, new_vault_header)
    print('✓ Vault toolbar com busca global e histórico')
else:
    print('✗ vault header não encontrado')

# ── 9. Adiciona modal de gerador de senhas no vault ──────────
old_vault_modal_end = '''      <!-- MODAL CATEGORIA -->'''
new_vault_pw_modal = '''      <!-- MODAL GERADOR DE SENHAS -->
      <div id="vault-pw-modal" class="vault-modal" style="display:none">
        <div class="vault-modal-box" style="max-width:420px">
          <div class="vault-modal-header">
            <span>🔐 Gerador de Senhas</span>
            <button onclick="el('vault-pw-modal').style.display='none'" class="btn-icon">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="vault-modal-body">
            <label>Comprimento</label>
            <div style="display:flex;align-items:center;gap:12px">
              <input type="range" id="pw-len" min="8" max="64" value="20" oninput="pwGenUpdate()" style="flex:1;accent-color:var(--orange)"/>
              <span id="pw-len-val" style="font-weight:700;min-width:28px">20</span>
            </div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:4px">
              <label style="display:flex;align-items:center;gap:6px;text-transform:none;letter-spacing:0;font-size:13px;cursor:pointer">
                <input type="checkbox" id="pw-upper" checked onchange="pwGenUpdate()" style="accent-color:var(--orange)"/> Maiúsculas
              </label>
              <label style="display:flex;align-items:center;gap:6px;text-transform:none;letter-spacing:0;font-size:13px;cursor:pointer">
                <input type="checkbox" id="pw-num" checked onchange="pwGenUpdate()" style="accent-color:var(--orange)"/> Números
              </label>
              <label style="display:flex;align-items:center;gap:6px;text-transform:none;letter-spacing:0;font-size:13px;cursor:pointer">
                <input type="checkbox" id="pw-sym" checked onchange="pwGenUpdate()" style="accent-color:var(--orange)"/> Símbolos
              </label>
            </div>
            <label style="margin-top:10px">Senha Gerada</label>
            <div style="display:flex;gap:8px;align-items:center">
              <input type="text" id="pw-result" readonly style="flex:1;font-family:monospace;font-size:13px;letter-spacing:.5px"/>
              <button class="btn-secondary" onclick="pwGenUpdate()" title="Gerar nova">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              </button>
              <button class="btn-primary" onclick="pwCopy()" title="Copiar">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
            </div>
            <div id="pw-strength" class="pw-strength-bar" style="margin-top:10px">
              <div id="pw-strength-fill" style="height:4px;border-radius:2px;transition:width .3s,background .3s"></div>
            </div>
            <span id="pw-strength-label" style="font-size:11px;color:var(--muted)"></span>
          </div>
          <div class="vault-modal-footer">
            <button onclick="el('vault-pw-modal').style.display='none'" class="btn-secondary">Fechar</button>
            <button onclick="pwUseInField()" class="btn-primary">Usar no campo</button>
          </div>
        </div>
      </div>

      <!-- MODAL HISTÓRICO DO COFRE -->
      <div id="vault-history-modal" class="vault-modal" style="display:none">
        <div class="vault-modal-box" style="max-width:500px">
          <div class="vault-modal-header">
            <span>Histórico de Acessos</span>
            <button onclick="el('vault-history-modal').style.display='none'" class="btn-icon">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="vault-modal-body" style="max-height:50vh;overflow-y:auto">
            <div id="vault-history-list"></div>
          </div>
          <div class="vault-modal-footer">
            <button onclick="el('vault-history-modal').style.display='none'" class="btn-secondary">Fechar</button>
          </div>
        </div>
      </div>

      <!-- MODAL CATEGORIA -->'''

if old_vault_modal_end in html:
    html = html.replace(old_vault_modal_end, new_vault_pw_modal)
    print('✓ Modais gerador de senhas e histórico adicionados')
else:
    print('✗ vault modal end não encontrado')

# ── 10. Adiciona botão de gerador no modal de entrada ────────
old_vm_btn = '''            <button onclick="vaultAddField()" class="btn-add-field">'''
new_vm_btn = '''            <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
              <button onclick="vaultAddField()" class="btn-add-field">'''
old_vm_btn_end = '''              Adicionar campo
            </button>'''
new_vm_btn_end = '''              Adicionar campo
              </button>
              <button type="button" onclick="el('vault-pw-modal').style.display='flex';pwGenUpdate()" class="btn-secondary" style="padding:6px 12px;font-size:12px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>
                Gerar senha
              </button>
            </div>'''

if old_vm_btn in html:
    html = html.replace(old_vm_btn, new_vm_btn)
    html = html.replace(old_vm_btn_end, new_vm_btn_end, 1)
    print('✓ Botão gerar senha no modal de entrada')
else:
    print('✗ btn add field não encontrado')

open('app/templates/index.html', 'w', encoding='utf-8').write(html)
print('\n✅ Bloco 2 (HTML) concluído!')