path = 'app/routes/api.py'
content = open(path, encoding='utf-8').read()

import re

new_block = '\n'.join([
    '@api_bp.route("/alerts/stream")',
    'def alerts_stream():',
    '    q = queue.Queue(maxsize=50)',
    '    with _alert_lock:',
    '        _alert_queues.append(q)',
    '    def generate():',
    "        yield 'data: ' + '{\"ping\":true}' + chr(10) + chr(10)",
    '        while True:',
    '            try:',
    '                data = q.get(timeout=25)',
    "                yield 'data: ' + json.dumps(data) + chr(10) + chr(10)",
    '            except queue.Empty:',
    "                yield 'data: ' + '{}' + chr(10) + chr(10)",
    '    return Response(',
    '        stream_with_context(generate()),',
    '        mimetype="text/event-stream",',
    '        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}',
    '    )',
])

content = re.sub(
    r'@api_bp\.route\("/alerts/stream"\).*?def alerts_stream\(\):.*?return Response\(.*?\)',
    new_block,
    content,
    flags=re.DOTALL
)

open(path, 'w', encoding='utf-8').write(content)
print('OK! Verificando...')

lines = content.split('\n')
for i, l in enumerate(lines):
    if 'alerts_stream' in l:
        for j, ll in enumerate(lines[i-1:i+20], i):
            print(j+1, repr(ll))
        break