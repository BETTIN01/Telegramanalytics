import os, glob

fixes = glob.glob('fix_*.py') + glob.glob('check_*.py') + glob.glob('estado_*.txt') + glob.glob('vault_state.txt')

if not fixes:
    print('Nenhum arquivo encontrado.')
else:
    for f in fixes:
        os.remove(f)
        print(f'Removido: {f}')
    print(f'\nTotal removido: {len(fixes)} arquivos.')