import sys
sys.stdout = open('html_dump.txt', 'w', encoding='utf-8')
print(open('app/templates/index.html', encoding='utf-8').read())