# ─── HTML ────────────────────────────────────────────────────
html = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>TG Analytics</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="/static/css/dashboard.css"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
<div class="layout" id="layout">

  <!-- SIDEBAR -->
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-top">
      <div class="logo">
        <div class="logo-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 1.27h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.82a16 16 0 0 0 6.26 6.27l.95-.95a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        </div>
        <span class="logo-text">TG Analytics</span>
      </div>
      <button class="sidebar-toggle" id="sidebar-toggle" title="Minimizar sidebar" onclick="toggleSidebar()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      </button>
    </div>

    <nav class="nav">
      <a class="nav-item active" data-view="overview"  href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg></span>
        <span class="nav-label">Overview</span>
      </a>
      <a class="nav-item" data-view="charts" href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></span>
        <span class="nav-label">Gráficos</span>
      </a>
      <a class="nav-item" data-view="events" href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></span>
        <span class="nav-label">Eventos</span>
      </a>
      <a class="nav-item" data-view="reports" href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></span>
        <span class="nav-label">Relatórios</span>
      </a>
      <a class="nav-item" data-view="members" href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>
        <span class="nav-label">Membros</span>
      </a>
      <div class="nav-divider"></div>
      <a class="nav-item" data-view="vault" href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
        <span class="nav-label">Cofre</span>
      </a>
      <a class="nav-item" data-view="settings" href="#">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg></span>
        <span class="nav-label">Configurações</span>
      </a>
    </nav>

    <div class="sidebar-footer">
      <div id="bot-status" class="bot-st">...</div>
      <span id="last-refresh" class="refresh-time"></span>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main">
    <header class="topbar">
      <div class="topbar-left">
        <h1 id="page-title">Overview</h1>
      </div>
      <div class="topbar-right">
        <div class="select-wrap">
          <svg class="select-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          <select id="group-select"></select>
        </div>
      </div>
    </header>

    <div class="content">

      <!-- OVERVIEW -->
      <section id="view-overview" class="view active">
        <div class="cards">
          <div class="card card--green">
            <div class="card-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg></div>
            <div class="card-label">Entradas</div>
            <div class="card-value" id="c-joins">–</div>
          </div>
          <div class="card card--red">
            <div class="card-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="23" y1="11" x2="17" y2="11"/></svg></div>
            <div class="card-label">Saídas</div>
            <div class="card-value" id="c-leaves">–</div>
          </div>
          <div class="card card--blue">
            <div class="card-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></div>
            <div class="card-label">Crescimento</div>
            <div class="card-value" id="c-net">–</div>
          </div>
          <div class="card card--yellow">
            <div class="card-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>
            <div class="card-label">Churn</div>
            <div class="card-value" id="c-churn">–</div>
          </div>
        </div>
        <div class="two-col">
          <div class="panel">
            <div class="panel-header">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              Insights
            </div>
            <div class="panel-body"><ul id="insights"></ul></div>
          </div>
          <div class="panel">
            <div class="panel-header">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Feed Recente
            </div>
            <div class="panel-body"><ul id="feed"></ul></div>
          </div>
        </div>
      </section>

      <!-- CHARTS -->
      <section id="view-charts" class="view">
        <div class="chart-wrap"><div class="chart-title">Entradas e Saídas</div><div style="height:240px"><canvas id="chart-line"></canvas></div></div>
        <div class="chart-wrap"><div class="chart-title">Crescimento Líquido</div><div style="height:200px"><canvas id="chart-bar"></canvas></div></div>
        <div class="chart-wrap"><div class="chart-title">Membros Estimados</div><div style="height:200px"><canvas id="chart-area"></canvas></div></div>
      </section>

      <!-- EVENTS -->
      <section id="view-events" class="view">
        <div class="table-wrap">
          <div class="table-title">Eventos</div>
          <table><thead><tr><th>#</th><th>Usuário</th><th>Tipo</th><th>Data</th></tr></thead><tbody id="ev-body"></tbody></table>
          <div id="pagination" class="pagination"></div>
        </div>
      </section>

      <!-- REPORTS -->
      <section id="view-reports" class="view">
        <div class="table-wrap"><div class="table-title">Semanal</div><table><thead><tr><th>Semana</th><th>Entradas</th><th>Saídas</th><th>Líquido</th></tr></thead><tbody id="weekly-body"></tbody></table></div>
        <div class="table-wrap"><div class="table-title">Mensal</div><table><thead><tr><th>Mês</th><th>Entradas</th><th>Saídas</th><th>Líquido</th></tr></thead><tbody id="monthly-body"></tbody></table></div>
        <div class="panel"><div class="panel-header">Anomalias</div><div class="panel-body"><div id="anomalies"></div></div></div>
      </section>

      <!-- MEMBERS -->
      <section id="view-members" class="view">
        <div class="members-bar">
          <div class="members-stats">
            <div class="stat-item"><span class="val" id="m-total">–</span><span class="lbl">Total</span></div>
            <div class="stat-item"><span class="val" id="m-admins" style="color:var(--yellow)">–</span><span class="lbl">Admins</span></div>
            <div class="stat-item"><span class="val" id="m-common">–</span><span class="lbl">Membros</span></div>
          </div>
          <div class="members-actions">
            <div class="search-wrap">
              <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input id="member-search" type="text" placeholder="Buscar membro..." oninput="filterMembers()"/>
            </div>
            <button class="btn-secondary" onclick="syncMembers()">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              Sincronizar
            </button>
            <button class="btn-primary" onclick="syncFull()">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Sync Completo
            </button>
            <span id="sync-msg" class="msg"></span>
          </div>
        </div>
        <div class="table-wrap">
          <table><thead><tr><th>#</th><th>Username</th><th>Nome</th><th>Tipo</th><th>Último acesso</th></tr></thead><tbody id="members-body"></tbody></table>
          <div id="members-empty" style="display:none;padding:24px;text-align:center;color:var(--muted)">Nenhum membro encontrado.</div>
        </div>
      </section>

      <!-- VAULT -->
      <section id="view-vault" class="view">
        <div class="vault-layout">
          <div class="vault-sidebar">
            <div class="vault-sidebar-header">
              <span>Categorias</span>
              <button onclick="vaultNewCategory()" class="btn-icon" title="Nova categoria">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>
            <ul id="vault-cats" class="vault-cats"></ul>
          </div>
          <div class="vault-main">
            <div class="vault-main-header">
              <span id="vault-cat-title">Selecione uma categoria</span>
              <button onclick="vaultNewEntry()" id="btn-new-entry" class="btn-primary" style="display:none">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Nova entrada
              </button>
            </div>
            <div id="vault-entries" class="vault-entries">
              <p class="muted" style="padding:20px">Selecione uma categoria à esquerda.</p>
            </div>
          </div>
        </div>

        <!-- MODAL ENTRADA -->
        <div id="vault-modal" class="vault-modal" style="display:none">
          <div class="vault-modal-box">
            <div class="vault-modal-header">
              <span id="vault-modal-title">Nova Entrada</span>
              <button onclick="vaultCloseModal()" class="btn-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="vault-modal-body">
              <label>Título</label>
              <input id="vm-title" type="text" placeholder="Ex: Gmail principal"/>
              <label>Campos</label>
              <div id="vm-fields"></div>
              <button onclick="vaultAddField()" class="btn-add-field">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Adicionar campo
              </button>
              <label>Notas</label>
              <textarea id="vm-notes" placeholder="Observações..." rows="3"></textarea>
            </div>
            <div class="vault-modal-footer">
              <button onclick="vaultCloseModal()" class="btn-secondary">Cancelar</button>
              <button onclick="vaultSaveEntry()" class="btn-primary">Salvar</button>
            </div>
          </div>
        </div>

        <!-- MODAL CATEGORIA -->
        <div id="vault-cat-modal" class="vault-modal" style="display:none">
          <div class="vault-modal-box" style="max-width:380px">
            <div class="vault-modal-header">
              <span>Nova Categoria</span>
              <button onclick="el('vault-cat-modal').style.display='none'" class="btn-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="vault-modal-body">
              <label>Nome</label>
              <input id="vc-name" type="text" placeholder="Ex: Redes Sociais"/>
              <label>Ícone (emoji)</label>
              <input id="vc-icon" type="text" placeholder="🔑" style="width:90px"/>
              <label>Cor</label>
              <input id="vc-color" type="color" value="#6366f1" style="width:60px;height:36px;padding:2px;border-radius:8px"/>
            </div>
            <div class="vault-modal-footer">
              <button onclick="el('vault-cat-modal').style.display='none'" class="btn-secondary">Cancelar</button>
              <button onclick="window.vaultSaveCat()" class="btn-primary">Criar</button>
            </div>
          </div>
        </div>
      </section>

      <!-- SETTINGS -->
      <section id="view-settings" class="view">
        <div class="settings-section">
          <div class="settings-header">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 1.27h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.82a16 16 0 0 0 6.26 6.27l.95-.95a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            Token do Bot
          </div>
          <div class="settings-body">
            <div class="input-row">
              <input id="inp-token" type="password" placeholder="token ja configurado" style="flex:1"/>
              <button class="btn-icon" onclick="toggleTokenVis()" title="Mostrar/ocultar">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
              <button class="btn-secondary" onclick="saveToken()">Salvar</button>
              <button class="btn-primary" onclick="restartBot()">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Iniciar
              </button>
              <button class="btn-danger" onclick="stopBot()">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
                Parar
              </button>
            </div>
            <span id="token-msg" class="msg"></span>
          </div>
        </div>
        <div class="settings-section">
          <div class="settings-header">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
            Grupos Monitorados
          </div>
          <div class="settings-body">
            <div class="input-row">
              <input id="inp-chatid" type="text" placeholder="Chat ID" style="width:180px"/>
              <input id="inp-title"  type="text" placeholder="Nome (opcional)" style="flex:1"/>
              <button class="btn-primary" onclick="addGroup()">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Adicionar
              </button>
            </div>
            <span id="group-msg" class="msg"></span>
            <table><thead><tr><th>Chat ID</th><th>Nome</th><th>Desde</th><th>Último evento</th><th>Ação</th></tr></thead><tbody id="groups-body"></tbody></table>
          </div>
        </div>
      </section>

    </div><!-- /content -->
  </main>
</div>

<script>
function toggleSidebar() {
  const layout = document.getElementById('layout');
  const sidebar = document.getElementById('sidebar');
  const btn = document.getElementById('sidebar-toggle');
  const collapsed = sidebar.classList.toggle('collapsed');
  btn.style.transform = collapsed ? 'rotate(180deg)' : '';
  localStorage.setItem('sidebar-collapsed', collapsed);
}
(function(){
  if (localStorage.getItem('sidebar-collapsed') === 'true') {
    document.getElementById('sidebar').classList.add('collapsed');
    document.getElementById('sidebar-toggle').style.transform = 'rotate(180deg)';
  }
})();
</script>
<script src="/static/js/dashboard.js?v=5"></script>
</body>
</html>"""

# ─── CSS ─────────────────────────────────────────────────────
css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:         #08080f;
  --bg2:        #0c0c16;
  --surface:    #111120;
  --surface2:   #161628;
  --border:     rgba(255,255,255,.06);
  --border2:    rgba(255,255,255,.11);
  --text:       #e2e2f0;
  --muted:      #5a5a72;
  --accent:     #6366f1;
  --accent2:    #818cf8;
  --accent-glow:rgba(99,102,241,.25);
  --green:      #22c55e;
  --green-dim:  rgba(34,197,94,.12);
  --red:        #ef4444;
  --red-dim:    rgba(239,68,68,.12);
  --yellow:     #f59e0b;
  --yellow-dim: rgba(245,158,11,.12);
  --blue:       #38bdf8;
  --blue-dim:   rgba(56,189,248,.12);
  --hover:      rgba(255,255,255,.04);
  --r:          10px;
  --r-lg:       14px;
  --shadow:     0 4px 24px rgba(0,0,0,.5);
  --shadow-lg:  0 12px 56px rgba(0,0,0,.7);
  --sidebar-w:  220px;
  --sidebar-w-collapsed: 60px;
  --topbar-h:   56px;
  --ease:       cubic-bezier(.4,0,.2,1);
}

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 13.5px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
  height: 100vh;
}

/* ── LAYOUT ──────────────────────────────────────────── */
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── SIDEBAR ─────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width .25s var(--ease), min-width .25s var(--ease);
  overflow: hidden;
  position: relative;
  z-index: 10;
}

.sidebar.collapsed {
  width: var(--sidebar-w-collapsed);
  min-width: var(--sidebar-w-collapsed);
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  height: var(--topbar-h);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  white-space: nowrap;
}

.logo-icon {
  width: 28px; height: 28px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 0 18px var(--accent-glow);
}

.logo-text {
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -.3px;
  opacity: 1;
  transition: opacity .2s var(--ease), width .2s var(--ease);
  white-space: nowrap;
}

.sidebar.collapsed .logo-text { opacity: 0; width: 0; }
.sidebar.collapsed .sidebar-footer .refresh-time { display: none; }

.sidebar-toggle {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 5px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  transition: color .15s, background .15s, transform .25s var(--ease);
  flex-shrink: 0;
}

.sidebar-toggle:hover { background: var(--hover); color: var(--text); }

.nav {
  flex: 1;
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav::-webkit-scrollbar { width: 4px; }
.nav::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

.nav-divider {
  height: 1px;
  background: var(--border);
  margin: 8px 4px;
  flex-shrink: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  color: var(--muted);
  font-size: 13px;
  font-weight: 500;
  transition: background .15s, color .15s;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.nav-item:hover { background: var(--hover); color: var(--text); }

.nav-item.active {
  background: rgba(99,102,241,.1);
  color: var(--accent2);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0; top: 22%; bottom: 22%;
  width: 3px;
  background: var(--accent);
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 8px var(--accent);
}

.nav-icon {
  display: flex; align-items: center; justify-content: center;
  width: 20px; height: 20px;
  flex-shrink: 0;
}

.nav-label {
  opacity: 1;
  transition: opacity .18s var(--ease);
  white-space: nowrap;
}

.sidebar.collapsed .nav-label { opacity: 0; pointer-events: none; }
.sidebar.collapsed .nav-item { justify-content: center; }
.sidebar.collapsed .nav-item::before { display: none; }
.sidebar.collapsed .nav-item.active { box-shadow: inset 2px 0 0 var(--accent); }

.sidebar-footer {
  padding: 14px 14px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.bot-st {
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: 500;
  font-size: 12px;
}

.bot-st::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
  box-shadow: 0 0 8px currentColor;
  animation: blink 2.4s ease-in-out infinite;
}

.bot-st.ok   { color: var(--green); }
.bot-st.warn { color: var(--yellow); }
.bot-st.err  { color: var(--red); }

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.35} }

.refresh-time {
  display: block;
  color: var(--muted);
  font-size: 11px;
  margin-top: 5px;
  white-space: nowrap;
  overflow: hidden;
}

/* ── MAIN ────────────────────────────────────────────── */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }

/* ── TOPBAR ──────────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: var(--topbar-h);
  min-height: var(--topbar-h);
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

#page-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -.3px;
}

.select-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.select-icon {
  position: absolute;
  left: 11px;
  color: var(--muted);
  pointer-events: none;
}

#group-select {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 7px 30px 7px 30px;
  font-size: 13px;
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  appearance: none;
  transition: border-color .15s, box-shadow .15s;
  min-width: 200px;
}

#group-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }

/* ── CONTENT ─────────────────────────────────────────── */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.content::-webkit-scrollbar { width: 5px; }
.content::-webkit-scrollbar-track { background: transparent; }
.content::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ── VIEWS ───────────────────────────────────────────── */
.view { display: none; flex-direction: column; gap: 16px; }
.view.active { display: flex; animation: fadeUp .22s var(--ease); }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── CARDS ───────────────────────────────────────────── */
.cards { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  overflow: hidden;
  transition: transform .18s var(--ease), box-shadow .18s, border-color .18s;
}

.card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  opacity: .5;
}

.card:hover { transform: translateY(-2px); box-shadow: var(--shadow); border-color: var(--border2); }

.card--green::after { background: linear-gradient(90deg,transparent,var(--green),transparent); }
.card--red::after   { background: linear-gradient(90deg,transparent,var(--red),transparent); }
.card--blue::after  { background: linear-gradient(90deg,transparent,var(--blue),transparent); }
.card--yellow::after{ background: linear-gradient(90deg,transparent,var(--yellow),transparent); }

.card-icon {
  width: 32px; height: 32px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 4px;
}

.card--green .card-icon { background: var(--green-dim);  color: var(--green); }
.card--red   .card-icon { background: var(--red-dim);    color: var(--red); }
.card--blue  .card-icon { background: var(--blue-dim);   color: var(--blue); }
.card--yellow .card-icon{ background: var(--yellow-dim); color: var(--yellow); }

.card-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
}

.card-value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -1.5px;
  line-height: 1;
}

/* ── TWO COL ─────────────────────────────────────────── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

/* ── PANEL ───────────────────────────────────────────── */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.panel-header {
  padding: 12px 18px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 7px;
}

.panel-body { padding: 14px 18px; }

/* ── INSIGHTS ────────────────────────────────────────── */
#insights { list-style: none; display: flex; flex-direction: column; gap: 7px; }

#insights li {
  padding: 10px 13px;
  background: var(--surface2);
  border-radius: 8px;
  font-size: 13px;
  border-left: 2px solid var(--accent);
  line-height: 1.45;
  color: var(--text);
}

/* ── FEED ────────────────────────────────────────────── */
#feed { list-style: none; display: flex; flex-direction: column; gap: 5px; }

#feed li {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 13px;
  background: var(--surface2);
  border-radius: 8px;
  font-size: 13px;
  transition: background .12s;
}

#feed li:hover { background: var(--hover); }
.feed-user { flex: 1; font-weight: 500; }
.feed-time { color: var(--muted); font-size: 11.5px; font-variant-numeric: tabular-nums; }

.badge {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: .4px;
  padding: 2px 8px;
  border-radius: 20px;
  text-transform: uppercase;
  flex-shrink: 0;
}

.badge.join  { background: var(--green-dim); color: var(--green); }
.badge.leave { background: var(--red-dim);   color: var(--red); }

/* ── CHARTS ──────────────────────────────────────────── */
.chart-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 18px 20px;
}

.chart-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
  margin-bottom: 14px;
}

/* ── TABLE ───────────────────────────────────────────── */
.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.table-title {
  padding: 12px 18px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}

table { width: 100%; border-collapse: collapse; }

thead th {
  padding: 9px 16px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .7px;
  color: var(--muted);
  text-align: left;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
  white-space: nowrap;
}

tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--hover); }
tbody td { padding: 10px 16px; font-size: 13px; }

/* ── PAGINATION ──────────────────────────────────────── */
.pagination { display: flex; gap: 5px; padding: 12px 14px; }

.pagination button {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: border-color .12s, color .12s;
}

.pagination button:hover { border-color: var(--accent); color: var(--text); }
.pagination button.current { background: var(--accent); border-color: var(--accent); color: #fff; }

/* ── ANOMALIES ───────────────────────────────────────── */
#anomalies { display: flex; flex-wrap: wrap; gap: 10px; }

.anom {
  padding: 12px 16px;
  border-radius: 9px;
  font-size: 13px;
  line-height: 1.5;
  min-width: 150px;
}

.anom.spike { background: var(--yellow-dim); border: 1px solid rgba(245,158,11,.2); color: var(--yellow); }
.anom.drop  { background: var(--red-dim);    border: 1px solid rgba(239,68,68,.2);  color: var(--red); }

/* ── MEMBERS ─────────────────────────────────────────── */
.members-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 16px 22px;
  flex-wrap: wrap;
}

.members-stats { display: flex; gap: 28px; }
.stat-item { display: flex; flex-direction: column; gap: 1px; }
.stat-item .val { font-size: 22px; font-weight: 700; letter-spacing: -.5px; line-height: 1; }
.stat-item .lbl { font-size: 10.5px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
.members-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.search-wrap { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 10px; color: var(--muted); pointer-events: none; }

#member-search {
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 7px 12px 7px 30px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  width: 200px;
  transition: border-color .15s, box-shadow .15s;
}

#member-search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }

/* ── BUTTONS ─────────────────────────────────────────── */
button { font-family: inherit; cursor: pointer; transition: all .15s var(--ease); border: none; outline: none; }

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-radius: 8px;
  padding: 7px 16px;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex; align-items: center; gap: 6px;
}

.btn-primary:hover { background: var(--accent2); box-shadow: 0 0 20px var(--accent-glow); }

.btn-secondary {
  background: var(--surface2);
  color: var(--text);
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
}

.btn-secondary:hover { border-color: var(--accent); color: var(--accent2); }

.btn-danger {
  background: var(--red-dim);
  color: var(--red);
  border: 1px solid rgba(239,68,68,.2);
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex; align-items: center; gap: 6px;
}

.btn-danger:hover { background: rgba(239,68,68,.2); }

.btn-icon {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: inline-flex; align-items: center; justify-content: center;
  transition: background .12s, color .12s;
}

.btn-icon:hover { background: var(--hover); color: var(--text); }

.btn-icon-sm {
  background: none; border: none;
  color: var(--muted); cursor: pointer;
  padding: 3px 6px; border-radius: 5px; font-size: 12px;
  transition: background .12s, color .12s;
}

.btn-icon-sm:hover { background: var(--hover); color: var(--text); }

.btn-del {
  background: var(--red-dim);
  color: var(--red);
  border: 1px solid rgba(239,68,68,.2);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
}

.btn-del:hover { background: rgba(239,68,68,.2); }

/* ── INPUTS ──────────────────────────────────────────── */
input[type=text], input[type=password], textarea {
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 8px 13px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}

input[type=text]:focus, input[type=password]:focus, textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

/* ── SETTINGS ────────────────────────────────────────── */
.settings-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.settings-header {
  padding: 12px 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-row { display: flex; gap: 9px; align-items: center; flex-wrap: wrap; }

/* ── MSG ─────────────────────────────────────────────── */
.msg { font-size: 12px; padding: 6px 12px; border-radius: 6px; font-weight: 500; display: inline-block; }
.msg.ok  { background: var(--green-dim); color: var(--green); }
.msg.err { background: var(--red-dim);   color: var(--red); }

/* ── UTILS ───────────────────────────────────────────── */
.muted { color: var(--muted); }
.small { font-size: 12px; }

/* ── VAULT ───────────────────────────────────────────── */
.vault-layout {
  display: flex;
  gap: 14px;
  height: calc(100vh - 112px);
  min-height: 0;
}

.vault-sidebar {
  width: 220px;
  min-width: 180px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.vault-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}

.vault-cats {
  list-style: none;
  padding: 8px;
  margin: 0;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.vault-cats::-webkit-scrollbar { width: 4px; }
.vault-cats::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

.vault-cat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 11px;
  cursor: pointer;
  border-radius: 7px;
  transition: background .12s, color .12s;
  font-size: 13px;
  font-weight: 500;
}

.vault-cat-item:hover { background: var(--hover); }
.vault-cat-item.active { background: rgba(99,102,241,.1); color: var(--accent2); }
.vault-cat-item span { flex: 1; }

.vault-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  min-width: 0;
}

.vault-main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 13px 18px;
  border-radius: var(--r-lg);
  font-weight: 600;
  font-size: 14px;
}

.vault-entries {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 2px;
}

.vault-entries::-webkit-scrollbar { width: 4px; }
.vault-entries::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

.vault-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 16px 18px;
  transition: border-color .15s, box-shadow .15s;
}

.vault-card:hover { border-color: var(--border2); box-shadow: var(--shadow); }

.vault-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.vault-card-header strong { font-size: 14px; font-weight: 600; }

.vault-field {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 0;
  border-bottom: 1px solid var(--border);
}

.vault-field:last-of-type { border-bottom: none; }
.vault-field-label { color: var(--muted); font-size: 12px; min-width: 100px; font-weight: 500; }
.vault-field-value { font-size: 13px; cursor: pointer; color: var(--accent2); flex: 1; }
.vault-field-value:hover { text-decoration: underline; }
.vault-notes { margin-top: 11px; color: var(--muted); font-size: 13px; line-height: 1.5; }

/* Modais */
.vault-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.75);
  z-index: 9999;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(6px);
}

.vault-modal-box {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: var(--r-lg);
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  animation: modalIn .2s var(--ease);
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(.96) translateY(12px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.vault-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  font-size: 14px;
}

.vault-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  max-height: 60vh;
  overflow-y: auto;
}

.vault-modal-body label {
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .6px;
  margin-top: 5px;
}

.vault-modal-body input,
.vault-modal-body textarea {
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 8px 12px;
  font-size: 13px;
  font-family: inherit;
  width: 100%;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}

.vault-modal-body input:focus,
.vault-modal-body textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }

.vault-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
}

.vault-field-row {
  display: flex;
  gap: 7px;
  align-items: center;
  margin-bottom: 7px;
}

.vault-field-row input { flex: 1; }

.btn-add-field {
  background: none;
  border: 1px dashed var(--border2);
  border-radius: 7px;
  color: var(--muted);
  padding: 7px 13px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: border-color .15s, color .15s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}

.btn-add-field:hover { border-color: var(--accent); color: var(--accent2); }
"""

with open('app/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('app/static/css/dashboard.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('HTML e CSS reescritos!')
print('HTML:', len(html), 'bytes')
print('CSS: ', len(css), 'bytes')