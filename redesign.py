css = open('app/static/css/dashboard.css', encoding='utf-8').read()

new_css = """
/* ══ RESET & TOKENS ═══════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:          #0a0a0f;
  --bg2:         #0f0f17;
  --surface:     #13131e;
  --surface2:    #1a1a28;
  --border:      #ffffff0f;
  --border2:     #ffffff18;
  --text:        #e8e8f0;
  --muted:       #6b6b80;
  --accent:      #6366f1;
  --accent2:     #818cf8;
  --accent-dim:  #6366f115;
  --green:       #22c55e;
  --green-dim:   #22c55e18;
  --red:         #ef4444;
  --red-dim:     #ef444418;
  --yellow:      #eab308;
  --yellow-dim:  #eab30818;
  --hover:       #ffffff08;
  --radius:      10px;
  --radius-lg:   14px;
  --shadow:      0 4px 24px rgba(0,0,0,.4);
  --shadow-lg:   0 8px 48px rgba(0,0,0,.6);
  --font:        'Inter', -apple-system, sans-serif;
  --transition:  all .18s cubic-bezier(.4,0,.2,1);
}

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

/* ══ LAYOUT ═══════════════════════════════════════════════════ */
.layout { display: flex; height: 100vh; width: 100vw; overflow: hidden; }

/* ══ SIDEBAR ══════════════════════════════════════════════════ */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  position: relative;
}

.sidebar::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 1px; height: 100%;
  background: linear-gradient(180deg, transparent, var(--accent)22, transparent);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px 16px;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: -.3px;
  color: var(--text);
  border-bottom: 1px solid var(--border);
}

.logo-icon {
  width: 30px; height: 30px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px;
  box-shadow: 0 0 16px var(--accent)44;
}

.nav {
  flex: 1;
  padding: 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  color: var(--muted);
  font-size: 13.5px;
  font-weight: 500;
  transition: var(--transition);
  position: relative;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--hover);
  color: var(--text);
}

.nav-item.active {
  background: var(--accent-dim);
  color: var(--accent2);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0; top: 20%; bottom: 20%;
  width: 3px;
  background: var(--accent);
  border-radius: 0 3px 3px 0;
}

.nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }

.sidebar-footer {
  padding: 14px 16px;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.bot-st {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 12px;
}

.bot-st::before {
  content: '';
  width: 7px; height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 8px currentColor;
  animation: pulse 2s infinite;
}

.bot-st.ok   { color: var(--green); }
.bot-st.warn { color: var(--yellow); }
.bot-st.err  { color: var(--red); }

@keyframes pulse {
  0%,100% { opacity: 1; }
  50%      { opacity: .4; }
}

#last-refresh {
  display: block;
  color: var(--muted);
  font-size: 11px;
  margin-top: 4px;
}

/* ══ MAIN ═════════════════════════════════════════════════════ */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ══ TOPBAR ═══════════════════════════════════════════════════ */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 58px;
  min-height: 58px;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
}

#page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -.3px;
}

.group-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

#group-select {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 7px 32px 7px 12px;
  font-size: 13px;
  font-family: var(--font);
  font-weight: 500;
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b6b80' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  transition: var(--transition);
}

#group-select:hover { border-color: var(--accent); }
#group-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent)22; }

/* ══ CONTENT ══════════════════════════════════════════════════ */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.content::-webkit-scrollbar { width: 6px; }
.content::-webkit-scrollbar-track { background: transparent; }
.content::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ══ VIEWS ════════════════════════════════════════════════════ */
.view { display: none; flex-direction: column; gap: 20px; animation: fadeIn .2s ease; }
.view.active { display: flex; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ══ CARDS ════════════════════════════════════════════════════ */
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent)33, transparent);
}

.card:hover {
  border-color: var(--border2);
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.card-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  margin-bottom: 10px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -1px;
  color: var(--text);
}

/* ══ TWO COL ══════════════════════════════════════════════════ */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* ══ PANELS ═══════════════════════════════════════════════════ */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel-header {
  padding: 14px 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-body { padding: 16px 20px; }

/* ══ INSIGHTS ═════════════════════════════════════════════════ */
#insights {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

#insights li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface2);
  border-radius: 8px;
  font-size: 13px;
  border-left: 3px solid var(--accent);
  line-height: 1.4;
}

/* ══ FEED ═════════════════════════════════════════════════════ */
#feed { list-style: none; display: flex; flex-direction: column; gap: 6px; }

#feed li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface2);
  border-radius: 8px;
  font-size: 13px;
  transition: var(--transition);
}

#feed li:hover { background: var(--hover); }

.badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .5px;
  padding: 3px 8px;
  border-radius: 20px;
  text-transform: uppercase;
}

.badge.join  { background: var(--green-dim);  color: var(--green); }
.badge.leave { background: var(--red-dim);    color: var(--red); }

.feed-user { font-weight: 500; flex: 1; }
.feed-time { color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; }

/* ══ CHARTS ═══════════════════════════════════════════════════ */
.chart-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.chart-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  margin-bottom: 16px;
}

canvas { border-radius: 6px; }

/* ══ TABLE ════════════════════════════════════════════════════ */
.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.table-title {
  padding: 14px 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}

table { width: 100%; border-collapse: collapse; }

thead th {
  padding: 10px 16px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--muted);
  text-align: left;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
}

tbody tr {
  border-bottom: 1px solid var(--border);
  transition: var(--transition);
}

tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--hover); }

tbody td {
  padding: 11px 16px;
  font-size: 13px;
  color: var(--text);
}

/* ══ PAGINATION ═══════════════════════════════════════════════ */
.pagination { display: flex; gap: 6px; padding: 14px 16px; }

.pagination button {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 6px;
  padding: 5px 11px;
  font-size: 12px;
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
}

.pagination button:hover { border-color: var(--accent); color: var(--text); }
.pagination button.current { background: var(--accent); border-color: var(--accent); color: #fff; }

/* ══ ANOMALIES ════════════════════════════════════════════════ */
#anomalies { display: flex; flex-wrap: wrap; gap: 12px; }

.anom {
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
  min-width: 160px;
}

.anom.spike { background: var(--yellow-dim); border: 1px solid var(--yellow)33; color: var(--yellow); }
.anom.drop  { background: var(--red-dim);    border: 1px solid var(--red)33;    color: var(--red); }

/* ══ MEMBERS ══════════════════════════════════════════════════ */
.members-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 22px;
}

.members-stats { display: flex; gap: 28px; }

.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-item .val { font-size: 20px; font-weight: 700; letter-spacing: -.5px; }
.stat-item .lbl { font-size: 11px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }

.members-actions { display: flex; gap: 8px; align-items: center; }

#member-search {
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 7px 14px;
  font-size: 13px;
  font-family: var(--font);
  outline: none;
  width: 200px;
  transition: var(--transition);
}

#member-search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent)22; }

/* ══ BUTTONS ══════════════════════════════════════════════════ */
button, .btn {
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
  border: none;
  outline: none;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary:hover { background: var(--accent2); box-shadow: 0 0 16px var(--accent)44; }

.btn-secondary {
  background: var(--surface2);
  color: var(--text);
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 7px 16px;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
}

.btn-secondary:hover { border-color: var(--accent); color: var(--accent2); }

.btn-danger {
  background: var(--red-dim);
  color: var(--red);
  border: 1px solid var(--red)33;
  border-radius: 7px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
}

.btn-danger:hover { background: var(--red)22; }

.btn-del { background: var(--red-dim); color: var(--red); border: 1px solid var(--red)33; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; cursor: pointer; transition: var(--transition); }
.btn-del:hover { background: var(--red)22; }

.btn-icon {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 15px;
  transition: var(--transition);
}

.btn-icon:hover { background: var(--hover); color: var(--text); }

.btn-icon-sm {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 3px 7px;
  border-radius: 5px;
  font-size: 12px;
  transition: var(--transition);
}

.btn-icon-sm:hover { background: var(--hover); color: var(--text); }

/* ══ SETTINGS ═════════════════════════════════════════════════ */
.settings-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.settings-header {
  padding: 14px 22px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
}

.settings-body { padding: 22px; display: flex; flex-direction: column; gap: 14px; }

.input-row { display: flex; gap: 10px; align-items: center; }

input[type=text], input[type=password], textarea, select {
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 8px 14px;
  font-size: 13px;
  font-family: var(--font);
  outline: none;
  transition: var(--transition);
}

input[type=text]:focus,
input[type=password]:focus,
textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent)22; }

/* ══ MSG ══════════════════════════════════════════════════════ */
.msg { font-size: 12px; padding: 7px 12px; border-radius: 6px; font-weight: 500; }
.msg.ok  { background: var(--green-dim); color: var(--green); }
.msg.err { background: var(--red-dim);   color: var(--red); }

/* ══ MUTED / SMALL ════════════════════════════════════════════ */
.muted { color: var(--muted); }
.small { font-size: 12px; }

/* ══ COFRE ════════════════════════════════════════════════════ */
.vault-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 118px);
}

.vault-sidebar {
  width: 230px;
  min-width: 180px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.vault-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
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

.vault-cat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  cursor: pointer;
  border-radius: 8px;
  transition: var(--transition);
  font-size: 13px;
  font-weight: 500;
}

.vault-cat-item:hover { background: var(--hover); }
.vault-cat-item.active { background: var(--accent-dim); color: var(--accent2); }
.vault-cat-item span { flex: 1; }

.vault-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
  min-width: 0;
}

.vault-main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 14px 20px;
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-size: 14px;
}

.vault-entries {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 2px;
}

.vault-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  transition: var(--transition);
}

.vault-card:hover { border-color: var(--border2); box-shadow: var(--shadow); }

.vault-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.vault-card-header strong { font-size: 14px; font-weight: 600; }

.vault-field {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}

.vault-field:last-of-type { border-bottom: none; }
.vault-field-label { color: var(--muted); font-size: 12px; min-width: 100px; font-weight: 500; }
.vault-field-value { font-size: 13px; cursor: pointer; color: var(--accent2); flex: 1; }
.vault-field-value:hover { text-decoration: underline; }
.vault-notes { margin-top: 12px; color: var(--muted); font-size: 13px; line-height: 1.5; }

/* Modais */
.vault-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.7);
  z-index: 9999;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.vault-modal-box {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  animation: slideUp .2s cubic-bezier(.4,0,.2,1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px) scale(.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.vault-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  font-size: 15px;
}

.vault-modal-body {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vault-modal-body label {
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .6px;
  margin-top: 6px;
}

.vault-modal-body input,
.vault-modal-body textarea {
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  padding: 9px 13px;
  font-size: 13px;
  font-family: var(--font);
  width: 100%;
  outline: none;
  transition: var(--transition);
}

.vault-modal-body input:focus,
.vault-modal-body textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent)22; }

.vault-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 22px;
  border-top: 1px solid var(--border);
}

.vault-modal-footer button:first-child {
  background: var(--surface2);
  border: 1px solid var(--border2);
  color: var(--muted);
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 13px;
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
}

.vault-modal-footer button:first-child:hover { color: var(--text); border-color: var(--border2); }

.vault-field-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.vault-field-row input { flex: 1; }

.btn-add-field {
  background: none;
  border: 1px dashed var(--border2);
  border-radius: 8px;
  color: var(--muted);
  padding: 8px 14px;
  font-size: 12px;
  font-family: var(--font);
  cursor: pointer;
  transition: var(--transition);
  margin-top: 4px;
}

.btn-add-field:hover { border-color: var(--accent); color: var(--accent2); }
"""

# Substitui o CSS completamente
with open('app/static/css/dashboard.css', 'w', encoding='utf-8') as f:
    f.write(new_css)

print('CSS redesenhado! Tamanho:', len(new_css))