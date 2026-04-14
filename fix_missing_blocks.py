html = open('app/templates/index.html', encoding='utf-8').read()

# ── FIX 1: Skeleton cards ────────────────────────────────────
old_cards = '        <div class="cards">\n          <div class="card card--green">'
new_cards = '''        <!-- SKELETON CARDS -->
        <div class="cards" id="skeleton-cards">
          <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
          <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
          <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
          <div class="card skel"><div class="skel-line skel-sm"></div><div class="skel-line skel-lg"></div></div>
        </div>
        <div class="cards" id="real-cards" style="display:none">
          <div class="card card--green">'''

if old_cards in html:
    html = html.replace(old_cards, new_cards, 1)
    print('✓ Skeleton cards corrigido')
else:
    print('✗ cards ainda não encontrado — verificar indentação')
    idx = html.find('card card--green')
    print(repr(html[idx-80:idx+60]))

# ── FIX 2: Vault toolbar ─────────────────────────────────────
old_vault = '            <div class="vault-main-header">\n              <span id="vault-cat-title">Selecione uma categoria</span>\n              <button onclick="vaultNewEntry()" id="btn-new-entry" class="btn-primary" style="display:none">'

new_vault = '''            <div class="vault-toolbar">
              <div class="search-wrap" style="flex:1">
                <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input id="vault-global-search" type="text" placeholder="Busca global no cofre..." oninput="vaultGlobalSearch(this.value)" style="width:100%"/>
              </div>
              <button class="btn-secondary" onclick="showVaultHistory()" style="white-space:nowrap;display:inline-flex;align-items:center;gap:6px">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Histórico
              </button>
            </div>
            <div class="vault-main-header">
              <span id="vault-cat-title">Selecione uma categoria</span>
              <button onclick="vaultNewEntry()" id="btn-new-entry" class="btn-primary" style="display:none">'''

if old_vault in html:
    html = html.replace(old_vault, new_vault, 1)
    print('✓ Vault toolbar corrigido')
else:
    print('✗ vault header ainda não encontrado')
    idx = html.find('vault-main-header')
    print(repr(html[idx-50:idx+200]))

# ── FIX 3: Fecha real-cards corretamente ─────────────────────
# Procura o fechamento do bloco de cards antes do two-col
old_close = '        </div>\n      </div>\n      <div class="two-col">'
new_close = '        </div>\n        </div><!-- /real-cards -->\n      <div class="two-col">'

if old_close in html:
    html = html.replace(old_close, new_close, 1)
    print('✓ real-cards fechado corretamente')
else:
    print('⚠ fechamento já ok ou não encontrado')

open('app/templates/index.html', 'w', encoding='utf-8').write(html)
print('\n✅ Fixes aplicados!')