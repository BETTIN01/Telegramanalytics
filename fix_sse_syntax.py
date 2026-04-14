api_path = 'app/routes/api.py'
api = open(api_path, encoding='utf-8').read()

# Remove a linha com erro e substitui por versão correta
old_yield = '''    def generate():
        yield "data: {}\\'ping\\'}\\'}\n\n".replace("{\\'ping\\'}\\'}", '{"ping":true}\n\n')
        while True:'''

new_yield = '''    def generate():
        yield 'data: {"ping":true}\\n\\n'
        while True:'''

if old_yield in api:
    api = api.replace(old_yield, new_yield)
    open(api_path, 'w', encoding='utf-8').write(api)
    print('✅ Corrigido!')
else:
    # Fallback: busca pela linha problemática diretamente
    lines = api.split('\n')
    for i, line in enumerate(lines):
        if 'ping' in line and 'replace' in line and 'yield' in line:
            lines[i] = "        yield 'data: {\"ping\":true}\\n\\n'"
            print(f'✅ Linha {i+1} corrigida!')
            break
    open(api_path, 'w', encoding='utf-8').write('\n'.join(lines))