css = open('app/static/css/dashboard.css', encoding='utf-8').read()

fixes = [
    # 1 — layout precisa de overflow:hidden para conter tudo
    ('.layout {\n  display: flex;\n  height: 100vh;\n  overflow: hidden;\n}',
     '.layout {\n  display: flex;\n  height: 100vh;\n  width: 100vw;\n  overflow: hidden;\n}'),

    # 2 — sidebar collapsed: forçar width exato e overflow hidden
    ('.sidebar.collapsed {\n  width: var(--sidebar-w-collapsed);\n  min-width: var(--sidebar-w-collapsed);\n}',
     '.sidebar.collapsed {\n  width: var(--sidebar-w-collapsed) !important;\n  min-width: var(--sidebar-w-collapsed) !important;\n  max-width: var(--sidebar-w-collapsed) !important;\n}'),

    # 3 — main deve crescer para ocupar espaço restante
    ('.main { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; transition: all .25s cubic-bezier(.4,0,.2,1); }',
     '.main {\n  flex: 1 1 0;\n  min-width: 0;\n  max-width: 100%;\n  display: flex;\n  flex-direction: column;\n  overflow: hidden;\n}'),
]

count = 0
for old, new in fixes:
    if old in css:
        css = css.replace(old, new)
        count += 1
        print(f'✓ fix {count} aplicado')
    else:
        print(f'✗ não encontrado: {repr(old[:60])}')

# Adiciona regra extra no final para garantir
css += """
/* ── FIX SIDEBAR COLLAPSE ────────────────────────── */
.sidebar { flex-shrink: 0; }
.main    { flex: 1 1 auto; min-width: 0; overflow: hidden; }
.layout  { display: flex !important; width: 100vw; height: 100vh; overflow: hidden; }
"""

open('app/static/css/dashboard.css', 'w', encoding='utf-8').write(css)
print('CSS corrigido! Tamanho:', len(css))