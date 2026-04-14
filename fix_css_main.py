css = open('app/static/css/dashboard.css', encoding='utf-8').read()

# Remove todos os blocos conflitantes de .main e .layout e reescreve limpo
import re

# Remove o bloco FIX SIDEBAR COLLAPSE que foi adicionado antes
css = re.sub(r'/\* ── FIX SIDEBAR COLLAPSE.*?\*/', '', css, flags=re.DOTALL)

# Substitui a regra .layout
css = re.sub(
    r'\.layout\s*\{[^}]+\}',
    '.layout {\n  display: flex;\n  height: 100vh;\n  width: 100vw;\n  overflow: hidden;\n  position: relative;\n}',
    css, count=1
)

# Substitui a regra .main
css = re.sub(
    r'\.main\s*\{[^}]+\}',
    '.main {\n  flex: 1 1 auto;\n  min-width: 0;\n  width: 0;\n  display: flex;\n  flex-direction: column;\n  overflow: hidden;\n  transition: width .25s cubic-bezier(.4,0,.2,1);\n}',
    css, count=1
)

# Garante sidebar com transition e flex-shrink:0
css = re.sub(
    r'\.sidebar\s*\{',
    '.sidebar {\n  flex-shrink: 0;',
    css, count=1
)

open('app/static/css/dashboard.css', 'w', encoding='utf-8').write(css)
print('CSS corrigido! Tamanho:', len(css))