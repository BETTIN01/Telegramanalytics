css_extra = """

/* ═══════════════════════════════════════════════════════════
   BLOCO 4 — NOVAS FUNCIONALIDADES
═══════════════════════════════════════════════════════════ */

/* ── TEMA CLARO ─────────────────────────────────────────── */
[data-theme="light"] {
  --bg:          #f4f5f7;
  --bg2:         #ffffff;
  --surface:     #ffffff;
  --surface2:    #f0f1f3;
  --border:      rgba(0,0,0,.09);
  --border2:     rgba(0,0,0,.15);
  --text:        #111827;
  --muted:       #6b7280;
  --accent:      #6366f1;
  --accent2:     #4f46e5;
  --accent-glow: rgba(99,102,241,.2);
  --orange:      #ea580c;
  --hover:       rgba(0,0,0,.04);
  --shadow:      0 4px 24px rgba(0,0,0,.1);
  --shadow-lg:   0 12px 56px rgba(0,0,0,.18);
}

[data-theme="light"] .content {
  background-image:
    linear-gradient(rgba(0,0,0,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,.025) 1px, transparent 1px);
}

[data-theme="light"] body { background: var(--bg); }

[data-theme="light"] .sidebar,
[data-theme="light"] .topbar {
  background: var(--bg2);
  border-color: var(--border);
}

[data-theme="light"] .panel,
[data-theme="light"] .chart-wrap,
[data-theme="light"] .table-wrap,
[data-theme="light"] .card,
[data-theme="light"] .settings-section,
[data-theme="light"] .members-bar,
[data-theme="light"] .vault-sidebar,
[data-theme="light"] .vault-main-header,
[data-theme="light"] .vault-card {
  background: var(--surface);
  border-color: var(--border);
}

[data-theme="light"] .panel-header,
[data-theme="light"] .table-title,
[data-theme="light"] .settings-header,
[data-theme="light"] .vault-sidebar-header,
[data-theme="light"] thead th {
  background: var(--surface2);
  color: var(--muted);
}

[data-theme="light"] #insights li,
[data-theme="light"] #feed li {
  background: var(--surface2);
}

[data-theme="light"] .nav-item { color: var(--muted); }
[data-theme="light"] .nav-item:hover { background: var(--hover); color: var(--text); }
[data-theme="light"] .vault-cat-item:hover { background: var(--hover); }

[data-theme="light"] input[type=text],
[data-theme="light"] input[type=password],
[data-theme="light"] textarea,
[data-theme="light"] #group-select,
[data-theme="light"] #member-search {
  background: var(--surface2);
  border-color: var(--border2);
  color: var(--text);
}

[data-theme="light"] .btn-secondary {
  background: var(--surface2);
  color: var(--text);
  border-color: var(--border2);
}

[data-theme="light"] .vault-modal-box {
  background: var(--surface);
  border-color: var(--border2);
}

[data-theme="light"] .vault-modal {
  background: rgba(0,0,0,.45);
}

[data-theme="light"] .log-container { background: #1e1e2e; }

[data-theme="light"] #page-title {
  background: linear-gradient(90deg, var(--text), var(--muted));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Transição suave entre temas */
body, .sidebar, .topbar, .main, .panel, .card,
.chart-wrap, .table-wrap, .settings-section,
.members-bar, .vault-sidebar, .vault-card,
input, textarea, select, .btn-secondary {
  transition: background .3s ease, color .2s ease,
              border-color .2s ease, box-shadow .2s ease !important;
}

/* ── BREADCRUMB ──────────────────────────────────────────── */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 14px;
}

.breadcrumb-root {
  color: var(--muted);
  font-weight: 500;
  font-size: 13px;
}

.breadcrumb svg { color: var(--muted); flex-shrink: 0; }

#page-title {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: -.3px;
}

/* ── TOPBAR BUTTONS ──────────────────────────────────────── */
.topbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  border: 1px solid transparent;
  transition: background .15s, color .15s, border-color .15s;
}

.topbar-btn:hover {
  background: var(--hover);
  color: var(--text);
  border-color: var(--border2);
}

/* ── TOAST ───────────────────────────────────────────────── */
#toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 99999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  min-width: 260px;
  max-width: 380px;
  pointer-events: all;
  box-shadow: 0 8px 32px rgba(0,0,0,.4);
  border: 1px solid transparent;
  opacity: 0;
  transform: translateX(24px);
  transition: opacity .3s ease, transform .3s ease;
  backdrop-filter: blur(8px);
}

.toast--visible {
  opacity: 1;
  transform: translateX(0);
}

.toast--success {
  background: rgba(34,197,94,.12);
  border-color: rgba(34,197,94,.25);
  color: #22c55e;
}

.toast--error {
  background: rgba(239,68,68,.12);
  border-color: rgba(239,68,68,.25);
  color: #ef4444;
}

.toast--warning {
  background: rgba(245,158,11,.12);
  border-color: rgba(245,158,11,.25);
  color: #f59e0b;
}

.toast--info {
  background: rgba(99,102,241,.12);
  border-color: rgba(99,102,241,.25);
  color: var(--accent2);
}

.toast-icon { flex-shrink: 0; }

.toast-msg { flex: 1; color: var(--text); }

.toast-close {
  background: none;
  border: none;
  color: var(--muted);
  font-size: 16px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  flex-shrink: 0;
}

.toast-close:hover { color: var(--text); }

/* ── SKELETON LOADING ────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position:  600px 0; }
}

.skel {
  pointer-events: none;
  cursor: default;
}

.skel-line {
  border-radius: 6px;
  background: linear-gradient(
    90deg,
    var(--surface2) 25%,
    var(--border2)  50%,
    var(--surface2) 75%
  );
  background-size: 600px 100%;
  animation: shimmer 1.6s infinite linear;
}

.skel-sm  { height: 10px; width: 55%; margin-bottom: 14px; }
.skel-lg  { height: 32px; width: 75%; }

/* ── ALERT BANNER ────────────────────────────────────────── */
.alert-banner {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 9998;
  padding: 10px 24px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  background: linear-gradient(90deg, var(--orange), #c2410c);
  color: #fff;
  animation: slideDown .3s ease;
}

@keyframes slideDown {
  from { transform: translateY(-100%); }
  to   { transform: translateY(0); }
}

/* ── LOG VIEWER ──────────────────────────────────────────── */
.log-container {
  background: #0d0d1a;
  border-radius: 0 0 var(--r-lg) var(--r-lg);
  padding: 14px 18px;
  height: calc(100vh - 220px);
  overflow-y: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 12.5px;
  line-height: 1.65;
}

.log-container::-webkit-scrollbar { width: 5px; }
.log-container::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

.log-line {
  display: flex;
  gap: 14px;
  padding: 2px 0;
  border-bottom: 1px solid rgba(255,255,255,.03);
  animation: fadeUp .15s ease;
}

.log-time {
  color: #6366f1;
  font-size: 11px;
  flex-shrink: 0;
  padding-top: 1px;
  font-weight: 600;
  letter-spacing: .3px;
}

.log-msg { color: #a0aec0; flex: 1; word-break: break-all; }

.log-placeholder {
  color: rgba(255,255,255,.2);
  font-style: italic;
  padding: 20px 0;
  text-align: center;
}

/* Live dot */
.live-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
  animation: blink 2s ease-in-out infinite;
  align-self: center;
}

/* ── VAULT TOOLBAR ───────────────────────────────────────── */
.vault-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  margin-bottom: 12px;
}

/* ── SENHA STRENGTH ──────────────────────────────────────── */
.pw-strength-bar {
  background: var(--surface2);
  border-radius: 2px;
  height: 4px;
  overflow: hidden;
}

/* ── SCHEDULER ───────────────────────────────────────────── */
#view-scheduler,
#view-logs {
  gap: 16px;
}

input[type="datetime-local"] {
  color-scheme: dark;
}

[data-theme="light"] input[type="datetime-local"] {
  color-scheme: light;
}

/* ── RESPONSIVO ──────────────────────────────────────────── */
@media (max-width: 900px) {
  :root {
    --sidebar-w: 200px;
  }
  .cards { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .sidebar:not(.collapsed) {
    position: fixed;
    z-index: 200;
    box-shadow: var(--shadow-lg);
  }

  .sidebar.collapsed {
    width: 0 !important;
    min-width: 0 !important;
    border: none;
  }

  .main { width: 100vw !important; }

  .cards { grid-template-columns: 1fr 1fr; }

  .topbar { padding: 0 14px; }

  .topbar-right { gap: 5px; }

  .topbar-btn span { display: none; }

  #group-select { min-width: 130px; font-size: 12px; }

  .content { padding: 14px; }

  .members-bar { flex-direction: column; align-items: flex-start; }
  .members-actions { flex-wrap: wrap; }

  .vault-layout { flex-direction: column; height: auto; }
  .vault-sidebar { width: 100%; min-width: unset; }
}

@media (max-width: 420px) {
  .cards { grid-template-columns: 1fr; }
  .breadcrumb-root { display: none; }
}
"""

css_path = 'app/static/css/dashboard.css'
css = open(css_path, encoding='utf-8').read()

if 'BLOCO 4' not in css:
    open(css_path, 'a', encoding='utf-8').write(css_extra)
    print('✅ Bloco 4 (CSS) aplicado!')
    print('Tamanho final CSS:', len(css) + len(css_extra), 'bytes')
else:
    print('⚠ já aplicado')