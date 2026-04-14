import re

# ── 1. FIX CSS ──────────────────────────────────────────────
css = open('app/static/css/dashboard.css', encoding='utf-8').read()

# Remove TODOS os blocos anteriores conflitantes de layout
# e injeta regras limpas no início do arquivo
layout_override = """
/* ═══════════════════════════════════════════════
   LAYOUT CORE — não editar
═══════════════════════════════════════════════ */
html, body {
  height: 100%;
  width: 100%;
  overflow: hidden;
  margin: 0; padding: 0;
}

.layout {
  display: flex !important;
  flex-direction: row !important;
  height: 100vh !important;
  width: 100vw !important;
  overflow: hidden !important;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
}

.sidebar {
  flex: 0 0 220px;
  width: 220px;
  max-width: 220px;
  min-width: 220px;
  height: 100vh;
  overflow: hidden;
  transition: flex 0.25s ease, width 0.25s ease, max-width 0.25s ease, min-width 0.25s ease;
  will-change: width;
  position: relative;
  z-index: 10;
}

.sidebar.collapsed {
  flex: 0 0 60px !important;
  width: 60px !important;
  max-width: 60px !important;
  min-width: 60px !important;
}

.main {
  flex: 1 1 0 !important;
  min-width: 0 !important;
  width: 0 !important;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

"""

css = layout_override + css
open('app/static/css/dashboard.css', 'w', encoding='utf-8').write(css)
print('CSS: layout core injetado no topo!')

# ── 2. FIX HTML — script toggle simplificado ────────────────
html = open('app/templates/index.html', encoding='utf-8').read()

# Garante id="main" no <main>
if 'id="main"' not in html:
    html = html.replace('<main class="main">', '<main class="main" id="main">')
    print('id=main: adicionado')

# Substitui qualquer script de toggleSidebar existente
new_script = """<script>
function toggleSidebar() {
  var s   = document.getElementById('sidebar');
  var btn = document.getElementById('sidebar-toggle');
  var collapsed = s.classList.toggle('collapsed');
  btn.style.transform = collapsed ? 'rotate(180deg)' : 'rotate(0deg)';
  localStorage.setItem('sb', collapsed ? '1' : '0');
}
(function(){
  if (localStorage.getItem('sb') === '1') {
    var s   = document.getElementById('sidebar');
    var btn = document.getElementById('sidebar-toggle');
    if (s)   s.classList.add('collapsed');
    if (btn) btn.style.transform = 'rotate(180deg)';
  }
})();
</script>"""

# Remove script anterior e coloca novo
html = re.sub(r'<script>\s*function toggleSidebar[\s\S]*?</script>', '', html)
html = html.replace('<script src="/static/js/dashboard.js', new_script + '\n<script src="/static/js/dashboard.js')

open('app/templates/index.html', 'w', encoding='utf-8').write(html)
print('HTML: script toggle reescrito!')
print('Tudo aplicado. Reinicie o servidor.')