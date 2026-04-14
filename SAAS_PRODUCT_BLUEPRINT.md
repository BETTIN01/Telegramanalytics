# SaaS Product Blueprint

## Ideal customer profile

- Operadores de grupos pagos no Telegram
- Pequenas equipes de growth, monetização e comunidade
- Infoprodutores e operações de tráfego que precisam ligar aquisição, membros e receita

## Core problem

Hoje o painel resolve monitoramento e operação, mas ainda parece ferramenta interna. O produto SaaS precisa resolver um problema de negócio maior:

- conectar aquisição, entrada/saída de membros e receita
- mostrar sinais de retenção e churn com clareza
- automatizar reporting e alertas sem trabalho manual
- permitir que múltiplos clientes usem o mesmo sistema com isolamento e cobrança

## Product positioning

Plataforma de analytics e operação para grupos pagos no Telegram, com foco em:

- crescimento de base
- retenção
- receita
- automação operacional

## Differentiation

- visão unificada de grupo + financeiro + aquisição
- relatórios automáticos e exportações prontas para operação
- camada futura de insights automáticos e previsão de crescimento
- produto voltado para monetização de comunidades, não só analytics genérico

## Monetization strategy

### Free

- 1 grupo
- até 1.000 eventos por mês
- 1 automação
- 1 integração
- 1 usuário

### Pro

- até 5 grupos
- até 25.000 eventos por mês
- 10 automações
- 5 usuários
- exportações, pixel, financeiro e relatórios agendados

### Premium

- até 25 grupos
- até 250.000 eventos por mês
- 100 automações
- 25 usuários
- alertas inteligentes
- AI insights
- growth forecast
- webhooks e prioridade

## Recommended pricing

- Free: R$ 0
- Pro: R$ 99/mês ou R$ 990/ano
- Premium: R$ 299/mês ou R$ 2.990/ano

## Usage-based expansion

Cobranças futuras podem ser adicionadas por:

- grupos extras
- eventos extras
- automações extras
- integrações extras

## SaaS architecture direction

### Current foundation added

- organizations
- organization_memberships
- saas_plans
- organization_subscriptions
- organization_usage_counters

### Next architecture phase

- filtrar todas as queries principais por `organization_id`
- propagar `organization_id` em:
  - groups
  - events
  - members
  - finance_transactions
  - scheduled_reports
  - campaign tables
- middleware para contexto do tenant atual
- feature gating centralizado por plano

## Key product KPIs

- MRR
- ARR
- churn de membros
- crescimento líquido
- retenção
- eventos por mês
- grupos ativos
- seats ativos
- conversão por origem/campanha

## Premium features roadmap

### Phase 1

- multi-tenant foundation
- planos e assinatura manual
- usage tracking
- painel de plano atual

### Phase 2

- feature gating real por plano
- onboarding por workspace
- cobrança Stripe / Pagar.me / Mercado Pago
- trial + upgrade + downgrade

### Phase 3

- alertas inteligentes
- insights por IA
- previsão de crescimento e risco de churn
- score de saúde do grupo

### Phase 4

- painel admin global
- analytics por cliente
- gestão de inadimplência
- controle de expansão por uso

## Retention levers

- relatórios recorrentes
- alertas de queda ou churn
- automações que economizam tempo
- benchmarking de performance por período
- insights acionáveis em vez de só dashboards

## Founder note

O melhor caminho comercial para este produto não é vender “um dashboard”. É vender:

- crescimento previsível de comunidades pagas
- controle operacional
- receita mais visível
- retenção mais alta com menos esforço manual
