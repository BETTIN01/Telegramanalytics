with open('app/routes/api.py', encoding='utf-8') as f:
    content = f.read()

old = 'api_bp = Blueprint("api", __name__)'
new = 'api_bp = Blueprint("api", __name__, url_prefix="/api")'

if old in content:
    content = content.replace(old, new)
    open('app/routes/api.py', 'w', encoding='utf-8').write(content)
    print('OK - prefixo adicionado')
else:
    # Mostra como está a linha do Blueprint
    for i, l in enumerate(content.split('\n'), 1):
        if 'Blueprint' in l:
            print(i, repr(l))