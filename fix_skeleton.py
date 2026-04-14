with open('app/static/js/dashboard.js', encoding='utf-8') as f:
    content = f.read()

# Remove o showSkeleton do loadOverview (colocado antes)
# e adiciona controle por flag
old = "async function loadOverview() {\n  showSkeleton();"
new = "async function loadOverview(forceSkeletion = false) {\n  if (forceSkeletion) showSkeleton();"

# Faz o loadGroups/change chamar com flag true
old2 = "await LOADERS[activeView]();"
new2 = "await (activeView === 'overview' ? loadOverview(true) : LOADERS[activeView]());"

if old in content:
    content = content.replace(old, new, 1)
    # Substitui apenas as chamadas manuais (click no nav e change do select), não o refresh
    content = content.replace(old2, new2)
    with open('app/static/js/dashboard.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Skeleton corrigido")
else:
    print("⚠️  Trecho não encontrado — skeleton já foi removido ou modificado")