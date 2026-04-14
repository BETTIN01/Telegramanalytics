css_path = 'app/static/css/dashboard.css'
css = open(css_path, encoding='utf-8').read()

# Remove o position:fixed do layout que está bloqueando tudo
css = css.replace(
    '  position: fixed;\n  top: 0; left: 0; right: 0; bottom: 0;\n',
    ''
)

# Garante que .layout.content não tem pointer-events bloqueados
# e que position:fixed não existe em nenhum bloco do layout
import re

# Substitui qualquer remanescente de position:fixed no .layout
css = re.sub(
    r'(\.layout\s*\{[^}]*?)position\s*:\s*fixed;?\s*',
    r'\1',
    css
)
css = re.sub(
    r'(\.layout\s*\{[^}]*?)top\s*:\s*0;\s*left\s*:\s*0;\s*right\s*:\s*0;\s*bottom\s*:\s*0;\s*',
    r'\1',
    css
)

open(css_path, 'w', encoding='utf-8').write(css)
print('Fix aplicado!')

# Verifica se ainda tem position:fixed no layout
idx = css.find('.layout')
print('Trecho .layout atual:')
print(css[idx:idx+250])