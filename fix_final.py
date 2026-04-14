path = 'app/routes/api.py'
lines = open(path, encoding='utf-8').read().split('\n')

# Acha a linha exata do decorator
start = next(i for i, l in enumerate(lines) if '@api_bp.route("/alerts/stream")' in l)

# Acha o fim do bloco (próxima linha após '    )' que fecha o return Response)
end = start
depth = 0
for i in range(start, len(lines)):
    if 'return Response(' in lines[i]:
        depth = 1
    if depth and lines[i].strip() == ')':
        end = i
        break

print(f'Substituindo linhas {start}–{end}')
print('Conteúdo atual:')
for i in range(start, end+1):
    print(i, repr(lines[i]))

new_block = [
    '@api_bp.route("/alerts/stream")',
    'def alerts_stream():',
    '    q = queue.Queue(maxsize=50)',
    '    with _alert_lock:',
    '        _alert_queues.append(q)',
    '    def generate():',
    '        yield \'data: {"ping":true}\\n\\n\'',
    '        while True:',
    '            try:',
    '                data = q.get(timeout=25)',
    "                yield 'data: ' + json.dumps(data) + '\\n\\n'",
    '            except queue.Empty:',
    "                yield 'data: {}\\n\\n'",
    '    return Response(',
    '        stream_with_context(generate()),',
    '        mimetype="text/event-stream",',
    '        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}',
    '    )',
]

lines[start:end+1] = new_block
open(path, 'w', encoding='utf-8').write('\n'.join(lines))
print('\n✅ OK! Resultado:')
for i, l in enumerate(lines[start:start+18], start):
    print(i, repr(l))