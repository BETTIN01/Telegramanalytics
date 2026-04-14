path  = 'app/routes/api.py'
lines = open(path, encoding='utf-8').read().split('\n')

nl = '\n'

lines[211] = "        yield 'data: " + chr(123) + chr(34) + "ping" + chr(34) + ":true}" + nl + nl + "'"
lines[215] = "                yield 'data: ' + json.dumps(data) + '" + nl + nl + "'"
lines[217] = "                yield 'data: {}" + nl + nl + "'"

open(path, 'w', encoding='utf-8').write('\n'.join(lines))
print('OK')
for i, l in enumerate(lines[210:218], 211):
    print(i, repr(l))