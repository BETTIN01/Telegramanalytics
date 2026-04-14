html = open('app/templates/index.html', encoding='utf-8').read()

# Substitui o script inline do toggle por versão robusta
old_script = '''<script>
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
</script>'''

new_script = '''<script>
function toggleSidebar() {
  var sidebar = document.getElementById('sidebar');
  var main    = document.getElementById('main');
  var btn     = document.getElementById('sidebar-toggle');
  var collapsed = sidebar.classList.toggle('collapsed');
  if (collapsed) {
    sidebar.style.width = '60px';
    sidebar.style.minWidth = '60px';
    main.style.width = 'calc(100vw - 60px)';
    btn.style.transform = 'rotate(180deg)';
  } else {
    sidebar.style.width = '220px';
    sidebar.style.minWidth = '220px';
    main.style.width = 'calc(100vw - 220px)';
    btn.style.transform = '';
  }
  localStorage.setItem('sidebar-collapsed', collapsed);
}
(function(){
  var sidebar = document.getElementById('sidebar');
  var main    = document.getElementById('main');
  var btn     = document.getElementById('sidebar-toggle');
  if (localStorage.getItem('sidebar-collapsed') === 'true') {
    sidebar.classList.add('collapsed');
    sidebar.style.width = '60px';
    sidebar.style.minWidth = '60px';
    main.style.width = 'calc(100vw - 60px)';
    if (btn) btn.style.transform = 'rotate(180deg)';
  }
})();
</script>'''

if old_script in html:
    html = html.replace(old_script, new_script)
    print('Script toggle corrigido!')
else:
    print('Script nao encontrado — checando...')
    idx = html.find('toggleSidebar')
    print(html[idx-20:idx+300])

# Garante que o main tem id="main"
if '<main class="main">' in html:
    html = html.replace('<main class="main">', '<main class="main" id="main">')
    print('id=main adicionado!')

open('app/templates/index.html', 'w', encoding='utf-8').write(html)