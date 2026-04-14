path = 'app/routes/api.py'
content = open(path, encoding='utf-8').read()

# Acha o bloco inteiro da função e substitui
import re

old_block = re.search(
    r'@api_bp\.route\("/alerts/stream"\).*?def alerts_stream\(\):.*?return Response\(.*?\)',
    content, re.DOTALL
)

if old_block:
    print('Bloco encontrado, substituindo...')
    NL = '\n'
    new_block = (
        '@api_bp.route("/alerts/stream")\n'
        'def alerts_stream():\n'
        '    q = queue.Queue(maxsize=50)\n'
        '    with _alert_lock:\n'
        '        _alert_queues.append(q)\n'
        '    def generate():\n'
        '        yield "data: {' + chr(34) + 'ping' + chr(34) + ':true}' + chr(10) + chr(10) + '"\n'
        '        while True:\n'
        '            try:\n'
        '                data = q.get(timeout=25)\n'
        '                yield "data: " + json.dumps(data) + "' + chr(10) + chr(10) + '"\n'
        '            except queue.Empty:\n'
        '                yield "data: {}"  + "' + chr(10) + chr(10) + '"\n'
        '    return Response(\n'
        '        stream_with_context(generate()),\n'
        '        mimetype="text/event-stream",\n'
        '        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}\n'
        '    )'
    )
    content = content[:old_block.start()] + new_block + content[old_block.end():]
    open(path, 'w', encoding='utf-8').write(content)
    print('✅ Bloco SSE reescrito com sucesso!')
else:
    print('✗ Bloco não encontrado, mostrando contexto...')
    for i, l in enumerate(content.split('\n')[200:230], 201):
        print(i, repr(l))