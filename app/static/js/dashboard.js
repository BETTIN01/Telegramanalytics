'use strict';

let chatId     = null;
let activeView = 'home';
let activePage = 1;
let timer      = null;
let charts     = {};
let prevJoins  = 0;
let audioCtx   = null;
let allMembers = [];
let allEvents  = [];
let groupList  = [];
let autoRefreshEnabled = false;
let notificationItems = [];
let goalSettings = {};
let currentGoalsMetrics = null;
const PERF_PROFILE = detectPerformanceProfile();
const GLOBAL_REFRESH_MS = PERF_PROFILE.isConservative ? 30000 : 18000;
const FINANCE_LIVE_REFRESH_MS = PERF_PROFILE.isConservative ? 15000 : 10000;
const LOG_REFRESH_MS = PERF_PROFILE.isConservative ? 5000 : 2500;
const GROUPS_CACHE_MS = PERF_PROFILE.isConservative ? 45000 : 20000;
const BOT_STATUS_CACHE_MS = PERF_PROFILE.isConservative ? 60000 : 25000;
let financeState = {
  settings: null,
  summary: null,
  payments: [],
  filteredPayments: [],
  activePayment: null,
  selectedAccount: '',
  pollTimer: null,
  pollBusy: false,
};
const MEMBER_AUTO_SYNC_MS = 120000;
const memberAutoSyncAt = {};
const refreshState = {
  busy: false,
  queued: false,
  groupsLoadedAt: 0,
  groupsSignature: '',
  botStatusLoadedAt: 0,
  botStatusSignature: '',
};
let activeViewRefreshTimer = null;
let nameSearchState = {
  query: '',
  searchType: 'nome',
  rows: [],
  raw: null,
  endpoint: '',
  source: '',
};
const NAME_SEARCH_TYPES = {
  nome: { param: 'nome', minChars: 2, labels: { pt: 'Nome', en: 'Name' } },
  cpf: { param: 'cpf', minChars: 1, labels: { pt: 'CPF', en: 'CPF' } },
  titulo: { param: 'titulo', minChars: 1, labels: { pt: 'Titulo', en: 'Voter ID' } },
  mae: { param: 'mae', minChars: 2, labels: { pt: 'Mae', en: 'Mother' } },
  pai: { param: 'pai', minChars: 2, labels: { pt: 'Pai', en: 'Father' } },
  rg: { param: 'rg', minChars: 1, labels: { pt: 'RG', en: 'RG' } },
};

const NOTIFICATIONS_KEY = 'tg_analytics_notifications_v3';
const MAX_NOTIFICATIONS = 24;
const GOALS_KEY = 'tg_analytics_goals_v1';
const NOTIFICATION_SESSION_STARTED_AT = Date.now();
const seenNotificationEventIds = new Set();

if (document.documentElement) {
  document.documentElement.classList.toggle('perf-lite', PERF_PROFILE.isConservative);
}

const VIEW_CONTEXT = {
  pt: {
    home: 'Escolha a area inicial do sistema e use a lateral para alternar rapidamente entre grupos monitorados.',
    overview: 'Acompanhe indicadores principais, insight rapido e feed recente do grupo ativo.',
    charts: 'Analise as series temporais de entradas, saidas e crescimento do grupo.',
    events: 'Filtre entradas e saidas por usuario e acompanhe a trilha operacional.',
    reports: 'Veja consolidado semanal, mensal e sinais de anomalia do grupo.',
    goals: 'Defina metas por grupo e acompanhe o progresso de crescimento, base e churn.',
    pixel: 'Conecte a Meta para acompanhar status de campanhas, cliques, leads e preparar o rastreamento do Pixel.',
    finance: 'Crie cobrancas PIX, acompanhe pagamentos e centralize recebimentos por grupo.',
    'name-search': 'Consulte base externa por nome, CPF, titulo, mae, pai ou RG e veja a resposta completa da API.',
    members: 'Gerencie a base de membros, admins e sincronizacoes com o Telegram.',
    vault: 'Acesse categorias seguras e entradas sensiveis do projeto.',
    scheduler: 'Controle a fila de mensagens agendadas para o grupo ativo.',
    logs: 'Monitore os logs do bot em tempo real para diagnostico rapido.',
    settings: 'Ajuste token, grupos monitorados e operacao do bot.'
  },
  en: {
    home: 'Choose the initial area of the system and use the sidebar to switch quickly between monitored groups.',
    overview: 'Track the main KPIs, quick insights and the recent activity feed for the active group.',
    charts: 'Analyze the time series for joins, leaves and group growth.',
    events: 'Filter joins and leaves by user and inspect the operational trail.',
    reports: 'See weekly, monthly and anomaly summaries for the group.',
    goals: 'Set group goals and track progress for growth, member base and churn.',
    pixel: 'Connect Meta to track campaign status, clicks, leads and prepare full Pixel tracking.',
    finance: 'Create PIX charges, track payments and centralize cashflow by group.',
    'name-search': 'Query the external base by name, CPF, voter ID, mother, father or RG and inspect the full API response.',
    members: 'Manage member base, admins and Telegram synchronizations.',
    vault: 'Access secure categories and sensitive project entries.',
    scheduler: 'Control the queue of scheduled messages for the active group.',
    logs: 'Monitor live bot logs for faster diagnostics.',
    settings: 'Adjust token, monitored groups and bot operation.'
  }
};

const VIEW_ORDER = ['home', 'overview', 'charts', 'reports', 'goals', 'events', 'pixel', 'finance', 'name-search', 'members', 'vault', 'scheduler', 'logs', 'settings'];
const LAUNCH_ORDER = ['overview', 'charts', 'reports', 'goals', 'events', 'pixel', 'finance', 'name-search', 'members', 'vault', 'scheduler', 'logs', 'settings'];
let currentLang = localStorage.getItem('lang') || 'pt';
let currentTheme = localStorage.getItem('theme') || 'light';
let currentThemePreset = localStorage.getItem('theme_preset') || 'corporate';
let currentUserProfile = {
  id: Number(document.body && document.body.dataset ? document.body.dataset.authUserId || 0 : 0) || 0,
  user: null,
  preferences: null,
  saas: null,
};

const THEME_PRESETS = {
  corporate: {
    name: { pt: 'Corporate', en: 'Corporate' },
    desc: { pt: 'Sobrio, limpo e executivo.', en: 'Clean, sober and executive.' },
    accent: '#2563eb',
    accent2: '#60a5fa',
    soft: 'rgba(37,99,235,.12)',
    strong: '#1d4ed8',
    glow: 'rgba(37,99,235,.2)',
    heroA: 'rgba(37,99,235,.16)',
    heroB: 'rgba(14,165,233,.1)',
    iconBg: 'rgba(37,99,235,.12)',
    iconColor: '#1d4ed8',
    shellStart: '#f7fbff',
    shellEnd: '#e6eef8',
    orbA: 'rgba(37,99,235,.18)',
    orbB: 'rgba(14,165,233,.12)',
    surfaceA: 'rgba(255,255,255,.92)',
    surfaceB: 'rgba(241,246,252,.94)',
    cardShadow: 'rgba(37,99,235,.14)',
    preview: 'linear-gradient(135deg, #0f172a 0%, #2563eb 54%, #93c5fd 100%)'
  },
  cyber: {
    name: { pt: 'Cyber', en: 'Cyber' },
    desc: { pt: 'Turquesa tecnico com energia de painel.', en: 'Technical cyan with control-room energy.' },
    accent: '#06b6d4',
    accent2: '#22d3ee',
    soft: 'rgba(6,182,212,.14)',
    strong: '#0891b2',
    glow: 'rgba(34,211,238,.22)',
    heroA: 'rgba(6,182,212,.16)',
    heroB: 'rgba(34,211,238,.12)',
    iconBg: 'rgba(6,182,212,.14)',
    iconColor: '#0f766e',
    shellStart: '#f2fdff',
    shellEnd: '#ddf8fb',
    orbA: 'rgba(6,182,212,.2)',
    orbB: 'rgba(34,211,238,.14)',
    surfaceA: 'rgba(245,255,255,.94)',
    surfaceB: 'rgba(230,249,250,.94)',
    cardShadow: 'rgba(6,182,212,.16)',
    preview: 'linear-gradient(135deg, #07111d 0%, #0f766e 45%, #22d3ee 100%)'
  },
  demon: {
    name: { pt: 'Demon', en: 'Demon' },
    desc: { pt: 'Vermelho escuro com presenca forte.', en: 'Deep red with stronger presence.' },
    accent: '#dc2626',
    accent2: '#fb7185',
    soft: 'rgba(220,38,38,.12)',
    strong: '#b91c1c',
    glow: 'rgba(251,113,133,.22)',
    heroA: 'rgba(220,38,38,.16)',
    heroB: 'rgba(251,113,133,.1)',
    iconBg: 'rgba(220,38,38,.12)',
    iconColor: '#b91c1c',
    shellStart: '#fff6f7',
    shellEnd: '#fde7ea',
    orbA: 'rgba(220,38,38,.18)',
    orbB: 'rgba(251,113,133,.14)',
    surfaceA: 'rgba(255,250,250,.94)',
    surfaceB: 'rgba(254,241,242,.94)',
    cardShadow: 'rgba(220,38,38,.14)',
    preview: 'linear-gradient(135deg, #19090c 0%, #991b1b 45%, #fb7185 100%)'
  },
  cyberpunk: {
    name: { pt: 'Cyberpunk', en: 'Cyberpunk' },
    desc: { pt: 'Neon magenta com contraste futurista.', en: 'Magenta neon with futuristic contrast.' },
    accent: '#db2777',
    accent2: '#8b5cf6',
    soft: 'rgba(219,39,119,.14)',
    strong: '#be185d',
    glow: 'rgba(139,92,246,.24)',
    heroA: 'rgba(219,39,119,.16)',
    heroB: 'rgba(139,92,246,.12)',
    iconBg: 'rgba(139,92,246,.14)',
    iconColor: '#7c3aed',
    shellStart: '#fff7fc',
    shellEnd: '#f4ebff',
    orbA: 'rgba(219,39,119,.18)',
    orbB: 'rgba(139,92,246,.16)',
    surfaceA: 'rgba(255,249,253,.94)',
    surfaceB: 'rgba(248,241,255,.94)',
    cardShadow: 'rgba(139,92,246,.16)',
    preview: 'linear-gradient(135deg, #140a1d 0%, #be185d 46%, #8b5cf6 100%)'
  },
  vaporwave: {
    name: { pt: 'Vaporwave', en: 'Vaporwave' },
    desc: { pt: 'Pastel neon com clima retro-digital.', en: 'Pastel neon with a retro-digital mood.' },
    accent: '#ff5ea9',
    accent2: '#6ee7ff',
    soft: 'rgba(255,94,169,.14)',
    strong: '#f472b6',
    glow: 'rgba(110,231,255,.24)',
    heroA: 'rgba(255,94,169,.16)',
    heroB: 'rgba(110,231,255,.14)',
    iconBg: 'rgba(125,90,255,.14)',
    iconColor: '#f472b6',
    shellStart: '#fff8ff',
    shellEnd: '#eef8ff',
    orbA: 'rgba(255,94,169,.20)',
    orbB: 'rgba(110,231,255,.18)',
    surfaceA: 'rgba(255,249,255,.95)',
    surfaceB: 'rgba(241,248,255,.95)',
    cardShadow: 'rgba(168,85,247,.18)',
    preview: 'linear-gradient(135deg, #180f2f 0%, #ff5ea9 42%, #8b5cf6 72%, #6ee7ff 100%)'
  },
  aurora: {
    name: { pt: 'Aurora', en: 'Aurora' },
    desc: { pt: 'Verde oceano com brilho editorial.', en: 'Ocean green with editorial glow.' },
    accent: '#0f9f88',
    accent2: '#7dd3fc',
    soft: 'rgba(15,159,136,.14)',
    strong: '#0f766e',
    glow: 'rgba(125,211,252,.24)',
    heroA: 'rgba(15,159,136,.16)',
    heroB: 'rgba(125,211,252,.14)',
    iconBg: 'rgba(15,159,136,.12)',
    iconColor: '#0f766e',
    shellStart: '#f2fffb',
    shellEnd: '#e4f4fb',
    orbA: 'rgba(20,184,166,.16)',
    orbB: 'rgba(125,211,252,.18)',
    surfaceA: 'rgba(248,255,253,.95)',
    surfaceB: 'rgba(237,247,251,.95)',
    cardShadow: 'rgba(20,184,166,.14)',
    preview: 'linear-gradient(135deg, #052f2d 0%, #0f766e 44%, #7dd3fc 100%)'
  },
  noctis: {
    name: { pt: 'Noctis', en: 'Noctis' },
    desc: { pt: 'Azul profundo com contraste premium.', en: 'Deep blue with premium contrast.' },
    accent: '#1d4ed8',
    accent2: '#94a3ff',
    soft: 'rgba(29,78,216,.14)',
    strong: '#1e40af',
    glow: 'rgba(148,163,255,.22)',
    heroA: 'rgba(29,78,216,.16)',
    heroB: 'rgba(148,163,255,.12)',
    iconBg: 'rgba(29,78,216,.12)',
    iconColor: '#1e40af',
    shellStart: '#f4f7ff',
    shellEnd: '#e8edfd',
    orbA: 'rgba(59,130,246,.18)',
    orbB: 'rgba(147,197,253,.12)',
    surfaceA: 'rgba(249,251,255,.95)',
    surfaceB: 'rgba(239,243,255,.95)',
    cardShadow: 'rgba(59,130,246,.14)',
    preview: 'linear-gradient(135deg, #0b1120 0%, #1e3a8a 48%, #94a3ff 100%)'
  }
};

const THEME_LAYOUT_SIGNATURES = {
  corporate: {
    uiFont: "'Inter', system-ui, sans-serif",
    displayFont: "'Manrope', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(18px, 2.4vw, 30px)',
    panelRadius: '18px',
    cardRadius: '14px',
    chipRadius: '12px',
    toolbarRadius: '16px',
    panelPadding: '18px',
    cardPadding: '17px',
    heroGap: '12px',
    contentGap: '9px',
    homeMain: 'minmax(0, 1.34fr)',
    homeSide: 'minmax(300px, .76fr)',
    metaMin: '186px',
    launchMin: '220px',
    cardMinHeight: '102px',
    heroTitleSize: 'clamp(26px, 2vw, 36px)',
    bodyTop: '#07111b',
    bodyBottom: '#0a1522',
    ambientGlow: 'rgba(96, 165, 250, 0.10)',
    ambientOpacity: '.18',
    toolbarSurface: 'linear-gradient(180deg, rgba(10,18,28,.88), rgba(8,15,24,.92))',
    toolbarBorder: 'rgba(148,163,184,.14)',
    panelBorder: 'rgba(118,146,187,.18)',
    heroSurface: 'linear-gradient(180deg, rgba(14,27,45,.98), rgba(11,22,38,.98))',
    panelSurface: 'linear-gradient(180deg, rgba(14,24,39,.92), rgba(10,18,30,.96))',
    cardSurface: 'linear-gradient(180deg, rgba(16,28,45,.82), rgba(11,20,34,.9))',
    cardShadowSoft: '0 14px 32px rgba(2, 8, 20, 0.18)',
    panelShadowSoft: '0 18px 44px rgba(2, 8, 20, 0.22)',
  },
  cyber: {
    uiFont: "'Inter', system-ui, sans-serif",
    displayFont: "'Space Grotesk', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(13px, 1.8vw, 22px)',
    panelRadius: '14px',
    cardRadius: '11px',
    chipRadius: '10px',
    toolbarRadius: '12px',
    panelPadding: '15px',
    cardPadding: '14px',
    heroGap: '8px',
    contentGap: '7px',
    homeMain: 'minmax(0, 1.42fr)',
    homeSide: 'minmax(280px, .62fr)',
    metaMin: '170px',
    launchMin: '210px',
    cardMinHeight: '98px',
    heroTitleSize: 'clamp(25px, 1.9vw, 34px)',
    bodyTop: '#04131a',
    bodyBottom: '#071720',
    ambientGlow: 'rgba(34, 211, 238, 0.14)',
    ambientOpacity: '.28',
    toolbarSurface: 'linear-gradient(180deg, rgba(3,16,22,.94), rgba(4,21,29,.96))',
    toolbarBorder: 'rgba(34,211,238,.18)',
    panelBorder: 'rgba(34,211,238,.16)',
    heroSurface: 'linear-gradient(180deg, rgba(4,22,29,.96), rgba(4,18,24,.98))',
    panelSurface: 'linear-gradient(180deg, rgba(4,20,27,.9), rgba(3,16,22,.96))',
    cardSurface: 'linear-gradient(180deg, rgba(6,23,31,.82), rgba(4,17,24,.92))',
    cardShadowSoft: '0 14px 34px rgba(3, 19, 27, 0.24)',
    panelShadowSoft: '0 18px 44px rgba(3, 19, 27, 0.26)',
  },
  demon: {
    uiFont: "'Inter', system-ui, sans-serif",
    displayFont: "'Sora', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(16px, 2.4vw, 30px)',
    panelRadius: '26px',
    cardRadius: '20px',
    chipRadius: '999px',
    toolbarRadius: '20px',
    panelPadding: '21px',
    cardPadding: '19px',
    heroGap: '17px',
    contentGap: '12px',
    homeMain: 'minmax(0, 1.2fr)',
    homeSide: 'minmax(320px, .82fr)',
    metaMin: '188px',
    launchMin: '220px',
    cardMinHeight: '108px',
    heroTitleSize: 'clamp(28px, 2.1vw, 38px)',
    bodyTop: '#14090d',
    bodyBottom: '#1a0e13',
    ambientGlow: 'rgba(251, 113, 133, 0.12)',
    ambientOpacity: '.22',
    toolbarSurface: 'linear-gradient(180deg, rgba(24,10,15,.92), rgba(18,10,15,.96))',
    toolbarBorder: 'rgba(248,113,113,.16)',
    panelBorder: 'rgba(248,113,113,.14)',
    heroSurface: 'linear-gradient(180deg, rgba(33,13,17,.96), rgba(17,9,14,.98))',
    panelSurface: 'linear-gradient(180deg, rgba(28,12,18,.88), rgba(16,10,14,.94))',
    cardSurface: 'linear-gradient(180deg, rgba(38,14,21,.8), rgba(20,11,16,.88))',
    cardShadowSoft: '0 16px 38px rgba(22, 6, 10, 0.28)',
    panelShadowSoft: '0 20px 48px rgba(22, 6, 10, 0.30)',
  },
  cyberpunk: {
    uiFont: "'Inter', system-ui, sans-serif",
    displayFont: "'Space Grotesk', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(13px, 1.9vw, 22px)',
    panelRadius: '14px',
    cardRadius: '12px',
    chipRadius: '10px',
    toolbarRadius: '12px',
    panelPadding: '15px',
    cardPadding: '14px',
    heroGap: '8px',
    contentGap: '7px',
    homeMain: 'minmax(0, 1.5fr)',
    homeSide: 'minmax(260px, .56fr)',
    metaMin: '176px',
    launchMin: '200px',
    cardMinHeight: '96px',
    heroTitleSize: 'clamp(24px, 1.85vw, 33px)',
    bodyTop: '#120917',
    bodyBottom: '#150d20',
    ambientGlow: 'rgba(168, 85, 247, 0.12)',
    ambientOpacity: '.24',
    toolbarSurface: 'linear-gradient(180deg, rgba(20,9,29,.94), rgba(12,8,22,.97))',
    toolbarBorder: 'rgba(168,85,247,.20)',
    panelBorder: 'rgba(168,85,247,.18)',
    heroSurface: 'linear-gradient(180deg, rgba(24,11,34,.96), rgba(12,9,23,.98))',
    panelSurface: 'linear-gradient(180deg, rgba(22,10,32,.88), rgba(11,9,22,.94))',
    cardSurface: 'linear-gradient(180deg, rgba(28,13,40,.8), rgba(13,10,25,.9))',
    cardShadowSoft: '0 15px 36px rgba(20, 7, 30, 0.28)',
    panelShadowSoft: '0 20px 46px rgba(20, 7, 30, 0.30)',
  },
  vaporwave: {
    uiFont: "'Space Grotesk', 'Inter', system-ui, sans-serif",
    displayFont: "'Sora', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(18px, 2.3vw, 32px)',
    panelRadius: '24px',
    cardRadius: '18px',
    chipRadius: '16px',
    toolbarRadius: '18px',
    panelPadding: '20px',
    cardPadding: '18px',
    heroGap: '15px',
    contentGap: '11px',
    homeMain: 'minmax(0, 1.32fr)',
    homeSide: 'minmax(300px, .72fr)',
    metaMin: '180px',
    launchMin: '216px',
    cardMinHeight: '104px',
    heroTitleSize: 'clamp(27px, 2vw, 37px)',
    bodyTop: '#160d2b',
    bodyBottom: '#24113d',
    ambientGlow: 'rgba(110, 231, 255, 0.14)',
    ambientOpacity: '.22',
    toolbarSurface: 'linear-gradient(180deg, rgba(29,12,48,.9), rgba(18,11,33,.95))',
    toolbarBorder: 'rgba(255,94,169,.18)',
    panelBorder: 'rgba(110,231,255,.14)',
    heroSurface: 'linear-gradient(180deg, rgba(35,16,55,.96), rgba(19,12,34,.98))',
    panelSurface: 'linear-gradient(180deg, rgba(33,14,50,.88), rgba(18,11,32,.94))',
    cardSurface: 'linear-gradient(180deg, rgba(40,18,58,.82), rgba(22,12,36,.9))',
    cardShadowSoft: '0 18px 38px rgba(20, 8, 32, 0.26)',
    panelShadowSoft: '0 24px 50px rgba(20, 8, 32, 0.30)',
  },
  aurora: {
    uiFont: "'Inter', system-ui, sans-serif",
    displayFont: "'Manrope', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(20px, 2.8vw, 36px)',
    panelRadius: '30px',
    cardRadius: '22px',
    chipRadius: '999px',
    toolbarRadius: '24px',
    panelPadding: '24px',
    cardPadding: '21px',
    heroGap: '20px',
    contentGap: '13px',
    homeMain: 'minmax(0, 1.34fr)',
    homeSide: 'minmax(280px, .68fr)',
    metaMin: '170px',
    launchMin: '230px',
    cardMinHeight: '110px',
    heroTitleSize: 'clamp(27px, 2vw, 36px)',
    bodyTop: '#081817',
    bodyBottom: '#0b1820',
    ambientGlow: 'rgba(125, 211, 252, 0.10)',
    ambientOpacity: '.16',
    toolbarSurface: 'linear-gradient(180deg, rgba(7,26,26,.80), rgba(8,20,28,.88))',
    toolbarBorder: 'rgba(125,211,252,.16)',
    panelBorder: 'rgba(125,211,252,.14)',
    heroSurface: 'linear-gradient(180deg, rgba(11,31,33,.94), rgba(9,23,33,.96))',
    panelSurface: 'linear-gradient(180deg, rgba(12,27,31,.86), rgba(8,19,28,.92))',
    cardSurface: 'linear-gradient(180deg, rgba(14,30,34,.78), rgba(10,22,30,.88))',
    cardShadowSoft: '0 16px 38px rgba(4, 20, 24, 0.22)',
    panelShadowSoft: '0 22px 52px rgba(4, 20, 24, 0.24)',
  },
  noctis: {
    uiFont: "'Inter', system-ui, sans-serif",
    displayFont: "'Sora', 'Inter', system-ui, sans-serif",
    shellPad: 'clamp(13px, 1.7vw, 22px)',
    panelRadius: '16px',
    cardRadius: '12px',
    chipRadius: '11px',
    toolbarRadius: '14px',
    panelPadding: '15px',
    cardPadding: '14px',
    heroGap: '9px',
    contentGap: '7px',
    homeMain: 'minmax(0, 1.36fr)',
    homeSide: 'minmax(300px, .68fr)',
    metaMin: '180px',
    launchMin: '210px',
    cardMinHeight: '100px',
    heroTitleSize: 'clamp(25px, 1.9vw, 34px)',
    bodyTop: '#050b16',
    bodyBottom: '#09111d',
    ambientGlow: 'rgba(96, 115, 173, 0.10)',
    ambientOpacity: '.14',
    toolbarSurface: 'linear-gradient(180deg, rgba(6,12,24,.94), rgba(7,11,20,.98))',
    toolbarBorder: 'rgba(96,115,173,.18)',
    panelBorder: 'rgba(96,115,173,.16)',
    heroSurface: 'linear-gradient(180deg, rgba(11,20,37,.96), rgba(8,14,27,.98))',
    panelSurface: 'linear-gradient(180deg, rgba(10,18,33,.9), rgba(8,13,25,.96))',
    cardSurface: 'linear-gradient(180deg, rgba(12,20,36,.82), rgba(9,15,28,.9))',
    cardShadowSoft: '0 14px 32px rgba(2, 8, 20, 0.24)',
    panelShadowSoft: '0 18px 42px rgba(2, 8, 20, 0.28)',
  },
};

const THEME_VISUAL_SIGNATURES = {
  corporate: {
    bodyDark: 'linear-gradient(180deg, #08121d 0%, #0c1725 100%)',
    bodyLight: 'linear-gradient(180deg, #f6f9fd 0%, #edf3f8 100%)',
    grid: 'linear-gradient(rgba(148,163,184,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.025) 1px, transparent 1px)',
    gridSize: '40px 40px',
    gridOpacity: '.10',
    panelDark: 'linear-gradient(180deg, rgba(13,23,36,.96), rgba(10,18,29,.98))',
    panelLight: 'linear-gradient(180deg, rgba(255,255,255,.96), rgba(245,249,253,.98))',
    cardDark: 'linear-gradient(180deg, rgba(16,28,44,.9), rgba(12,21,34,.94))',
    cardLight: 'linear-gradient(180deg, rgba(255,255,255,.98), rgba(247,250,255,.98))',
    controlDark: 'linear-gradient(180deg, rgba(16,28,44,.92), rgba(12,21,34,.96))',
    controlLight: 'linear-gradient(180deg, rgba(255,255,255,.98), rgba(247,250,255,.98))',
    border: 'rgba(120,146,183,.14)',
    panelShadow: '0 14px 28px rgba(4,10,20,.16)',
    cardShadow: '0 10px 22px rgba(4,10,20,.12)',
    backdrop: 'none',
    kickerSpacing: '.16em',
    kickerShadow: 'none'
  },
  cyber: {
    bodyDark: 'radial-gradient(circle at top left, rgba(34, 211, 238, 0.22), transparent 20%), radial-gradient(circle at bottom right, rgba(6, 182, 212, 0.18), transparent 20%), linear-gradient(180deg, #031118 0%, #06171d 100%)',
    bodyLight: 'radial-gradient(circle at top left, rgba(34, 211, 238, 0.12), transparent 22%), linear-gradient(180deg, #f1fdff 0%, #e2f7fa 100%)',
    grid: 'linear-gradient(rgba(34,211,238,0.075) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.075) 1px, transparent 1px)',
    gridSize: '26px 26px',
    gridOpacity: '.46',
    panelDark: 'repeating-linear-gradient(180deg, rgba(255,255,255,.016) 0 1px, transparent 1px 14px), linear-gradient(180deg, rgba(5,23,28,.97), rgba(3,16,21,.99))',
    panelLight: 'repeating-linear-gradient(180deg, rgba(34,211,238,.03) 0 1px, transparent 1px 14px), linear-gradient(180deg, rgba(247,255,255,.98), rgba(234,250,251,.99))',
    cardDark: 'repeating-linear-gradient(180deg, rgba(255,255,255,.012) 0 1px, transparent 1px 12px), linear-gradient(180deg, rgba(8,28,34,.92), rgba(4,18,23,.96))',
    cardLight: 'repeating-linear-gradient(180deg, rgba(34,211,238,.022) 0 1px, transparent 1px 12px), linear-gradient(180deg, rgba(255,255,255,.98), rgba(239,252,252,.99))',
    controlDark: 'repeating-linear-gradient(180deg, rgba(255,255,255,.012) 0 1px, transparent 1px 12px), linear-gradient(180deg, rgba(8,28,34,.94), rgba(4,18,23,.98))',
    controlLight: 'repeating-linear-gradient(180deg, rgba(34,211,238,.022) 0 1px, transparent 1px 12px), linear-gradient(180deg, rgba(255,255,255,.99), rgba(239,252,252,.99))',
    border: 'rgba(34,211,238,.18)',
    panelShadow: '0 18px 36px rgba(2,18,24,.28)',
    cardShadow: '0 12px 28px rgba(2,18,24,.20)',
    backdrop: 'none',
    kickerSpacing: '.16em',
    kickerShadow: '0 0 14px rgba(34,211,238,.22)'
  },
  demon: {
    bodyDark: 'radial-gradient(circle at 12% 0%, rgba(239, 68, 68, 0.16), transparent 20%), radial-gradient(circle at 88% 100%, rgba(190, 24, 93, 0.12), transparent 18%), linear-gradient(180deg, #0d0609 0%, #14090d 100%)',
    bodyLight: 'radial-gradient(circle at 12% 0%, rgba(248, 113, 113, 0.08), transparent 22%), linear-gradient(180deg, #fff8f8 0%, #feeff1 100%)',
    grid: 'linear-gradient(rgba(251,113,133,0.026) 1px, transparent 1px), linear-gradient(90deg, rgba(251,113,133,0.026) 1px, transparent 1px)',
    gridSize: '38px 38px',
    gridOpacity: '.11',
    panelDark: 'linear-gradient(180deg, rgba(30,12,16,.96), rgba(16,8,11,.995))',
    panelLight: 'linear-gradient(180deg, rgba(255,251,252,.985), rgba(252,241,244,.99))',
    cardDark: 'linear-gradient(180deg, rgba(39,14,18,.92), rgba(21,10,13,.97))',
    cardLight: 'linear-gradient(180deg, rgba(255,255,255,.985), rgba(253,243,246,.99))',
    controlDark: 'linear-gradient(180deg, rgba(39,14,18,.94), rgba(21,10,13,.985))',
    controlLight: 'linear-gradient(180deg, rgba(255,255,255,.99), rgba(253,243,246,.995))',
    border: 'rgba(248,113,113,.14)',
    panelShadow: '0 16px 34px rgba(19,7,10,.26)',
    cardShadow: '0 10px 22px rgba(19,7,10,.18)',
    backdrop: 'none',
    kickerSpacing: '.12em',
    kickerShadow: '0 0 16px rgba(248,113,113,.16)'
  },
  cyberpunk: {
    bodyDark: 'radial-gradient(circle at 8% 0%, rgba(236, 72, 153, 0.16), transparent 20%), radial-gradient(circle at 100% 100%, rgba(124, 58, 237, 0.16), transparent 20%), linear-gradient(180deg, #0a0714 0%, #110b1d 100%)',
    bodyLight: 'radial-gradient(circle at 10% 0%, rgba(236, 72, 153, 0.08), transparent 22%), radial-gradient(circle at 100% 100%, rgba(124, 58, 237, 0.07), transparent 18%), linear-gradient(180deg, #fff8fd 0%, #f3edff 100%)',
    grid: 'linear-gradient(rgba(168,85,247,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(236,72,153,0.04) 1px, transparent 1px), linear-gradient(135deg, rgba(236,72,153,0.035), transparent 45%)',
    gridSize: '30px 30px',
    gridOpacity: '.28',
    panelDark: 'linear-gradient(150deg, rgba(236,72,153,.07), transparent 34%), linear-gradient(330deg, rgba(139,92,246,.08), transparent 30%), linear-gradient(180deg, rgba(23,11,35,.96), rgba(13,8,23,.995))',
    panelLight: 'linear-gradient(150deg, rgba(236,72,153,.04), transparent 36%), linear-gradient(330deg, rgba(139,92,246,.05), transparent 30%), linear-gradient(180deg, rgba(255,251,254,.985), rgba(246,240,255,.99))',
    cardDark: 'linear-gradient(145deg, rgba(236,72,153,.06), transparent 42%), linear-gradient(180deg, rgba(29,12,41,.92), rgba(16,9,27,.97))',
    cardLight: 'linear-gradient(145deg, rgba(236,72,153,.03), transparent 42%), linear-gradient(180deg, rgba(255,255,255,.99), rgba(247,242,255,.99))',
    controlDark: 'linear-gradient(145deg, rgba(236,72,153,.06), transparent 42%), linear-gradient(180deg, rgba(29,12,41,.94), rgba(16,9,27,.985))',
    controlLight: 'linear-gradient(145deg, rgba(236,72,153,.03), transparent 42%), linear-gradient(180deg, rgba(255,255,255,.99), rgba(247,242,255,.995))',
    border: 'rgba(168,85,247,.16)',
    panelShadow: '0 16px 36px rgba(20,7,30,.26)',
    cardShadow: '0 10px 24px rgba(20,7,30,.18)',
    backdrop: 'none',
    kickerSpacing: '.14em',
    kickerShadow: '0 0 18px rgba(168,85,247,.16)'
  },
  vaporwave: {
    bodyDark: 'radial-gradient(circle at 12% 0%, rgba(255, 94, 169, 0.18), transparent 22%), radial-gradient(circle at 88% 100%, rgba(110, 231, 255, 0.16), transparent 20%), linear-gradient(180deg, #120a24 0%, #24113d 100%)',
    bodyLight: 'radial-gradient(circle at 12% 0%, rgba(255, 94, 169, 0.08), transparent 24%), radial-gradient(circle at 88% 100%, rgba(110, 231, 255, 0.08), transparent 22%), linear-gradient(180deg, #fff7ff 0%, #eef8ff 100%)',
    grid: 'linear-gradient(rgba(255,94,169,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(110,231,255,0.03) 1px, transparent 1px), linear-gradient(180deg, rgba(255,255,255,0.03), transparent 34%)',
    gridSize: '34px 34px',
    gridOpacity: '.24',
    panelDark: 'radial-gradient(circle at top center, rgba(255,94,169,.10), transparent 34%), linear-gradient(180deg, rgba(38,16,58,.94), rgba(20,11,36,.98))',
    panelLight: 'radial-gradient(circle at top center, rgba(255,94,169,.05), transparent 34%), linear-gradient(180deg, rgba(255,252,255,.985), rgba(241,248,255,.99))',
    cardDark: 'radial-gradient(circle at top left, rgba(110,231,255,.08), transparent 30%), linear-gradient(180deg, rgba(43,20,64,.9), rgba(24,13,40,.95))',
    cardLight: 'radial-gradient(circle at top left, rgba(110,231,255,.04), transparent 30%), linear-gradient(180deg, rgba(255,255,255,.99), rgba(246,242,255,.99))',
    controlDark: 'linear-gradient(145deg, rgba(255,94,169,.06), transparent 44%), linear-gradient(180deg, rgba(38,16,58,.94), rgba(20,11,36,.985))',
    controlLight: 'linear-gradient(145deg, rgba(255,94,169,.03), transparent 44%), linear-gradient(180deg, rgba(255,255,255,.99), rgba(246,242,255,.995))',
    border: 'rgba(255,94,169,.15)',
    panelShadow: '0 20px 40px rgba(19,8,31,.28)',
    cardShadow: '0 12px 26px rgba(19,8,31,.20)',
    backdrop: 'blur(18px) saturate(1.1)',
    kickerSpacing: '.18em',
    kickerShadow: '0 0 20px rgba(110,231,255,.18)'
  },
  aurora: {
    bodyDark: 'radial-gradient(circle at top left, rgba(94, 234, 212, 0.18), transparent 22%), radial-gradient(circle at top right, rgba(125, 211, 252, 0.16), transparent 18%), linear-gradient(180deg, #071716 0%, #0a1a21 100%)',
    bodyLight: 'radial-gradient(circle at top left, rgba(94, 234, 212, 0.08), transparent 22%), radial-gradient(circle at top right, rgba(125, 211, 252, 0.08), transparent 18%), linear-gradient(180deg, #f2fffb 0%, #e7f6fb 100%)',
    grid: 'linear-gradient(rgba(125,211,252,0.026) 1px, transparent 1px), linear-gradient(90deg, rgba(94,234,212,0.026) 1px, transparent 1px)',
    gridSize: '44px 44px',
    gridOpacity: '.16',
    panelDark: 'radial-gradient(circle at top left, rgba(125,211,252,.08), transparent 28%), linear-gradient(180deg, rgba(13,31,34,.84), rgba(8,21,28,.9))',
    panelLight: 'radial-gradient(circle at top left, rgba(125,211,252,.05), transparent 28%), linear-gradient(180deg, rgba(248,255,253,.96), rgba(239,250,248,.98))',
    cardDark: 'radial-gradient(circle at top left, rgba(125,211,252,.06), transparent 28%), linear-gradient(180deg, rgba(15,33,36,.82), rgba(10,23,30,.88))',
    cardLight: 'radial-gradient(circle at top left, rgba(125,211,252,.04), transparent 28%), linear-gradient(180deg, rgba(255,255,255,.98), rgba(241,253,249,.98))',
    controlDark: 'radial-gradient(circle at top left, rgba(125,211,252,.06), transparent 28%), linear-gradient(180deg, rgba(15,33,36,.84), rgba(10,23,30,.9))',
    controlLight: 'radial-gradient(circle at top left, rgba(125,211,252,.04), transparent 28%), linear-gradient(180deg, rgba(255,255,255,.99), rgba(241,253,249,.99))',
    border: 'rgba(125,211,252,.16)',
    panelShadow: '0 18px 34px rgba(4,20,24,.18)',
    cardShadow: '0 12px 24px rgba(4,20,24,.12)',
    backdrop: 'blur(18px) saturate(1.08)',
    kickerSpacing: '.14em',
    kickerShadow: 'none'
  },
  noctis: {
    bodyDark: 'radial-gradient(circle at top center, rgba(129, 140, 248, 0.12), transparent 22%), radial-gradient(circle at bottom left, rgba(59, 130, 246, 0.08), transparent 18%), linear-gradient(180deg, #040a14 0%, #08101b 100%)',
    bodyLight: 'radial-gradient(circle at top center, rgba(129, 140, 248, 0.06), transparent 22%), linear-gradient(180deg, #f4f7ff 0%, #e9effd 100%)',
    grid: 'linear-gradient(rgba(129,140,248,0.024) 1px, transparent 1px), linear-gradient(90deg, rgba(129,140,248,0.024) 1px, transparent 1px)',
    gridSize: '36px 36px',
    gridOpacity: '.12',
    panelDark: 'linear-gradient(180deg, rgba(10,17,31,.96), rgba(7,12,23,.99))',
    panelLight: 'linear-gradient(180deg, rgba(249,251,255,.98), rgba(241,246,255,.99))',
    cardDark: 'linear-gradient(180deg, rgba(13,20,36,.92), rgba(9,15,27,.96))',
    cardLight: 'linear-gradient(180deg, rgba(255,255,255,.99), rgba(244,247,255,.99))',
    controlDark: 'linear-gradient(180deg, rgba(13,20,36,.94), rgba(9,15,27,.98))',
    controlLight: 'linear-gradient(180deg, rgba(255,255,255,.99), rgba(244,247,255,.99))',
    border: 'rgba(129,140,248,.12)',
    panelShadow: 'inset 0 1px 0 rgba(255,255,255,.03), inset 0 0 0 1px rgba(129,140,248,.05), 0 18px 42px rgba(1,7,18,.34)',
    cardShadow: 'inset 0 1px 0 rgba(255,255,255,.03), 0 12px 24px rgba(1,7,18,.24)',
    backdrop: 'none',
    kickerSpacing: '.13em',
    kickerShadow: 'none'
  }
};

const UI_COPY = {
  pt: {
    common: {
      selectGroup: 'Selecione um grupo',
      selectGroupOption: '-- Selecione o grupo --',
      activeGroup: 'Grupo ativo',
      noGroups: 'Nenhum grupo monitorado.',
      save: 'Salvar',
      cancel: 'Cancelar',
      close: 'Fechar',
      add: 'Adicionar',
      remove: 'Remover',
      update: 'Atualizar',
      clear: 'Limpar',
      copy: 'Copiar',
      open: 'Abrir',
      show: 'Mostrar',
      hide: 'Ocultar',
      optional: 'Opcional',
      credentials: 'Credenciais'
    },
    notifications: {
      title: 'Notificacoes',
      empty: 'As ultimas notificacoes do bot vao aparecer aqui.',
      clearToast: 'Notificacoes removidas',
      joined: 'Entrou',
      left: 'Saiu',
      payment: 'Nova transacao',
      paymentCreatedTitle: 'Nova transacao recebida',
      paymentCreatedMessage: 'Uma nova cobranca apareceu no financeiro.',
      removeAria: 'Excluir notificacao',
      langToast: 'Idioma: Portugues',
      themeLightToast: 'Tema claro ativado',
      themeDarkToast: 'Tema escuro ativado'
    },
    topbar: {
      languageTitle: 'Idioma',
      themeTitle: 'Tema',
      refresh: 'Atualizar',
      refreshTitle: 'Atualizar agora',
      exportCsvTitle: 'Exportar CSV',
      exportPdfTitle: 'Exportar PDF',
      notificationsTitle: 'Notificacoes',
      closeNotifications: 'Fechar notificacoes'
    },
    home: {
      railLabel: 'Telas',
      kicker: 'Dashboard de navegacao',
      title: 'Escolha a area que voce quer abrir primeiro',
      copy: 'Use esta pagina inicial para entrar mais rapido nas telas do sistema, acompanhar o grupo ativo e gerar exportacoes com contexto.',
      groupLabel: 'Grupo ativo',
      groupsLabel: 'Grupos monitorados',
      eventsLabel: 'Eventos totais',
      membersLabel: 'Membros base',
      financeTotalLabel: 'Faturamento total',
      finance24hLabel: 'Transacoes nas ultimas 24h',
      financeApproved24hLabel: 'Finalizadas/aprovadas 24h',
      financeWeekLabel: 'Finalizadas/aprovadas na semana',
      financeSourceLabel: function(name) { return `Base financeira: ${name}`; },
      financeTotalLabelFor: function(name) { return `Faturamento total (${name})`; },
      finance24hLabelFor: function(name) { return `Transacoes 24h (${name})`; },
      financeApproved24hLabelFor: function(name) { return `Finalizadas/aprovadas 24h (${name})`; },
      financeWeekLabelFor: function(name) { return `Finalizadas/aprovadas semana (${name})`; },
      transactionsHeaderFor: function(name) { return `Ultimas transacoes (${name})`; },
      exportHeader: 'Central de exportacao',
      exportCopy: 'Crie um CSV bruto para analise operacional ou um PDF pronto para compartilhar.',
      exportCsv: 'Exportar CSV',
      exportPdf: 'Exportar PDF',
      exportNoteEmpty: 'Selecione um grupo no topo para liberar exportacoes contextualizadas.',
      exportNoteFilled: function(name) { return `Os arquivos serao gerados para ${name}.`; },
      transactionsHeader: 'Ultimas transacoes',
      transactionsEmpty: 'Nenhuma transacao recente encontrada.',
      transactionsSourceGlobal: 'Historico geral do painel',
    },
    launch: {
      overview: { kicker: 'Monitoramento', title: 'Overview', desc: 'Indicadores principais, insight rapido e atividade recente.' },
      charts: { kicker: 'Analise', title: 'Graficos', desc: 'Series temporais com entradas, saidas e crescimento do grupo.' },
      reports: { kicker: 'Resumo', title: 'Relatorios', desc: 'Semanal, mensal e anomalias consolidadas do grupo.' },
      events: { kicker: 'Auditoria', title: 'Eventos', desc: 'Consulte a fila completa de entradas e saidas por usuario.' },
      goals: { kicker: 'Planejamento', title: 'Metas', desc: 'Defina objetivos por grupo e acompanhe a execucao em tempo real.' },
      pixel: { kicker: 'Meta', title: 'PIXEL', desc: 'Conecte o Pixel da Meta, acompanhe campanhas, cliques e leads em um unico painel.' },
      finance: { kicker: 'Recebimentos', title: 'Financeiro', desc: 'Crie cobrancas PIX, acompanhe status e consolide pagamentos por grupo.' },
      'name-search': { kicker: 'Consulta', title: 'Consultas API', desc: 'Pesquise por nome, CPF, titulo, mae, pai ou RG e veja o retorno completo.' },
      members: { kicker: 'Base', title: 'Membros', desc: 'Veja admins, membros comuns e sincronize a base do Telegram.' },
      vault: { kicker: 'Seguranca', title: 'Cofre', desc: 'Acesse categorias e entradas seguras vinculadas ao projeto.' },
      scheduler: { kicker: 'Automacao', title: 'Agendador', desc: 'Crie e acompanhe mensagens agendadas por grupo.' },
      logs: { kicker: 'Diagnostico', title: 'Logs', desc: 'Monitore o comportamento do bot e investigue ocorrencias.' },
      settings: { kicker: 'Controle', title: 'Configuracoes', desc: 'Gerencie token, grupos monitorados e operacao do bot.' }
    },
    charts: {
      titles: ['Entradas vs Saidas', 'Crescimento liquido', 'Membros estimados'],
      joins: 'Entradas',
      leaves: 'Saidas',
      joinsMa: 'Entradas MA7',
      leavesMa: 'Saidas MA7',
      net: 'Crescimento liquido',
      members: 'Membros estimados'
    },
    events: {
      title: 'Eventos',
      searchPlaceholder: 'Buscar usuario ou @...',
      clearSearchAria: 'Limpar busca',
      filterAll: 'Todos',
      filterJoin: 'Entradas',
      filterLeave: 'Saidas',
      headers: ['#', 'Usuario', 'Tipo', 'Data'],
      selectGroup: 'Selecione um grupo.',
      empty: 'Nenhum evento encontrado.'
    },
    reports: {
      titles: ['Semanal', 'Mensal'],
      headersWeekly: ['Semana', 'Entradas', 'Saidas', 'Liquido'],
      headersMonthly: ['Mes', 'Entradas', 'Saidas', 'Liquido'],
      anomaliesTitle: 'Anomalias',
      noGroup: 'Selecione um grupo.',
      none: 'Nenhuma anomalia detectada.',
      peak: 'Pico',
      drop: 'Queda',
      joins: 'entradas',
      leaves: 'saidas',
      average: 'media'
    },
    goals: {
      emptyTitle: 'Selecione um grupo',
      emptyCopy: 'Escolha um grupo no topo para definir metas personalizadas e acompanhar o ritmo de crescimento.',
      titles: {
        weeklyJoins: 'Entradas semanais',
        monthlyNet: 'Liquido mensal',
        memberBase: 'Base de membros',
        maxChurn: 'Churn maximo'
      },
      labels: {
        currentTotal: 'Total atual',
        baseHealth: 'Saude da base',
        goalPrefix: 'Meta',
        noGroupTitle: 'Sem grupo ativo',
        waiting: 'Aguardando'
      },
      states: {
        underLimit: 'Dentro do limite',
        aboveLimit: 'Acima do limite',
        goalHit: 'Meta batida',
        onTrack: 'No ritmo',
        attention: 'Atencao'
      },
      details: {
        marginOf: function(v) { return `Margem de ${v}`; },
        aboveBy: function(v) { return `Acima em ${v}`; },
        exceededBy: function(v) { return `Superada por ${v}`; },
        missing: function(v) { return `Faltam ${v}`; },
        currentOfTarget: function(current, target) { return `Atual ${current} de ${target}.`; }
      },
      summaries: {
        perfect: 'Todas as metas principais estao sob controle.',
        good: 'Bom ritmo geral, com poucos ajustes pendentes.',
        low: 'Ha metas relevantes para recuperar no grupo ativo.'
      },
      groupTitle: function(name) { return `Metas de ${name}`; },
      groupCaption: function(name) { return `Use esta area para ajustar objetivos de ${name} e acompanhar o progresso com os dados reais do dashboard.`; },
      defaultTitle: 'Metas',
      defaultCaption: 'Defina objetivos por grupo e acompanhe a execucao em tempo real.',
      scoreEmpty: 'Selecione um grupo para acompanhar.',
      insightEmptyTitle: 'Sem grupo ativo',
      insightEmptyCopy: 'Escolha um grupo para liberar as metas personalizadas.',
      saveToast: 'Metas salvas para este grupo.',
      resetToast: 'Metas recalculadas com base no desempenho atual.',
      selectWarning: 'Selecione um grupo primeiro'
    },
    pixel: {
      kicker: 'Meta Ads',
      title: 'PIXEL',
      copy: 'Conecte sua conta da Meta para acompanhar o status das campanhas, cliques, leads e preparar o rastreamento completo com Pixel + Conversions API.',
      statusKicker: 'Status',
      statusWaiting: 'Integracao aguardando configuracao',
      statusReady: 'Integracao pronta para a proxima fase',
      statusCopyWaiting: 'Preencha as credenciais da Meta para liberar a sincronizacao das campanhas e dos eventos.',
      statusCopyReady: 'Credenciais salvas. Esta tela ja esta pronta para receber sincronizacao real da Meta.',
      connected: 'Conectado',
      disconnected: 'Nao conectado',
      neverSynced: 'Sem sincronizacao ainda',
      lastSyncPrefix: 'Ultima sincronizacao',
      metrics: ['Campanhas rodando', 'Campanhas pausadas', 'Cliques hoje', 'Leads hoje'],
      credentialsTitle: 'Credenciais da Meta',
      roadmapTitle: 'Escopo da integracao',
      fields: {
        pixelId: 'Pixel ID',
        adAccountId: 'Ad Account ID',
        accessToken: 'Access Token',
        datasetId: 'Dataset ID',
        testEventCode: 'Test Event Code'
      },
      placeholders: {
        pixelId: 'Ex.: 123456789012345',
        adAccountId: 'act_123456789012345',
        accessToken: 'Cole o token da Meta',
        datasetId: 'Opcional para CAPI',
        testEventCode: 'Opcional para validar eventos'
      },
      tokenConfigured: function(preview) { return `Token atual: ${preview || 'configurado'}.`; },
      tokenMissing: 'Token atual: nao configurado.',
      buttons: { save: 'Salvar configuracao', refresh: 'Atualizar status' },
      browserTitle: 'Pixel no navegador',
      browserCopy: 'Rastrear PageView, clique no CTA, inicio de checkout e lead diretamente no site.',
      capiTitle: 'Conversions API',
      capiCopy: 'Enviar os mesmos eventos pelo backend para reduzir perdas por bloqueadores e melhorar a atribuicao.',
      insightsTitle: 'Insights de campanhas',
      insightsCopy: 'Puxar status, cliques, leads e gasto da Meta para exibir campanhas rodando ou pausadas em tempo real.',
      nextStepLabel: 'Proximo passo',
      nextStepWaiting: 'Aguardando credenciais',
      nextStepReady: 'Conectar a Insights API',
      summaryTitle: 'Resumo da conexao',
      summaryLabels: ['Pixel ID conectado', 'Conta de anuncios', 'Dataset', 'Token'],
      notInformed: 'Nao informado',
      tokenNotConfigured: 'Nao configurado',
      saveToast: 'Configuracao da Meta salva.'
    },
    finance: {
      heroTitle: 'Central financeira PIXGO',
      heroCaption: 'Acompanhe status dos pagamentos, faturamento total e cobrancas pendentes em um unico lugar.',
      heroGroupTitle: function(name) { return `Financeiro de ${name}`; },
      heroGroupCaption: function(name) { return `Acompanhe status, pagamentos recebidos e faturamento vinculado a ${name}.`; },
      heroGlobalCaption: 'Use esta tela para acompanhar todos os pagamentos recebidos pela PIXGO, mesmo sem um grupo selecionado.',
      metrics: ['Faturamento total', 'Em aberto', 'Pagamentos', 'Taxa paga'],
      gatewayKicker: 'Gateway',
      gatewayReady: 'Integracao pronta. O painel ja pode receber webhooks, atualizar status e consolidar faturamento.',
      gatewayEmpty: 'Configure sua API key para liberar leitura de status e faturamento da PIXGO.',
      suggestedWebhook: 'Webhook sugerido',
      refreshStatus: 'Atualizar status',
      newCharge: 'Nova cobranca PIX',
      integrationTitle: 'Integracao PIXGO',
      importTitle: 'Importar historico',
      lookupTitle: 'Consultar transacao externa',
      activeChargeTitle: 'Cobranca ativa',
      historyTitle: 'Historico financeiro',
      accountFilterLabel: 'Conta PIXGO',
      accountFilterAll: 'Todas as contas',
      historyHeaders: ['Pagamento', 'Cliente', 'Valor', 'Status', 'Atualizado', 'Acao'],
      emptyActive: 'Selecione um pagamento para visualizar status, QR Code e dados completos.',
      emptyPayments: 'Nenhum pagamento encontrado ainda.',
      emptyFiltered: 'Nenhum pagamento encontrado para este filtro.',
      fields: {
        amount: 'Valor (R$)',
        description: 'Descricao',
        customerName: 'Nome do cliente',
        cpf: 'CPF',
        email: 'Email',
        phone: 'Telefone',
        address: 'Endereco do cliente (opcional)',
        apiKey: 'API Key',
        webhookPublic: 'Webhook publico',
        webhookSecret: 'Webhook secret',
        defaultDescription: 'Descricao padrao',
        importFile: 'Arquivo CSV ou JSON',
        importAccount: 'Conta PIXGO (opcional)',
        importText: 'Colar conteudo manual',
        lookupPaymentId: 'Payment ID',
        lookupAccount: 'Conta PIXGO (opcional)'
      },
      placeholders: {
        amount: '29.90',
        description: 'Acesso premium do grupo',
        customerName: 'Nome completo',
        cpf: 'Somente numeros',
        email: 'cliente@email.com',
        phone: 'DDD + numero',
        address: 'Rua, numero, bairro, cidade',
        apiKey: 'Cole a API key da PIXGO',
        webhookPublic: 'https://seu-dominio.com/api/finance/pixgo/webhook',
        webhookSecret: 'Opcional',
        defaultDescription: 'Cobranca TG Analytics',
        importAccount: 'Ex.: Vibratura ou Velatura',
        importText: 'Cole aqui um JSON ou CSV com colunas como payment_id, amount, status, customer_name, created_at',
        lookupPaymentId: 'Ex.: dep_1234567890abcdef',
        lookupAccount: 'Ex.: Vibratura ou Velatura'
      },
      notes: {
        payments: 'As cobrancas ficam salvas localmente no dashboard e o status pode ser atualizado em lote a qualquer momento.',
        webhook: 'Se o dashboard estiver em localhost, use um dominio publico ou tunel para receber webhooks da PIXGO.',
        import: 'Use esta area para importar transacoes antigas. O importador aceita JSON, lista JSON e CSV com colunas flexiveis, e atualiza pagamentos existentes pelo payment_id.',
        lookup: 'Use esta consulta quando a transacao foi criada fora do painel. Se voce informar a conta, a busca fica mais rapida.'
      },
      buttons: {
        refreshPanel: 'Atualizar painel',
        createCharge: 'Gerar cobranca PIX',
        saveIntegration: 'Salvar integracao',
        importHistory: 'Importar historico',
        clearImport: 'Limpar',
        lookupPayment: 'Buscar transacao',
        refreshPayment: 'Atualizar',
        copyPix: 'Copiar codigo',
        openQr: 'Abrir QR'
      },
      activeLabels: {
        amount: 'Valor',
        customer: 'Cliente',
        payment: 'Pagamento',
        expiresAt: 'Expira em',
        pixCode: 'Copia e cola PIX'
      },
      scopeGlobal: 'visao geral PIXGO',
      webhookExternal: 'Webhook externo',
      noDescription: 'Sem descricao',
      notProvided: 'Nao informado',
      qrPending: 'QR Code ainda nao retornado pela PIXGO.',
      saveToast: 'Integracao PIXGO salva.',
      createToast: 'Cobranca PIX criada com sucesso.',
      statusToast: 'Status atualizado.',
      copyToast: 'Codigo PIX copiado.',
      selectWarning: 'Selecione um grupo primeiro.',
      qrMissing: 'Essa cobranca ainda nao retornou um QR Code.',
      qrImageMissing: 'Essa cobranca nao retornou imagem do QR Code.',
      copyError: 'Nao foi possivel copiar o codigo PIX.',
      importToast: function(imported, skipped) { return skipped ? `${imported} transacoes importadas, ${skipped} ignoradas.` : `${imported} transacoes importadas com sucesso.`; },
      importEmpty: 'Selecione um arquivo ou cole um conteudo para importar.',
      lookupToast: 'Transacao carregada para o painel.',
      refreshManyToast: function(updated) { return updated ? `${updated} pagamentos atualizados.` : 'Nenhum pagamento precisou de atualizacao.'; }
    },
    nameSearch: {
      kicker: 'Consulta externa',
      title: 'Consultas API completas',
      copy: 'Consulte por nome, CPF, titulo, mae, pai ou RG e visualize toda a resposta sem sair do dashboard.',
      sideLabel: 'Fluxo rapido',
      sideTitle: 'Escolha o tipo e consulte',
      sideCopy: 'A tabela mostra cada registro retornado e o bloco abaixo exibe o JSON bruto completo, literalmente como veio da API.',
      placeholderByType: {
        nome: 'Digite o nome para pesquisar',
        cpf: 'Digite o CPF para pesquisar',
        titulo: 'Digite o titulo para pesquisar',
        mae: 'Digite o nome da mae para pesquisar',
        pai: 'Digite o nome do pai para pesquisar',
        rg: 'Digite o RG para pesquisar'
      },
      searchTypes: {
        nome: 'Nome',
        cpf: 'CPF',
        titulo: 'Titulo',
        mae: 'Mae',
        pai: 'Pai',
        rg: 'RG'
      },
      tableTitle: 'Registros retornados',
      structuredTitle: 'Leitura estruturada da resposta',
      structuredOverviewTitle: 'Resumo da consulta',
      structuredRootSummary: 'JSON bruto completo estruturado',
      structuredRootKey: 'ROOT',
      structuredFlatTitle: 'Tabela completa de campos (caminho -> valor)',
      structuredFlatCount: function(total) { return `${total} linha(s) estruturada(s)`; },
      structuredFlatHeaders: {
        path: 'Caminho',
        type: 'Tipo',
        value: 'Valor'
      },
      rawTitle: 'JSON completo retornado pela API',
      rawSummary: 'Abrir JSON bruto completo',
      recordRawSummary: 'Ver todos os campos deste registro',
      labels: {
        query: 'Consulta',
        type: 'Tipo',
        records: 'Registros em RESULTADOS',
        endpoint: 'Endpoint',
        source: 'Fonte'
      },
      nodeTypes: {
        object: 'objeto',
        array: 'lista',
        string: 'texto',
        number: 'numero',
        boolean: 'booleano',
        nullValue: 'nulo',
        undefinedValue: 'indefinido',
        empty: 'vazio'
      },
      headers: ['#', 'Tipo', 'Dados completos'],
      fields: {
        name: 'Nome',
        cpf: 'CPF',
        birth: 'Nascimento',
        sex: 'Sexo',
        mother: 'Mae',
        father: 'Pai',
        rg: 'RG',
        title: 'Titulo eleitor',
        phones: 'Telefones',
        emails: 'Emails',
        address: 'Endereco',
        contactsId: 'Contatos ID',
        cadastroId: 'Cadastro ID'
      },
      stats: {
        total: 'Resultados',
        records: 'Registros',
        jsonSize: 'Tamanho JSON'
      },
      buttons: {
        search: 'Pesquisar',
        clear: 'Limpar'
      },
      idle: 'Escolha o tipo, digite um valor e clique em pesquisar.',
      minChars: function(min, label) { return `Informe ao menos ${min} caractere(s) para ${label}.`; },
      loading: function(label) { return `Consultando API por ${label}...`; },
      empty: 'Nenhum registro encontrado na chave RESULTADOS.',
      rawIdle: 'Aguardando pesquisa.',
      found: function(total, query, label) { return `${total} registro(s) encontrado(s) para ${label} "${query}".`; }
    },
    members: {
      stats: ['Total', 'Admins', 'Membros'],
      searchPlaceholder: 'Buscar membro...',
      filters: { all: 'Todos', admin: 'Admins', member: 'Membros' },
      buttons: { sync: 'Sincronizar', syncFull: 'Sync Completo' },
      headers: ['#', 'Username', 'Nome', 'Tipo', 'Ultimo acesso'],
      empty: 'Nenhum membro encontrado.',
      noGroup: 'Selecione um grupo.',
      admin: 'Admin',
      member: 'Membro',
      syncNow: 'Sincronizando...',
      syncAll: 'Sincronizando todos os membros... pode demorar.',
      syncUnavailable: 'Nao foi possivel sincronizar agora.',
      selectWarning: 'Selecione um grupo primeiro.'
    },
    scheduler: {
      placeholder: 'Mensagem a enviar...',
      datetimeLabel: 'Data/Hora:',
      sent: 'Enviado',
      pending: 'Pendente',
      loadError: 'Erro ao carregar agendamentos.',
      selectWarning: 'Selecione um grupo.',
      messageRequired: 'Digite uma mensagem.',
      dateRequired: 'Selecione data e hora.',
      scheduled: 'Mensagem agendada!',
      scheduleError: 'Erro ao agendar mensagem.',
      removed: 'Agendamento removido.'
    },
    logs: {
      waiting: 'Aguardando logs do bot...',
      cleared: 'Log limpo.'
    },
    bot: {
      active: 'Bot Ativo',
      stopped: 'Bot Parado',
      noToken: 'Sem Token'
    },
    vault: {
      heroKicker: 'Credenciais',
      heroTitle: 'Cofre operacional',
      heroCopy: 'Organize tokens, logins, chaves e acessos internos com mascara para campos sensiveis, copia rapida auditada e gerador de senha integrado.',
      pills: [
        ['Uso', 'Equipe interna'],
        ['Protecao', 'Campos sensiveis mascarados'],
        ['Fluxo', 'Copia e historico rapido']
      ],
      categories: 'Categorias',
      newCategory: 'Nova categoria',
      searchPlaceholder: 'Busca global no cofre...',
      generatePassword: 'Gerar senha',
      history: 'Historico',
      selectCategory: 'Selecione uma categoria',
      selectCategoryHint: 'Selecione uma categoria a esquerda.',
      newEntry: 'Nova entrada',
      modal: {
        newEntry: 'Nova entrada',
        editEntry: 'Editar entrada',
        titleLabel: 'Titulo',
        titlePlaceholder: 'Ex: Gmail principal',
        fieldsLabel: 'Campos',
        addField: 'Adicionar campo',
        sensitiveField: 'Campo sensivel',
        notesLabel: 'Notas',
        notesPlaceholder: 'Observacoes...'
      },
      passwordModal: {
        title: 'Gerador de senhas',
        length: 'Comprimento',
        uppercase: 'Maiusculas',
        numbers: 'Numeros',
        symbols: 'Simbolos',
        generated: 'Senha gerada',
        close: 'Fechar',
        useInField: 'Usar no campo'
      },
      historyTitle: 'Historico de acessos',
      historyEmpty: 'Nenhum acesso registrado.',
      categoryModal: {
        title: 'Nova categoria',
        name: 'Nome',
        namePlaceholder: 'Ex: Redes Sociais',
        icon: 'Icone (emoji)',
        color: 'Cor',
        create: 'Criar'
      },
      noCategories: 'Nenhuma categoria.',
      noEntries: 'Nenhuma entrada ainda.',
      meta: 'Credenciais',
      show: 'Mostrar',
      hide: 'Ocultar',
      copy: 'Copiar',
      fieldPlaceholder: 'Campo',
      valuePlaceholder: 'Valor',
      sensitiveToggle: 'Sensivel',
      see: 'Ver',
      categoryNameRequired: 'Digite um nome para a categoria.',
      entryTitleRequired: 'Digite um titulo para a entrada.',
      passwordCopied: 'Senha copiada!',
      passwordUsed: 'Senha inserida no campo!',
      historyLoadError: 'Erro ao carregar historico.',
      removeCategoryAria: 'Remover categoria',
      removeCategoryConfirm: 'Remover categoria e todas as entradas?',
      removeEntryConfirm: 'Remover esta entrada?',
      noCopyField: 'Nao foi possivel copiar o campo.',
      copiedField: function(label) { return `\"${label}\" copiado!`; }
    },
    settings: {
      heroKicker: 'Painel de controle',
      heroTitle: 'Configuracoes do produto',
      heroCopy: 'Organize aparencia, automacao, grupos, acessos e entrega em areas mais claras, com menos ruido visual e mais contexto por categoria.',
      heroSideLabel: 'Navegacao contextual',
      heroSideTitle: 'Cada categoria agrupa uma responsabilidade do sistema',
      heroSideCopy: 'Use os chips abaixo para alternar entre identidade visual, operacao do bot, estrutura de acesso e automacoes de entrega.',
      categories: {
        appearance: 'Aparencia',
        bot: 'Bot',
        groups: 'Grupos',
        access: 'Acesso',
        delivery: 'Entrega'
      },
      appearanceTitle: 'Aparencia do painel',
      appearanceCopy: 'Escolha o modo base, o estilo visual e a identidade do seu perfil dentro do dashboard.',
      modeLabel: 'Modo base',
      presetLabel: 'Estilo visual',
      profileLabel: 'Perfil visual',
      profilePhoto: 'URL da foto',
      profileTitle: 'Cargo / assinatura',
      profileBio: 'Descricao curta',
      motionLabel: 'Animacao',
      motionCalm: 'Calma',
      motionStandard: 'Padrao',
      motionExpressive: 'Expressiva',
      profilePreview: 'Prever visual',
      profileSave: 'Salvar perfil',
      profileSaved: 'Perfil visual atualizado.',
      profileTitleFallback: 'Administrador',
      light: 'Claro',
      dark: 'Escuro',
      tokenTitle: 'Token do Bot',
      tokenPlaceholderReady: 'token ja configurado',
      tokenPlaceholderNew: '1234567890:ABCdef...',
      groupsTitle: 'Grupos Monitorados',
      groupNamePlaceholder: 'Nome (opcional)',
      buttons: { save: 'Salvar', start: 'Iniciar', stop: 'Parar', add: 'Adicionar' },
      headers: ['Chat ID', 'Nome', 'Desde', 'Ultimo evento', 'Acao'],
      removeConfirm: function(cid) { return `Remover grupo ${cid} e todos os dados?`; },
      tokenRequired: 'Digite o token.',
      groupRequired: 'Digite o chat_id.'
    },
    statuses: {
      paid: 'Pago',
      approved: 'Aprovado',
      completed: 'Concluido',
      success: 'Sucesso',
      succeeded: 'Sucesso',
      pending: 'Pendente',
      created: 'Criado',
      processing: 'Processando',
      waiting_payment: 'Aguardando pagamento',
      waiting: 'Aguardando',
      open: 'Aberto',
      expired: 'Expirado',
      failed: 'Falhou',
      cancelled: 'Cancelado',
      canceled: 'Cancelado',
      refused: 'Recusado',
      voided: 'Anulado'
    }
  },
  en: {
    common: {
      selectGroup: 'Select a group',
      selectGroupOption: '-- Select group --',
      activeGroup: 'Active group',
      noGroups: 'No monitored groups.',
      save: 'Save',
      cancel: 'Cancel',
      close: 'Close',
      add: 'Add',
      remove: 'Remove',
      update: 'Update',
      clear: 'Clear',
      copy: 'Copy',
      open: 'Open',
      show: 'Show',
      hide: 'Hide',
      optional: 'Optional',
      credentials: 'Credentials'
    },
    notifications: {
      title: 'Notifications',
      empty: 'The latest bot notifications will appear here.',
      clearToast: 'Notifications cleared',
      joined: 'Joined',
      left: 'Left',
      payment: 'New transaction',
      paymentCreatedTitle: 'New transaction received',
      paymentCreatedMessage: 'A new charge was added to finance.',
      removeAria: 'Delete notification',
      langToast: 'Language: English',
      themeLightToast: 'Light theme enabled',
      themeDarkToast: 'Dark theme enabled'
    },
    topbar: {
      languageTitle: 'Language',
      themeTitle: 'Theme',
      refresh: 'Refresh',
      refreshTitle: 'Refresh now',
      exportCsvTitle: 'Export CSV',
      exportPdfTitle: 'Export PDF',
      notificationsTitle: 'Notifications',
      closeNotifications: 'Close notifications'
    },
    home: {
      railLabel: 'Screens',
      kicker: 'Navigation dashboard',
      title: 'Choose the area you want to open first',
      copy: 'Use this landing page to jump faster into the system areas, follow the active group and export with context.',
      groupLabel: 'Active group',
      groupsLabel: 'Monitored groups',
      eventsLabel: 'Total events',
      membersLabel: 'Member base',
      financeTotalLabel: 'Total revenue',
      finance24hLabel: 'Transactions in the last 24h',
      financeApproved24hLabel: 'Approved/completed in the last 24h',
      financeWeekLabel: 'Approved/completed this week',
      financeSourceLabel: function(name) { return `Financial base: ${name}`; },
      financeTotalLabelFor: function(name) { return `Total revenue (${name})`; },
      finance24hLabelFor: function(name) { return `Transactions 24h (${name})`; },
      financeApproved24hLabelFor: function(name) { return `Approved/completed 24h (${name})`; },
      financeWeekLabelFor: function(name) { return `Approved/completed week (${name})`; },
      transactionsHeaderFor: function(name) { return `Latest transactions (${name})`; },
      exportHeader: 'Export center',
      exportCopy: 'Create a raw CSV for operations or a polished PDF ready to share.',
      exportCsv: 'Export CSV',
      exportPdf: 'Export PDF',
      exportNoteEmpty: 'Select a group at the top to enable contextual exports.',
      exportNoteFilled: function(name) { return `Files will be generated for ${name}.`; },
      transactionsHeader: 'Latest transactions',
      transactionsEmpty: 'No recent transactions found.',
      transactionsSourceGlobal: 'Global panel history',
    },
    launch: {
      overview: { kicker: 'Monitoring', title: 'Overview', desc: 'Main KPIs, quick insights and recent activity.' },
      charts: { kicker: 'Analysis', title: 'Charts', desc: 'Time series for joins, leaves and group growth.' },
      reports: { kicker: 'Summary', title: 'Reports', desc: 'Weekly, monthly and anomaly summaries for the group.' },
      events: { kicker: 'Audit', title: 'Events', desc: 'Inspect the full trail of joins and leaves by user.' },
      goals: { kicker: 'Planning', title: 'Goals', desc: 'Set goals by group and follow execution in real time.' },
      pixel: { kicker: 'Meta', title: 'PIXEL', desc: 'Connect Meta Pixel and monitor campaigns, clicks and leads in one place.' },
      finance: { kicker: 'Revenue', title: 'Finance', desc: 'Create PIX charges, track status and consolidate payments by group.' },
      'name-search': { kicker: 'Lookup', title: 'API lookups', desc: 'Search by name, CPF, voter ID, mother, father or RG and inspect the full payload.' },
      members: { kicker: 'Base', title: 'Members', desc: 'See admins, members and sync the Telegram base.' },
      vault: { kicker: 'Security', title: 'Vault', desc: 'Access secure categories and protected project entries.' },
      scheduler: { kicker: 'Automation', title: 'Scheduler', desc: 'Create and monitor scheduled messages by group.' },
      logs: { kicker: 'Diagnostics', title: 'Logs', desc: 'Monitor bot behavior and investigate occurrences.' },
      settings: { kicker: 'Control', title: 'Settings', desc: 'Manage token, monitored groups and bot operation.' }
    },
    charts: {
      titles: ['Joins vs Leaves', 'Net growth', 'Estimated members'],
      joins: 'Joins',
      leaves: 'Leaves',
      joinsMa: 'Joins MA7',
      leavesMa: 'Leaves MA7',
      net: 'Net growth',
      members: 'Estimated members'
    },
    events: {
      title: 'Events',
      searchPlaceholder: 'Search user or @...',
      clearSearchAria: 'Clear search',
      filterAll: 'All',
      filterJoin: 'Joins',
      filterLeave: 'Leaves',
      headers: ['#', 'User', 'Type', 'Date'],
      selectGroup: 'Select a group.',
      empty: 'No events found.'
    },
    reports: {
      titles: ['Weekly', 'Monthly'],
      headersWeekly: ['Week', 'Joins', 'Leaves', 'Net'],
      headersMonthly: ['Month', 'Joins', 'Leaves', 'Net'],
      anomaliesTitle: 'Anomalies',
      noGroup: 'Select a group.',
      none: 'No anomalies detected.',
      peak: 'Peak',
      drop: 'Drop',
      joins: 'joins',
      leaves: 'leaves',
      average: 'avg'
    },
    goals: {
      emptyTitle: 'Select a group',
      emptyCopy: 'Choose a group at the top to define custom goals and track growth pace.',
      titles: {
        weeklyJoins: 'Weekly joins',
        monthlyNet: 'Monthly net',
        memberBase: 'Member base',
        maxChurn: 'Max churn'
      },
      labels: {
        currentTotal: 'Current total',
        baseHealth: 'Base health',
        goalPrefix: 'Goal',
        noGroupTitle: 'No active group',
        waiting: 'Waiting'
      },
      states: {
        underLimit: 'Within limit',
        aboveLimit: 'Above limit',
        goalHit: 'Goal reached',
        onTrack: 'On track',
        attention: 'Attention'
      },
      details: {
        marginOf: function(v) { return `Margin of ${v}`; },
        aboveBy: function(v) { return `Above by ${v}`; },
        exceededBy: function(v) { return `Exceeded by ${v}`; },
        missing: function(v) { return `${v} remaining`; },
        currentOfTarget: function(current, target) { return `Current ${current} of ${target}.`; }
      },
      summaries: {
        perfect: 'All major goals are under control.',
        good: 'Good overall pace, with only a few adjustments pending.',
        low: 'There are relevant goals to recover for the active group.'
      },
      groupTitle: function(name) { return `${name} goals`; },
      groupCaption: function(name) { return `Use this area to adjust goals for ${name} and track progress using the real dashboard data.`; },
      defaultTitle: 'Goals',
      defaultCaption: 'Set goals by group and follow execution in real time.',
      scoreEmpty: 'Select a group to start tracking.',
      insightEmptyTitle: 'No active group',
      insightEmptyCopy: 'Choose a group to unlock custom goals.',
      saveToast: 'Goals saved for this group.',
      resetToast: 'Goals recalculated from current performance.',
      selectWarning: 'Select a group first'
    },
    pixel: {
      kicker: 'Meta Ads',
      title: 'PIXEL',
      copy: 'Connect your Meta account to track campaign status, clicks, leads and prepare full tracking with Pixel + Conversions API.',
      statusKicker: 'Status',
      statusWaiting: 'Integration waiting for configuration',
      statusReady: 'Integration ready for the next phase',
      statusCopyWaiting: 'Fill in your Meta credentials to unlock campaign and event synchronization.',
      statusCopyReady: 'Credentials saved. This screen is ready to receive live Meta synchronization.',
      connected: 'Connected',
      disconnected: 'Not connected',
      neverSynced: 'No sync yet',
      lastSyncPrefix: 'Last sync',
      metrics: ['Running campaigns', 'Paused campaigns', 'Clicks today', 'Leads today'],
      credentialsTitle: 'Meta credentials',
      roadmapTitle: 'Integration scope',
      fields: {
        pixelId: 'Pixel ID',
        adAccountId: 'Ad Account ID',
        accessToken: 'Access Token',
        datasetId: 'Dataset ID',
        testEventCode: 'Test Event Code'
      },
      placeholders: {
        pixelId: 'Example: 123456789012345',
        adAccountId: 'act_123456789012345',
        accessToken: 'Paste your Meta token',
        datasetId: 'Optional for CAPI',
        testEventCode: 'Optional for event testing'
      },
      tokenConfigured: function(preview) { return `Current token: ${preview || 'configured'}.`; },
      tokenMissing: 'Current token: not configured.',
      buttons: { save: 'Save configuration', refresh: 'Refresh status' },
      browserTitle: 'Browser Pixel',
      browserCopy: 'Track PageView, CTA click, checkout start and lead events directly on the site.',
      capiTitle: 'Conversions API',
      capiCopy: 'Send the same events from the backend to reduce browser loss and improve attribution.',
      insightsTitle: 'Campaign insights',
      insightsCopy: 'Pull status, clicks, leads and spend from Meta to show running or paused campaigns in real time.',
      nextStepLabel: 'Next step',
      nextStepWaiting: 'Waiting for credentials',
      nextStepReady: 'Connect the Insights API',
      summaryTitle: 'Connection summary',
      summaryLabels: ['Connected Pixel ID', 'Ad account', 'Dataset', 'Token'],
      notInformed: 'Not informed',
      tokenNotConfigured: 'Not configured',
      saveToast: 'Meta configuration saved.'
    },
    finance: {
      heroTitle: 'PIXGO finance center',
      heroCaption: 'Track payment status, total revenue and open charges in one place.',
      heroGroupTitle: function(name) { return `${name} finance`; },
      heroGroupCaption: function(name) { return `Track status, received payments and revenue linked to ${name}.`; },
      heroGlobalCaption: 'Use this screen to follow every PIXGO payment, even without a selected group.',
      metrics: ['Total revenue', 'Open amount', 'Payments', 'Paid rate'],
      gatewayKicker: 'Gateway',
      gatewayReady: 'Integration ready. The panel can now receive webhooks, refresh statuses and consolidate revenue.',
      gatewayEmpty: 'Configure your API key to enable PIXGO status and revenue reading.',
      suggestedWebhook: 'Suggested webhook',
      refreshStatus: 'Refresh status',
      newCharge: 'New PIX charge',
      integrationTitle: 'PIXGO integration',
      importTitle: 'Import history',
      lookupTitle: 'Lookup external transaction',
      activeChargeTitle: 'Active charge',
      historyTitle: 'Finance history',
      accountFilterLabel: 'PIXGO account',
      accountFilterAll: 'All accounts',
      historyHeaders: ['Payment', 'Customer', 'Amount', 'Status', 'Updated', 'Action'],
      emptyActive: 'Select a payment to view status, QR code and full details.',
      emptyPayments: 'No payments found yet.',
      emptyFiltered: 'No payments found for this filter.',
      fields: {
        amount: 'Amount (BRL)',
        description: 'Description',
        customerName: 'Customer name',
        cpf: 'CPF',
        email: 'Email',
        phone: 'Phone',
        address: 'Customer address (optional)',
        apiKey: 'API Key',
        webhookPublic: 'Public webhook',
        webhookSecret: 'Webhook secret',
        defaultDescription: 'Default description',
        importFile: 'CSV or JSON file',
        importAccount: 'PIXGO account (optional)',
        importText: 'Paste content manually',
        lookupPaymentId: 'Payment ID',
        lookupAccount: 'PIXGO account (optional)'
      },
      placeholders: {
        amount: '29.90',
        description: 'Premium access',
        customerName: 'Full name',
        cpf: 'Digits only',
        email: 'customer@email.com',
        phone: 'Area code + number',
        address: 'Street, number, city, district',
        apiKey: 'Paste the PIXGO API key',
        webhookPublic: 'https://your-domain.com/api/finance/pixgo/webhook',
        webhookSecret: 'Optional',
        defaultDescription: 'TG Analytics charge',
        importAccount: 'Example: Vibratura or Velatura',
        importText: 'Paste a JSON or CSV here with columns such as payment_id, amount, status, customer_name, created_at',
        lookupPaymentId: 'Example: dep_1234567890abcdef',
        lookupAccount: 'Example: Vibratura or Velatura'
      },
      notes: {
        payments: 'Charges are stored locally in the dashboard and their statuses can be batch refreshed at any time.',
        webhook: 'If the dashboard runs on localhost, use a public domain or tunnel to receive PIXGO webhooks.',
        import: 'Use this area to import old transactions. The importer accepts JSON, JSON lists and CSV with flexible columns, and updates existing payments by payment_id.',
        lookup: 'Use this lookup when the transaction was created outside the panel. If you provide the account, the search is faster.'
      },
      buttons: {
        refreshPanel: 'Refresh panel',
        createCharge: 'Create PIX charge',
        saveIntegration: 'Save integration',
        importHistory: 'Import history',
        clearImport: 'Clear',
        lookupPayment: 'Lookup transaction',
        refreshPayment: 'Refresh',
        copyPix: 'Copy code',
        openQr: 'Open QR'
      },
      activeLabels: {
        amount: 'Amount',
        customer: 'Customer',
        payment: 'Payment',
        expiresAt: 'Expires at',
        pixCode: 'PIX copy-and-paste'
      },
      scopeGlobal: 'PIXGO overview',
      webhookExternal: 'External webhook',
      noDescription: 'No description',
      notProvided: 'Not provided',
      qrPending: 'PIXGO has not returned a QR code yet.',
      saveToast: 'PIXGO integration saved.',
      createToast: 'PIX charge created successfully.',
      statusToast: 'Status refreshed.',
      copyToast: 'PIX code copied.',
      selectWarning: 'Select a group first.',
      qrMissing: 'This charge does not have a QR code yet.',
      qrImageMissing: 'This charge did not return a QR image.',
      copyError: 'Could not copy the PIX code.',
      importToast: function(imported, skipped) { return skipped ? `${imported} transactions imported, ${skipped} skipped.` : `${imported} transactions imported successfully.`; },
      importEmpty: 'Select a file or paste content to import.',
      lookupToast: 'Transaction loaded into the panel.',
      refreshManyToast: function(updated) { return updated ? `${updated} payments refreshed.` : 'No payment required a refresh.'; }
    },
    nameSearch: {
      kicker: 'External lookup',
      title: 'Full API lookups',
      copy: 'Search by name, CPF, voter ID, mother, father or RG and inspect the full API payload without leaving the dashboard.',
      sideLabel: 'Quick flow',
      sideTitle: 'Choose a type and query',
      sideCopy: 'The table shows each returned record and the panel below prints the raw JSON exactly as returned by the API.',
      placeholderByType: {
        nome: 'Type a name to search',
        cpf: 'Type a CPF to search',
        titulo: 'Type a voter ID to search',
        mae: 'Type the mother name to search',
        pai: 'Type the father name to search',
        rg: 'Type an RG to search'
      },
      searchTypes: {
        nome: 'Name',
        cpf: 'CPF',
        titulo: 'Voter ID',
        mae: 'Mother',
        pai: 'Father',
        rg: 'RG'
      },
      tableTitle: 'Returned records',
      structuredTitle: 'Structured response view',
      structuredOverviewTitle: 'Query summary',
      structuredRootSummary: 'Fully structured raw JSON',
      structuredRootKey: 'ROOT',
      structuredFlatTitle: 'Complete field table (path -> value)',
      structuredFlatCount: function(total) { return `${total} structured row(s)`; },
      structuredFlatHeaders: {
        path: 'Path',
        type: 'Type',
        value: 'Value'
      },
      rawTitle: 'Full raw JSON response',
      rawSummary: 'Open full raw JSON',
      recordRawSummary: 'Show every field from this record',
      labels: {
        query: 'Query',
        type: 'Type',
        records: 'Records in RESULTADOS',
        endpoint: 'Endpoint',
        source: 'Source'
      },
      nodeTypes: {
        object: 'object',
        array: 'list',
        string: 'text',
        number: 'number',
        boolean: 'boolean',
        nullValue: 'null',
        undefinedValue: 'undefined',
        empty: 'empty'
      },
      headers: ['#', 'Type', 'Full data'],
      fields: {
        name: 'Name',
        cpf: 'CPF',
        birth: 'Birth',
        sex: 'Sex',
        mother: 'Mother',
        father: 'Father',
        rg: 'RG',
        title: 'Voter ID',
        phones: 'Phones',
        emails: 'Emails',
        address: 'Address',
        contactsId: 'Contacts ID',
        cadastroId: 'Registration ID'
      },
      stats: {
        total: 'Results',
        records: 'Records',
        jsonSize: 'JSON size'
      },
      buttons: {
        search: 'Search',
        clear: 'Clear'
      },
      idle: 'Choose the type, type a value and click search.',
      minChars: function(min, label) { return `Enter at least ${min} character(s) for ${label}.`; },
      loading: function(label) { return `Querying API by ${label}...`; },
      empty: 'No records found in RESULTADOS.',
      rawIdle: 'Waiting for a search.',
      found: function(total, query, label) { return `${total} record(s) found for ${label} "${query}".`; }
    },
    members: {
      stats: ['Total', 'Admins', 'Members'],
      searchPlaceholder: 'Search member...',
      filters: { all: 'All', admin: 'Admins', member: 'Members' },
      buttons: { sync: 'Sync', syncFull: 'Full sync' },
      headers: ['#', 'Username', 'Name', 'Type', 'Last access'],
      empty: 'No members found.',
      noGroup: 'Select a group.',
      admin: 'Admin',
      member: 'Member',
      syncNow: 'Syncing...',
      syncAll: 'Syncing all members... this may take a while.',
      syncUnavailable: 'Could not sync right now.',
      selectWarning: 'Select a group first.'
    },
    scheduler: {
      placeholder: 'Message to send...',
      datetimeLabel: 'Date/Time:',
      sent: 'Sent',
      pending: 'Pending',
      loadError: 'Could not load schedules.',
      selectWarning: 'Select a group.',
      messageRequired: 'Enter a message.',
      dateRequired: 'Select date and time.',
      scheduled: 'Message scheduled!',
      scheduleError: 'Could not schedule the message.',
      removed: 'Schedule removed.'
    },
    logs: {
      waiting: 'Waiting for bot logs...',
      cleared: 'Log cleared.'
    },
    bot: {
      active: 'Bot Active',
      stopped: 'Bot Stopped',
      noToken: 'No Token'
    },
    vault: {
      heroKicker: 'Credentials',
      heroTitle: 'Operational vault',
      heroCopy: 'Organize tokens, logins, keys and internal access with masking for sensitive fields, audited quick copy and a built-in password generator.',
      pills: [
        ['Usage', 'Internal team'],
        ['Protection', 'Sensitive fields masked'],
        ['Flow', 'Quick copy and history']
      ],
      categories: 'Categories',
      newCategory: 'New category',
      searchPlaceholder: 'Global vault search...',
      generatePassword: 'Generate password',
      history: 'History',
      selectCategory: 'Select a category',
      selectCategoryHint: 'Select a category on the left.',
      newEntry: 'New entry',
      modal: {
        newEntry: 'New entry',
        editEntry: 'Edit entry',
        titleLabel: 'Title',
        titlePlaceholder: 'Example: Primary Gmail',
        fieldsLabel: 'Fields',
        addField: 'Add field',
        sensitiveField: 'Sensitive field',
        notesLabel: 'Notes',
        notesPlaceholder: 'Notes...'
      },
      passwordModal: {
        title: 'Password generator',
        length: 'Length',
        uppercase: 'Uppercase',
        numbers: 'Numbers',
        symbols: 'Symbols',
        generated: 'Generated password',
        close: 'Close',
        useInField: 'Use in field'
      },
      historyTitle: 'Access history',
      historyEmpty: 'No access recorded.',
      categoryModal: {
        title: 'New category',
        name: 'Name',
        namePlaceholder: 'Example: Social Media',
        icon: 'Icon (emoji)',
        color: 'Color',
        create: 'Create'
      },
      noCategories: 'No categories.',
      noEntries: 'No entries yet.',
      meta: 'Credentials',
      show: 'Show',
      hide: 'Hide',
      copy: 'Copy',
      fieldPlaceholder: 'Field',
      valuePlaceholder: 'Value',
      sensitiveToggle: 'Sensitive',
      see: 'View',
      categoryNameRequired: 'Enter a category name.',
      entryTitleRequired: 'Enter an entry title.',
      passwordCopied: 'Password copied!',
      passwordUsed: 'Password inserted into the field!',
      historyLoadError: 'Could not load history.',
      removeCategoryAria: 'Remove category',
      removeCategoryConfirm: 'Remove category and all entries?',
      removeEntryConfirm: 'Remove this entry?',
      noCopyField: 'Could not copy this field.',
      copiedField: function(label) { return `\"${label}\" copied!`; }
    },
    settings: {
      heroKicker: 'Control panel',
      heroTitle: 'Product settings',
      heroCopy: 'Organize appearance, automation, groups, access and delivery into clearer areas, with less visual noise and more context by category.',
      heroSideLabel: 'Contextual navigation',
      heroSideTitle: 'Each category groups one system responsibility',
      heroSideCopy: 'Use the chips below to switch between visual identity, bot operations, access structure and delivery automations.',
      categories: {
        appearance: 'Appearance',
        bot: 'Bot',
        groups: 'Groups',
        access: 'Access',
        delivery: 'Delivery'
      },
      appearanceTitle: 'Panel appearance',
      appearanceCopy: 'Choose the base mode, the visual style and the identity of your profile inside the dashboard.',
      modeLabel: 'Base mode',
      presetLabel: 'Visual style',
      profileLabel: 'Visual profile',
      profilePhoto: 'Photo URL',
      profileTitle: 'Role / signature',
      profileBio: 'Short description',
      motionLabel: 'Animation',
      motionCalm: 'Calm',
      motionStandard: 'Standard',
      motionExpressive: 'Expressive',
      profilePreview: 'Preview visual',
      profileSave: 'Save profile',
      profileSaved: 'Visual profile updated.',
      profileTitleFallback: 'Administrator',
      light: 'Light',
      dark: 'Dark',
      tokenTitle: 'Bot token',
      tokenPlaceholderReady: 'token already configured',
      tokenPlaceholderNew: '1234567890:ABCdef...',
      groupsTitle: 'Monitored groups',
      groupNamePlaceholder: 'Name (optional)',
      buttons: { save: 'Save', start: 'Start', stop: 'Stop', add: 'Add' },
      headers: ['Chat ID', 'Name', 'Since', 'Last event', 'Action'],
      removeConfirm: function(cid) { return `Remove group ${cid} and all data?`; },
      tokenRequired: 'Enter the token.',
      groupRequired: 'Enter the chat_id.'
    },
    statuses: {
      paid: 'Paid',
      approved: 'Approved',
      completed: 'Completed',
      success: 'Success',
      succeeded: 'Success',
      pending: 'Pending',
      created: 'Created',
      processing: 'Processing',
      waiting_payment: 'Waiting payment',
      waiting: 'Waiting',
      open: 'Open',
      expired: 'Expired',
      failed: 'Failed',
      cancelled: 'Cancelled',
      canceled: 'Cancelled',
      refused: 'Refused',
      voided: 'Voided'
    }
  }
};

function el(id) { return document.getElementById(id); }
function detectPerformanceProfile() {
  const nav = window.navigator || {};
  const ua = String(nav.userAgent || '');
  const isFirefox = /firefox/i.test(ua);
  const isSafari = /safari/i.test(ua) && !/chrome|chromium|edg/i.test(ua);
  const reducedMotion = Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const saveData = Boolean(nav.connection && nav.connection.saveData);
  const lowCores = Number(nav.hardwareConcurrency || 0) > 0 && Number(nav.hardwareConcurrency) <= 4;
  const lowMemory = Number(nav.deviceMemory || 0) > 0 && Number(nav.deviceMemory) <= 4;
  return {
    isFirefox: isFirefox,
    isSafari: isSafari,
    reducedMotion: reducedMotion,
    saveData: saveData,
    lowCores: lowCores,
    lowMemory: lowMemory,
    isConservative: Boolean(reducedMotion || saveData || lowCores || lowMemory),
  };
}
function getLocale() { return currentLang === 'en' ? 'en-US' : 'pt-BR'; }
function getPanelTimeZone() { return 'America/Sao_Paulo'; }
function parsePanelDateTime(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;
  const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const hasZone = /(?:Z|[+\-]\d{2}:\d{2})$/i.test(normalized);
  const date = new Date(hasZone ? normalized : `${normalized}-03:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}
function formatPanelDateTimeParts(value) {
  const date = parsePanelDateTime(value);
  if (!date) return null;
  const parts = new Intl.DateTimeFormat('pt-BR', {
    timeZone: getPanelTimeZone(),
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).formatToParts(date);
  const pick = function(type) {
    const match = parts.find(function(part) { return part.type === type; });
    return match ? match.value : '';
  };
  return {
    date: `${pick('day')}/${pick('month')}/${pick('year')}`,
    time: `${pick('hour')}:${pick('minute')}:${pick('second')}`
  };
}
function fmt(d) {
  const parts = formatPanelDateTimeParts(d);
  return parts ? `${parts.date} - ${parts.time}` : '-';
}
function fmtT(d) {
  const parts = formatPanelDateTimeParts(d);
  return parts ? parts.time : '-';
}

function getUiText() {
  return UI_COPY[currentLang] || UI_COPY.pt;
}

function setText(selector, value) {
  const node = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (node && typeof value !== 'undefined' && value !== null) node.textContent = value;
}

function setPlaceholder(selector, value) {
  const node = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (node && typeof value !== 'undefined' && value !== null) node.placeholder = value;
}

function setButtonLabel(selector, value) {
  const node = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (!node || typeof value === 'undefined' || value === null) return;
  const svg = node.querySelector('svg');
  if (!svg) {
    node.textContent = value;
    return;
  }
  Array.from(node.childNodes).forEach(function(child) {
    if (child !== svg) child.remove();
  });
  node.appendChild(document.createTextNode(' ' + value));
}

function scheduleActiveViewRefresh(delay) {
  if (document.hidden) return;
  if (activeViewRefreshTimer) clearTimeout(activeViewRefreshTimer);
  activeViewRefreshTimer = setTimeout(async function() {
    activeViewRefreshTimer = null;
    try {
      await loadActiveView(false);
    } catch (e) {
      console.warn('scheduled view refresh failed:', e);
    }
  }, typeof delay === 'number' ? delay : 220);
}

function setInlineControlLabel(selector, value) {
  const node = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (!node || typeof value === 'undefined' || value === null) return;
  const control = node.querySelector('input');
  if (!control) {
    node.textContent = value;
    return;
  }
  Array.from(node.childNodes).forEach(function(child) {
    if (child !== control) child.remove();
  });
  node.appendChild(document.createTextNode(' ' + value));
}

function loadStoredNotifications() {
  return [];
}

function saveNotifications() {
  localStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(notificationItems.slice(0, MAX_NOTIFICATIONS)));
}

notificationItems = loadStoredNotifications();

function parseNotificationOccurredAt(value) {
  const raw = String(value || '').trim();
  if (!raw) return 0;
  const normalized = raw.replace('T', ' ').replace(/\.\d+$/, '');
  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?$/);
  if (match) {
    return new Date(
      Number(match[1]),
      Number(match[2]) - 1,
      Number(match[3]),
      Number(match[4]),
      Number(match[5]),
      Number(match[6] || 0)
    ).getTime();
  }
  const parsed = Date.parse(raw);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatNotificationClock(ms) {
  const date = ms ? new Date(ms) : new Date();
  try {
    return date.toLocaleTimeString(getLocale(), {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch(_) {
    return date.toLocaleTimeString();
  }
}

function getNotificationEventId(data) {
  if (!data || typeof data !== 'object') return '';
  if (data.alert_id) return String(data.alert_id);
  if (data.type === 'finance') {
    const financeKey = data.payment_id || data.external_id || '';
    return financeKey ? `finance:${financeKey}` : '';
  }
  const scope = data.chat_id || '';
  const user = data.user_id || data.username || data.display_name || '';
  const occurredAt = data.occurred_at || data.time || '';
  return scope && user && data.type ? `member:${scope}:${user}:${data.type}:${occurredAt}` : '';
}

function isValidIncomingNotification(data) {
  if (!data || typeof data !== 'object') return false;
  if (!['join', 'leave', 'finance'].includes(data.type)) return false;
  if (data.type === 'finance') {
    return Boolean(data.payment_id || data.external_id || data.chat_title || data.provider_account);
  }
  return Boolean(getNotificationActor(data) && (data.chat_title || data.chat_id));
}

function shouldAcceptIncomingNotification(data) {
  if (!isValidIncomingNotification(data)) return { ok: false, reason: 'invalid' };
  const eventId = getNotificationEventId(data);
  if (eventId && seenNotificationEventIds.has(eventId)) {
    return { ok: false, reason: 'duplicate', eventId: eventId };
  }
  const occurredAtMs = parseNotificationOccurredAt(data.occurred_at);
  if (occurredAtMs && occurredAtMs < (NOTIFICATION_SESSION_STARTED_AT - 2000)) {
    if (eventId) seenNotificationEventIds.add(eventId);
    return { ok: false, reason: 'stale', eventId: eventId, occurredAtMs: occurredAtMs };
  }
  return { ok: true, eventId: eventId, occurredAtMs: occurredAtMs };
}

function loadStoredGoals() {
  try {
    const raw = localStorage.getItem(GOALS_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch(_) {
    return {};
  }
}

function saveStoredGoals() {
  localStorage.setItem(GOALS_KEY, JSON.stringify(goalSettings));
}

goalSettings = loadStoredGoals();

function showMsg(elId, text, isOk) {
  const m = el(elId);
  if (!m) return;
  m.textContent = text;
  m.className = 'msg ' + (isOk ? 'ok' : 'err');
}

async function api(path, opts) {
  const r = await fetch(path, opts || {});
  if (!r.ok) throw new Error(r.status + ': ' + r.statusText);
  return r.json();
}

async function apiBinary(path, opts) {
  const r = await fetch(path, opts || {});
  if (!r.ok) {
    let message = r.status + ': ' + r.statusText;
    try {
      const data = await r.json();
      if (data && (data.msg || data.error)) message = data.msg || data.error;
    } catch(_) {}
    throw new Error(message);
  }
  return r;
}

async function postJson(path, payload) {
  const r = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload || {}),
  });
  const data = await r.json().catch(function() { return {}; });
  if (!r.ok || data.ok === false) {
    throw new Error(data.msg || data.error || (r.status + ': ' + r.statusText));
  }
  return data;
}

async function postForm(path, formData) {
  const r = await fetch(path, {
    method: 'POST',
    body: formData,
  });
  const data = await r.json().catch(function() { return {}; });
  if (!r.ok || data.ok === false) {
    throw new Error(data.msg || data.error || (r.status + ': ' + r.statusText));
  }
  return data;
}

const COPT = {
  responsive: true, maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  animation: PERF_PROFILE.isConservative ? { duration: 0 } : {
    duration: 420,
    easing: 'easeOutCubic'
  },
  elements: {
    line: {
      cubicInterpolationMode: 'monotone'
    },
    point: {
      radius: 0,
      hoverRadius: 5,
      hoverBorderWidth: 2
    }
  },
  plugins: {
    legend: {
      labels: {
        color: '#aab8cf',
        font: { size: 11, family: 'Inter, Manrope, sans-serif', weight: '600' },
        boxWidth: 10,
        boxHeight: 10,
        usePointStyle: true,
        pointStyle: 'circle',
        padding: 18
      }
    },
    tooltip: {
      backgroundColor: 'rgba(8, 16, 28, 0.94)',
      borderColor: 'rgba(255, 179, 71, 0.22)',
      borderWidth: 1,
      titleColor: '#f8fafc',
      bodyColor: '#d8e3f3',
      titleFont: { family: 'Inter, Manrope, sans-serif', weight: '700' },
      bodyFont: { family: 'Inter, Manrope, sans-serif', weight: '600' },
      padding: 12,
      cornerRadius: 14,
      displayColors: true,
      boxPadding: 5
    }
  },
  scales: {
    x: {
      ticks: { color:'#92a4bf', maxTicksLimit:14, font: { family: 'Inter, Manrope, sans-serif', size: 11 } },
      grid: { color:'rgba(148, 163, 184, 0.05)', drawBorder: false }
    },
    y: {
      ticks: { color:'#92a4bf', font: { family: 'Inter, Manrope, sans-serif', size: 11 } },
      grid: { color:'rgba(148, 163, 184, 0.05)', drawBorder: false }
    }
  }
};

function mkChart(id, type, data, extra) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  const nextOptions = Object.assign({}, COPT, extra || {});
  if (charts[id] && charts[id].config && charts[id].config.type === type) {
    charts[id].data = data;
    charts[id].options = nextOptions;
    charts[id].update(PERF_PROFILE.isConservative ? 'none' : undefined);
    return;
  }
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }
  charts[id] = new Chart(ctx.getContext('2d'), {
    type: type, data: data, options: nextOptions
  });
}

async function loadGroups(force) {
  const now = Date.now();
  if (!force && groupList.length && refreshState.groupsLoadedAt && (now - refreshState.groupsLoadedAt) < GROUPS_CACHE_MS) {
    return groupList;
  }
  const groups = await api('/api/groups');
  const orderedGroups = (groups || []).slice().sort(function(a, b) {
    const aPrimary = normalizeGroupName(a && a.chat_title).includes('private - hot casais plus') ? 1 : 0;
    const bPrimary = normalizeGroupName(b && b.chat_title).includes('private - hot casais plus') ? 1 : 0;
    if (aPrimary !== bPrimary) return bPrimary - aPrimary;
    return 0;
  });
  groupList = orderedGroups;
  const sel    = el('group-select');
  const prev   = sel ? sel.value : (chatId || '');
  const signature = JSON.stringify(orderedGroups.map(function(g) {
    return [String(g.chat_id), String(g.chat_title || '')];
  }));
  if (sel && (force || signature !== refreshState.groupsSignature)) {
    const fragment = document.createDocumentFragment();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.text = getUiText().common.selectGroupOption;
    fragment.appendChild(placeholder);
    orderedGroups.forEach(function(g) {
      const o = document.createElement('option');
      o.value = String(g.chat_id);
      o.text = g.chat_title || String(g.chat_id);
      fragment.appendChild(o);
    });
    sel.innerHTML = '';
    sel.appendChild(fragment);
  }
  const hasPrevious = Boolean(sel && prev && Array.from(sel.options).some(function(o) { return o.value === prev; }));
  if (hasPrevious) {
    sel.value = prev;
    chatId = prev;
  } else if (orderedGroups.length) {
    if (sel) sel.value = String(orderedGroups[0].chat_id);
    chatId    = String(orderedGroups[0].chat_id);
  } else {
    if (sel) sel.value = '';
    chatId = null;
  }
  refreshState.groupsLoadedAt = now;
  if (force || signature !== refreshState.groupsSignature) {
    refreshState.groupsSignature = signature;
    renderSidebarGroups(groupList);
  }
  return groupList;
}

async function checkBotStatus(force) {
  const now = Date.now();
  if (!force && refreshState.botStatusLoadedAt && (now - refreshState.botStatusLoadedAt) < BOT_STATUS_CACHE_MS) {
    return;
  }
  try {
    const text = getUiText();
    const s = await api('/api/settings');
    const d = el('bot-status');
    const signature = [String(Boolean(s.bot_running)), String(Boolean(s.token_set)), currentLang].join('|');
    if (d && (force || signature !== refreshState.botStatusSignature)) {
      if (s.bot_running) {
        d.className = 'bot-st ok'; d.textContent = text.bot.active;
      } else if (s.token_set) {
        d.className = 'bot-st warn'; d.textContent = text.bot.stopped;
      } else {
        d.className = 'bot-st err'; d.textContent = text.bot.noToken;
      }
    }
    refreshState.botStatusLoadedAt = now;
    refreshState.botStatusSignature = signature;
  } catch(_) {}
}

async function loadOverview(forceSkeletion = false) {
  const text = getUiText();
  if (el('overview-export-group')) el('overview-export-group').textContent = getSelectedGroupLabel();
  if (forceSkeletion) showSkeleton();
  if (!chatId) {
    ['c-joins','c-leaves','c-net','c-churn'].forEach(function(id) { el(id).textContent = '-'; });
    el('insights').innerHTML = `<li>${text.common.selectGroup}.</li>`;
    el('feed').innerHTML = '';
    return;
  }
  const results = await Promise.all([
    api('/api/stats/'   + chatId),
    api('/api/reports/' + chatId),
    api('/api/recent/'  + chatId),
    api('/api/members/' + chatId)
  ]);
  const stats = results[0], report = results[1], recent = results[2], members = results[3];
  el('c-joins').textContent  = stats.total_joins  || 0;
  el('c-leaves').textContent = stats.total_leaves || 0;
  const net = stats.net_growth || 0;
  el('c-net').textContent = (net >= 0 ? '+' : '') + net;
  el('c-net').style.color = net >= 0 ? '#3fb950' : '#f85149';
  el('c-churn').textContent = (stats.churn_rate || 0) + '%';
  const ul = el('insights');
  ul.innerHTML = '';
  (report.insights || []).forEach(function(t) {
    const li = document.createElement('li'); li.textContent = t; ul.appendChild(li);
  });
  const feed = el('feed');
  feed.innerHTML = '';
  el('meta-first').textContent = stats.first_event ? fmt(stats.first_event.replace(' ', 'T')) : '-';
  el('meta-last').textContent = stats.last_event ? fmt(stats.last_event.replace(' ', 'T')) : '-';
  el('meta-members').textContent = members && members.count ? (members.count.total || 0) : 0;
  el('meta-admins').textContent = members && members.count ? (members.count.admins || 0) : 0;
  hideSkeleton();
  (recent || []).forEach(function(ev) {
    const li = document.createElement('li');
    li.innerHTML =
      '<span class="badge ' + ev.event_type + '">' + (ev.event_type === 'join' ? text.notifications.joined.toUpperCase() : text.notifications.left.toUpperCase()) + '</span>' +
      '<span class="feed-user">@' + ev.username + '</span>' +
      '<span class="feed-time">' + fmtT(ev.created_at) + '</span>';
    feed.appendChild(li);
  });
}

async function loadCharts() {
  if (!chatId) return;
  const text = getUiText();
  const ts = await api('/api/timeseries/' + chatId);
  if (!ts.labels || !ts.labels.length) return;
  const joins = ts.joins || [], leaves = ts.leaves || [];
  mkChart('chart-line', 'line', {
    labels: ts.labels,
    datasets: [
      {
        label:text.charts.joins,
        data:joins,
        borderColor:'#34d399',
        backgroundColor:'rgba(52, 211, 153, 0.14)',
        pointRadius:0,
        pointHoverRadius:5,
        pointHoverBackgroundColor:'#34d399',
        pointHoverBorderColor:'#06111c',
        borderWidth:2.4,
        tension:.38,
        fill:true
      },
      {
        label:text.charts.leaves,
        data:leaves,
        borderColor:'#fb7185',
        backgroundColor:'rgba(251, 113, 133, 0.12)',
        pointRadius:0,
        pointHoverRadius:5,
        pointHoverBackgroundColor:'#fb7185',
        pointHoverBorderColor:'#06111c',
        borderWidth:2.4,
        tension:.38,
        fill:true
      },
      {
        label:text.charts.joinsMa,
        data:ts.joins_ma7,
        borderColor:'#7dd3fc',
        borderDash:[7,6],
        pointRadius:0,
        borderWidth:1.8,
        tension:.34,
        fill:false
      },
      {
        label:text.charts.leavesMa,
        data:ts.leaves_ma7,
        borderColor:'#fdba74',
        borderDash:[7,6],
        pointRadius:0,
        borderWidth:1.8,
        tension:.34,
        fill:false
      }
    ]
  }, {
    plugins: { filler: { propagate: false } }
  });
  const netArr = joins.map(function(j,i){ return j-(leaves[i]||0); });
  mkChart('chart-bar', 'bar', {
    labels: ts.labels,
    datasets: [{
      label:text.charts.net,
      data:netArr,
      borderRadius:8,
      maxBarThickness:24,
      backgroundColor: netArr.map(function(v){ return v>=0?'rgba(52, 211, 153, 0.78)':'rgba(251, 113, 133, 0.78)'; }),
      borderColor: netArr.map(function(v){ return v>=0?'rgba(167, 243, 208, 0.92)':'rgba(254, 205, 211, 0.92)'; }),
      borderWidth:1
    }]
  });
  mkChart('chart-area', 'line', {
    labels: ts.labels,
    datasets: [{
      label:text.charts.members,
      data:ts.net_members||[],
      borderColor:'#60a5fa',
      backgroundColor:'rgba(96, 165, 250, 0.18)',
      pointRadius:0,
      pointHoverRadius:5,
      pointHoverBackgroundColor:'#60a5fa',
      pointHoverBorderColor:'#06111c',
      borderWidth:2.4,
      tension:.36,
      fill:true
    }]
  }, {
    scales: {
      x: {
        ticks: { color:'#92a4bf', maxTicksLimit:14, font: { family: 'Inter, Manrope, sans-serif', size: 11 } },
        grid: { color:'rgba(148, 163, 184, 0.05)', drawBorder: false }
      },
      y: {
        ticks: { color:'#92a4bf', font: { family: 'Inter, Manrope, sans-serif', size: 11 } },
        grid: { color:'rgba(96, 165, 250, 0.08)', drawBorder: false }
      }
    }
  });
}

function getSelectedGroupLabel() {
  const sel = el('group-select');
  if (!sel || !sel.value) return getUiText().common.selectGroup;
  const option = sel.options[sel.selectedIndex];
  return option ? option.text : String(sel.value);
}

function normalizeGroupName(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function getPrimaryRevenueGroup() {
  return (groupList || []).find(function(group) {
    return normalizeGroupName(group && group.chat_title).includes('private - hot casais plus');
  }) || null;
}

function getPrimaryRevenueGroupId() {
  const group = getPrimaryRevenueGroup();
  return group && group.chat_id ? String(group.chat_id) : '';
}

function getPrimaryRevenueGroupLabel() {
  const group = getPrimaryRevenueGroup();
  return group && group.chat_title ? String(group.chat_title) : 'PRIVATE - Hot Casais Plus';
}

function formatBRL(value) {
  return new Intl.NumberFormat(getLocale(), {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value) || 0);
}

function getGroupInitials(name) {
  const source = (name || '').replace(/[^A-Za-z0-9\s]/g, ' ').trim();
  const parts = source.split(/\s+/).filter(Boolean);
  if (!parts.length) return 'TG';
  return parts.slice(0, 2).map(part => part.charAt(0).toUpperCase()).join('');
}

function renderSidebarGroups(groups) {
  const list = el('sidebar-groups');
  const badge = el('sidebar-groups-total');
  if (badge) badge.textContent = String((groups || []).length);
  if (!list) return;

  list.innerHTML = '';
  if (!groups || !groups.length) {
    const empty = document.createElement('div');
    empty.className = 'sidebar-empty';
    empty.textContent = getUiText().common.noGroups;
    list.appendChild(empty);
    return;
  }

  groups.forEach(group => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sidebar-group-btn' + (String(group.chat_id) === String(chatId) ? ' active' : '');
    btn.dataset.tooltip = group.chat_title || String(group.chat_id);

    const avatar = document.createElement('span');
    avatar.className = 'sidebar-group-avatar';
    avatar.textContent = getGroupInitials(group.chat_title || String(group.chat_id));

    const copy = document.createElement('span');
    copy.className = 'sidebar-group-copy';

    const title = document.createElement('strong');
    title.textContent = group.chat_title || String(group.chat_id);

    const meta = document.createElement('small');
    meta.textContent = String(group.chat_id);

    copy.appendChild(title);
    copy.appendChild(meta);
    btn.appendChild(avatar);
    btn.appendChild(copy);
    btn.addEventListener('click', async () => {
      await selectGroup(group.chat_id);
    });
    list.appendChild(btn);
  });
}

async function selectGroup(nextChatId) {
  const value = nextChatId ? String(nextChatId) : '';
  const sel = el('group-select');
  if (sel) sel.value = value;
  chatId = value || null;
  prevJoins = 0;
  activePage = 1;
  renderSidebarGroups(groupList);
  syncExportButtons();
  await loadActiveView(true);
}

function syncExportButtons() {
  const enabled = Boolean(chatId);
  document.querySelectorAll('[data-export-action]').forEach(btn => {
    btn.disabled = !enabled;
    btn.classList.toggle('is-disabled', !enabled);
  });
}

async function loadHome() {
  const text = getUiText();
  const groupName = getSelectedGroupLabel();
  const groupsCount = Array.isArray(groupList) ? groupList.length : 0;
  const primaryRevenueGroupId = getPrimaryRevenueGroupId();
  const primaryRevenueGroupLabel = getPrimaryRevenueGroupLabel();
  const financeHomeScopeId = primaryRevenueGroupId || (chatId ? String(chatId) : '');
  if (el('home-active-group')) el('home-active-group').textContent = groupName;
  if (el('home-groups-count')) el('home-groups-count').textContent = String(groupsCount);
  if (el('home-transactions-header')) el('home-transactions-header').textContent = text.home.transactionsHeaderFor(primaryRevenueGroupLabel);
  if (el('home-finance-total-label')) el('home-finance-total-label').textContent = text.home.financeTotalLabelFor(primaryRevenueGroupLabel);
  if (el('home-finance-24h-label')) el('home-finance-24h-label').textContent = text.home.finance24hLabelFor(primaryRevenueGroupLabel);
  if (el('home-finance-approved-24h-label')) el('home-finance-approved-24h-label').textContent = text.home.financeApproved24hLabelFor(primaryRevenueGroupLabel);
  if (el('home-finance-week-label')) el('home-finance-week-label').textContent = text.home.financeWeekLabelFor(primaryRevenueGroupLabel);
  if (el('home-finance-source')) el('home-finance-source').textContent = text.home.financeSourceLabel(primaryRevenueGroupLabel);
  if (el('home-transactions-source')) el('home-transactions-source').textContent = text.home.financeSourceLabel(primaryRevenueGroupLabel);

  if (!chatId) {
    if (el('home-events-count')) el('home-events-count').textContent = '-';
    if (el('home-members-count')) el('home-members-count').textContent = '-';
  }

  try {
    const requests = [
      api(financeHomeScopeId ? ('/api/finance/payments/' + encodeURIComponent(financeHomeScopeId)) : '/api/finance/payments'),
      api(financeHomeScopeId ? ('/api/finance/home-metrics?chat_id=' + encodeURIComponent(financeHomeScopeId)) : '/api/finance/home-metrics'),
    ];
    if (chatId) {
      requests.unshift(api('/api/stats/' + chatId), api('/api/members/' + chatId));
    }
    const responses = await Promise.all(requests);
    let payments;
    let financeMetrics;
    if (chatId) {
      const stats = responses[0];
      const members = responses[1];
      payments = responses[2];
      financeMetrics = responses[3];
      const totalEvents = (stats.total_joins || 0) + (stats.total_leaves || 0);
      if (el('home-events-count')) el('home-events-count').textContent = String(totalEvents);
      if (el('home-members-count')) el('home-members-count').textContent = String((members.count && members.count.total) || 0);
    } else {
      payments = responses[0];
      financeMetrics = responses[1];
    }
    if (el('home-finance-total')) el('home-finance-total').textContent = formatBRL(financeMetrics && financeMetrics.total_revenue || 0);
    if (el('home-finance-24h')) el('home-finance-24h').textContent = String(financeMetrics && financeMetrics.transactions_last_24h || 0);
    if (el('home-finance-approved-24h')) el('home-finance-approved-24h').textContent = String(financeMetrics && financeMetrics.approved_last_24h || 0);
    if (el('home-finance-week')) el('home-finance-week').textContent = String(financeMetrics && financeMetrics.approved_this_week || 0);
    renderHomeTransactions(Array.isArray(payments) ? payments.slice(0, 3) : [], primaryRevenueGroupLabel);
  } catch(_) {
    // Preserve the last successful values during transient refresh failures.
  }
}

function renderHomeTransactions(rows, groupName) {
  const text = getUiText();
  const list = el('home-transactions-list');
  if (!list) return;
  list.innerHTML = '';
  if (!Array.isArray(rows) || !rows.length) {
    list.innerHTML = `<div class="home-transaction-empty" id="home-transactions-empty">${text.home.transactionsEmpty}</div>`;
    return;
  }
  rows.forEach(function(row) {
    const meta = getFinanceStatusMeta(row.status);
    const sourceLabel = row.provider_account || (chatId ? groupName : text.home.transactionsSourceGlobal);
    const timeLabel = getFinanceDisplayTimestamp(row) || '-';
    const renderedTime = renderFinanceTimestamp(timeLabel);
    const item = document.createElement('div');
    item.className = 'home-transaction-row';
    item.innerHTML = `
      <div class="home-transaction-main">
        <span class="home-transaction-title">${escHtml(row.external_id || row.payment_id || '-')}</span>
        <span class="home-transaction-subtitle">${escHtml(sourceLabel)}${row.description ? ` - ${escHtml(row.description)}` : ''}</span>
      </div>
      <div class="home-transaction-side">
        <strong class="home-transaction-amount">${formatBRL(row.amount)}</strong>
        <span class="home-transaction-time">${renderedTime}</span>
        <span class="finance-status-badge finance-status-badge--${meta.tone} home-transaction-status">${meta.label}</span>
      </div>
    `;
    list.appendChild(item);
  });
}

function ensureAudioContext() {
  const AudioCtor = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtor) return null;
  if (!audioCtx) audioCtx = new AudioCtor();
  if (audioCtx.state === 'suspended') {
    audioCtx.resume().catch(function(){});
  }
  return audioCtx;
}

function playNotificationSound(type) {
  const ctx = ensureAudioContext();
  if (!ctx) return;
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();
  oscillator.type = type === 'finance' ? 'triangle' : 'sine';
  const startFrequency = type === 'join' ? 880 : (type === 'finance' ? 740 : 620);
  const endFrequency = type === 'join' ? 1120 : (type === 'finance' ? 980 : 480);
  const peakGain = type === 'finance' ? 0.095 : 0.08;
  oscillator.frequency.setValueAtTime(startFrequency, ctx.currentTime);
  oscillator.frequency.exponentialRampToValueAtTime(endFrequency, ctx.currentTime + 0.16);
  gain.gain.setValueAtTime(0.0001, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(peakGain, ctx.currentTime + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.22);
  oscillator.connect(gain);
  gain.connect(ctx.destination);
  oscillator.start(ctx.currentTime);
  oscillator.stop(ctx.currentTime + 0.24);
}

function getNotificationActor(item) {
  const fullName = String(item && (item.full_name || item.display_name || item.actor_name) || '').trim();
  const username = String(item && item.username || '').trim().replace(/^@+/, '');
  if (fullName && username && fullName.toLowerCase() !== username.toLowerCase()) {
    return `${fullName} (@${username})`;
  }
  if (fullName) return fullName;
  if (username) return `@${username}`;
  if (item && item.user_id) return `ID ${item.user_id}`;
  return '';
}

function getNotificationDisplayParts(item) {
  const text = getUiText();
  const type = item && item.type ? item.type : 'join';
  if (type === 'finance') {
    const title = item.title || text.notifications.paymentCreatedTitle;
    const scope = item.chat_title || item.chat_id || text.notifications.payment;
    const value = item.amount ? formatBRL(item.amount) : '';
    const message = item.message || [scope, value].filter(Boolean).join(' â€¢ ') || text.notifications.paymentCreatedMessage;
    return {
      badge: text.notifications.payment,
      title: title,
      message: message,
      scope: item.provider_account || '',
      icon: 'ðŸ’°',
      tone: 'finance'
    };
  }
  const actor = getNotificationActor(item);
  return {
    badge: type === 'join' ? text.notifications.joined : text.notifications.left,
    title: actor || (type === 'join' ? text.notifications.joined : text.notifications.left),
    message: type === 'join' ? `${text.notifications.joined} em ${item.chat_title || item.chat_id || '-'}` : `${text.notifications.left} de ${item.chat_title || item.chat_id || '-'}`,
    scope: item.chat_title || item.chat_id || '',
    icon: 'ðŸ‘¤',
    tone: type
  };
}

function showLiveNotificationCard(item) {
  const stack = el('live-notification-stack');
  if (!stack) return;
  const parts = getNotificationDisplayParts(item);
  const card = document.createElement('div');
  card.className = `live-notification-card live-notification-card--${parts.tone}`;
  card.innerHTML = `
    <div class="live-notification-icon">${escHtml(parts.icon)}</div>
    <div class="live-notification-copy">
      <div class="live-notification-topline">
        <span class="live-notification-badge">${escHtml(parts.badge)}</span>
        <span class="live-notification-time">${escHtml(item.time || '')}</span>
      </div>
      <strong>${escHtml(parts.title)}</strong>
      <p>${escHtml(parts.message)}</p>
      ${parts.scope ? `<span class="live-notification-scope">${escHtml(parts.scope)}</span>` : ''}
    </div>
    <button type="button" class="live-notification-close" aria-label="${escHtml(getUiText().notifications.removeAria)}">Ã—</button>
  `;
  const close = function() {
    card.classList.add('is-leaving');
    window.setTimeout(function() {
      card.remove();
    }, 220);
  };
  const closeBtn = card.querySelector('.live-notification-close');
  if (closeBtn) closeBtn.addEventListener('click', close);
  stack.prepend(card);
  while (stack.children.length > 4) {
    stack.lastElementChild.remove();
  }
  window.setTimeout(close, 6500);
}

function renderSidebarNotifications() {
  const text = getUiText();
  const list = el('notifications-panel-list');
  const badge = el('notifications-panel-total');
  const topBadge = el('topbar-notifications-total');
  if (badge) badge.textContent = notificationItems.length === 1 ? '1 alerta' : `${notificationItems.length} alertas`;
  if (topBadge) {
    topBadge.textContent = String(notificationItems.length);
    topBadge.classList.toggle('is-hidden', notificationItems.length === 0);
  }
  if (!list) return;

  list.innerHTML = '';
  if (!notificationItems.length) {
    const empty = document.createElement('div');
    empty.className = 'sidebar-empty';
    empty.textContent = text.notifications.empty;
    list.appendChild(empty);
    return;
  }

  notificationItems.forEach(item => {
    const parts = getNotificationDisplayParts(item);
    const row = document.createElement('div');
    row.className = 'notification-item notification-item--' + item.type;
    row.innerHTML = `
      <div class="notification-item-main">
        <span class="notification-item-badge">${parts.badge}</span>
        <strong>${escHtml(parts.title)}</strong>
        <p>${escHtml(parts.message)}</p>
        <small>${item.time || ''}</small>
      </div>
      <button type="button" class="notification-item-remove" onclick="removeNotification('${item.id}')" aria-label="${text.notifications.removeAria}">x</button>
    `;
    list.appendChild(row);
  });
}

function pushNotificationItem(data) {
  const decision = shouldAcceptIncomingNotification(data);
  if (!decision.ok) return null;
  const item = {
    id: decision.eventId || (String(Date.now()) + '-' + Math.random().toString(16).slice(2, 8)),
    event_id: decision.eventId || '',
    type: data.type || 'join',
    username: data.username || '',
    full_name: data.full_name || '',
    display_name: data.display_name || '',
    user_id: data.user_id || '',
    title: data.title || '',
    message: data.message || '',
    chat_title: data.chat_title || '',
    chat_id: data.chat_id || '',
    provider_account: data.provider_account || '',
    payment_id: data.payment_id || '',
    external_id: data.external_id || '',
    amount: data.amount || 0,
    occurred_at: data.occurred_at || '',
    time: data.time || formatNotificationClock(decision.occurredAtMs)
  };
  if (item.event_id) seenNotificationEventIds.add(item.event_id);
  notificationItems.unshift(item);
  notificationItems = notificationItems.slice(0, MAX_NOTIFICATIONS);
  saveNotifications();
  renderSidebarNotifications();
  showLiveNotificationCard(item);
  return item;
}

window.removeNotification = function(id) {
  notificationItems = notificationItems.filter(function(item) { return item.id !== id; });
  saveNotifications();
  renderSidebarNotifications();
};

window.clearNotifications = function() {
  notificationItems = [];
  saveNotifications();
  renderSidebarNotifications();
  showToast(getUiText().notifications.clearToast, 'info');
};

function setNotificationsDrawer(open) {
  const panel = el('topbar-notifications-panel');
  const backdrop = el('topbar-notifications-backdrop');
  const toggle = el('notifications-toggle');
  const isOpen = Boolean(open);
  if (panel) {
    panel.classList.toggle('is-open', isOpen);
    panel.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
  }
  if (backdrop) {
    backdrop.hidden = !isOpen;
    backdrop.classList.toggle('is-open', isOpen);
    backdrop.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
  }
  if (toggle) {
    toggle.classList.toggle('is-open', isOpen);
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }
}

window.toggleNotificationsDrawer = function(event) {
  if (event && typeof event.preventDefault === 'function') event.preventDefault();
  if (event && typeof event.stopPropagation === 'function') event.stopPropagation();
  const panel = el('topbar-notifications-panel');
  const isOpen = panel ? panel.classList.contains('is-open') : false;
  setNotificationsDrawer(!isOpen);
};

window.closeNotificationsDrawer = function() {
  setNotificationsDrawer(false);
};

function updateViewRailVisibility(view) {
  const rail = el('view-rail');
  if (!rail) return;
  rail.classList.toggle('is-hidden', view === 'home');
  document.body.classList.toggle('home-active', view === 'home');
}

function scrollActiveChipIntoView(view) {
  const railTrack = el('view-rail-track');
  const chip = document.querySelector(`.view-chip[data-view="${view}"]`);
  if (!railTrack || !chip) return;
  chip.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
}

function syncViewChipTitles() {
  document.querySelectorAll('.view-chip').forEach(function(node) {
    const label = node.querySelector('.view-chip-label');
    const text = label ? label.textContent.trim() : '';
    if (!text) return;
    node.setAttribute('title', text);
    node.setAttribute('aria-label', text);
  });
}

function animateViewChipPress(node) {
  if (!node || !node.classList.contains('view-chip')) return;
  node.classList.remove('is-activating');
  void node.offsetWidth;
  node.classList.add('is-activating');
  setTimeout(function() {
    node.classList.remove('is-activating');
  }, 460);
}

function initViewRailDrag() {
  const railTrack = el('view-rail-track');
  if (!railTrack || railTrack.dataset.dragReady === '1') return;
  railTrack.dataset.dragReady = '1';
  let pressed = false;
  let moved = false;
  let startX = 0;
  let startScroll = 0;
  let suppressClickUntil = 0;

  railTrack.addEventListener('pointerdown', function(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    pressed = true;
    moved = false;
    startX = e.clientX;
    startScroll = railTrack.scrollLeft;
  });

  railTrack.addEventListener('pointermove', function(e) {
    if (!pressed) return;
    const delta = e.clientX - startX;
    if (!moved && Math.abs(delta) > 7) {
      moved = true;
      railTrack.classList.add('is-dragging');
    }
    if (!moved) return;
    railTrack.scrollLeft = startScroll - delta;
  });

  function stopDrag() {
    if (!pressed) return;
    if (moved) suppressClickUntil = Date.now() + 220;
    pressed = false;
    moved = false;
    railTrack.classList.remove('is-dragging');
  }

  railTrack.addEventListener('pointerup', stopDrag);
  railTrack.addEventListener('pointercancel', stopDrag);
  railTrack.addEventListener('lostpointercapture', stopDrag);
  railTrack.addEventListener('wheel', function(e) {
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      railTrack.scrollLeft += e.deltaY;
      e.preventDefault();
    }
  }, { passive: false });
  railTrack.addEventListener('click', function(e) {
    if (Date.now() < suppressClickUntil) {
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);
}

async function loadEvents(page) {
  const text = getUiText();
  if (!chatId) {
    el('ev-body').innerHTML = `<tr><td colspan="4" style="padding:20px;text-align:center">${text.events.selectGroup}</td></tr>`;
    el('pagination').innerHTML = '';
    return;
  }
  page = page || activePage;
  const data = await api('/api/events/' + chatId + '?page=' + page);
  activePage = data.page;
  allEvents = data.events || [];
  filterEvents();
  const pg = el('pagination');
  pg.innerHTML = '';
  for (let p = 1; p <= Math.min(data.total_pages||1, 10); p++) {
    const btn = document.createElement('button');
    btn.textContent = p;
    if (p === page) btn.classList.add('current');
    btn.onclick = (function(pp){ return function(){ loadEvents(pp); }; })(p);
    pg.appendChild(btn);
  }
}

function renderEventsTable(events, page) {
  const text = getUiText();
  const tbody = el('ev-body');
  tbody.innerHTML = '';
  if (!events || !events.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="padding:20px;text-align:center">${text.events.empty}</td></tr>`;
    return;
  }
  events.forEach(function(ev, i) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + ((page-1)*50+i+1) + '</td>' +
      '<td>@' + ev.username + '</td>' +
      '<td style="color:' + (ev.event_type==='join'?'#3fb950':'#f85149') + '">' + (ev.event_type==='join' ? text.notifications.joined.toUpperCase() : text.notifications.left.toUpperCase()) + '</td>' +
      '<td>' + fmt(ev.created_at) + '</td>';
    tbody.appendChild(tr);
  });
}

window.filterEvents = function() {
  const query = ((el('event-search') && el('event-search').value) || '').toLowerCase().trim();
  const type = (el('event-type-filter') && el('event-type-filter').value) || 'all';
  const filtered = allEvents.filter(function(ev) {
    const matchesQuery = !query || (ev.username || '').toLowerCase().includes(query);
    const matchesType = type === 'all' || ev.event_type === type;
    return matchesQuery && matchesType;
  });
  renderEventsTable(filtered, activePage);
  toggleEventSearchClear();
};

window.toggleEventSearchClear = function() {
  const input = el('event-search');
  const clear = el('event-search-clear');
  if (!input || !clear) return;
  clear.classList.toggle('visible', Boolean(input.value.trim()));
};

window.clearEventSearch = function() {
  const input = el('event-search');
  if (!input) return;
  input.value = '';
  filterEvents();
  toggleEventSearchClear();
  input.focus();
};

async function loadReports() {
  const text = getUiText();
  if (!chatId) {
    ['weekly-body','monthly-body'].forEach(function(id){
      el(id).innerHTML = `<tr><td colspan="4" style="padding:16px;text-align:center">${text.reports.noGroup}</td></tr>`;
    });
    el('anomalies').innerHTML = '';
    return;
  }
  const r = await api('/api/reports/' + chatId);
  function fillTable(tbodyId, rows, keys) {
    const tbody = el(tbodyId);
    tbody.innerHTML = '';
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="padding:14px;text-align:center">Sem dados.</td></tr>';
      return;
    }
    rows.forEach(function(row) {
      const tr = document.createElement('tr');
      tr.innerHTML = keys.map(function(k) {
        if (k === 'net') {
          const v = row[k]||0;
          return '<td style="color:'+(v>=0?'#3fb950':'#f85149')+';font-weight:600">'+(v>=0?'+':'')+v+'</td>';
        }
        return '<td>'+(row[k]!==undefined?row[k]:'-')+'</td>';
      }).join('');
      tbody.appendChild(tr);
    });
  }
  fillTable('weekly-body',  r.weekly,  ['week',  'joins','leaves','net']);
  fillTable('monthly-body', r.monthly, ['month', 'joins','leaves','net']);
  const box = el('anomalies');
  box.innerHTML = '';
  (r.spikes||[]).forEach(function(s){
    const d = document.createElement('div');
    d.className = 'anom spike';
    d.innerHTML = '<strong>' + text.reports.peak + '</strong><br>' + s.day + '<br>' + s.joins + ' ' + text.reports.joins + ' (' + s.vs_avg + 'x ' + text.reports.average + ')';
    box.appendChild(d);
  });
  (r.drops||[]).forEach(function(s){
    const d = document.createElement('div');
    d.className = 'anom drop';
    d.innerHTML = '<strong>' + text.reports.drop + '</strong><br>' + s.day + '<br>' + s.leaves + ' ' + text.reports.leaves + ' vs ' + s.joins + ' ' + text.reports.joins;
    box.appendChild(d);
  });
  if (!box.children.length) box.innerHTML = `<p style="color:#8b949e">${text.reports.none}</p>`;
}

function getGoalStorageKey() {
  return chatId ? String(chatId) : '__no_group__';
}

function toNumber(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function roundTo(value, decimals) {
  const factor = 10 ** (decimals || 0);
  return Math.round((Number(value) || 0) * factor) / factor;
}

function lastEntry(rows) {
  return Array.isArray(rows) && rows.length ? rows[rows.length - 1] : null;
}

function buildGoalsMetrics(stats, report, members) {
  const weekly = lastEntry(report && report.weekly) || {};
  const monthly = lastEntry(report && report.monthly) || {};
  return {
    groupName: getSelectedGroupLabel(),
    weeklyLabel: weekly.week || 'Sem dados',
    monthlyLabel: monthly.month || 'Sem dados',
    weeklyJoins: toNumber(weekly.joins, 0),
    weeklyNet: toNumber(weekly.net, 0),
    monthlyNet: toNumber(monthly.net, 0),
    membersTotal: toNumber(members && members.count && members.count.total, 0),
    membersAdmins: toNumber(members && members.count && members.count.admins, 0),
    churnRate: toNumber(stats && stats.churn_rate, 0),
    totalJoins: toNumber(stats && stats.total_joins, 0),
    totalLeaves: toNumber(stats && stats.total_leaves, 0),
    netGrowth: toNumber(stats && stats.net_growth, 0),
  };
}

function buildSuggestedGoals(metrics) {
  return {
    weekly_joins: Math.max(8, Math.ceil(Math.max(metrics.weeklyJoins, 0) * 1.25) || 8),
    monthly_net: Math.max(10, Math.ceil(Math.max(metrics.monthlyNet, 0) * 1.25) || 10),
    member_base: Math.max(50, Math.ceil(Math.max(metrics.membersTotal, 0) * 1.12) || 50),
    max_churn: Math.max(6, roundTo((metrics.churnRate || 0) + 2, 1) || 12),
  };
}

function getStoredGoals(metrics) {
  const defaults = buildSuggestedGoals(metrics || {});
  const stored = goalSettings[getGoalStorageKey()] || {};
  return {
    weekly_joins: Math.max(1, Math.round(toNumber(stored.weekly_joins, defaults.weekly_joins))),
    monthly_net: Math.max(1, Math.round(toNumber(stored.monthly_net, defaults.monthly_net))),
    member_base: Math.max(1, Math.round(toNumber(stored.member_base, defaults.member_base))),
    max_churn: Math.max(0.1, roundTo(toNumber(stored.max_churn, defaults.max_churn), 1)),
  };
}

function setGoalsFormDisabled(disabled) {
  document.querySelectorAll('#view-goals input').forEach(function(input) {
    input.disabled = disabled;
  });
  ['goals-save-btn', 'goals-reset-btn'].forEach(function(id) {
    const button = el(id);
    if (button) button.disabled = disabled;
  });
}

function writeGoalsForm(goals) {
  if (el('goal-weekly-joins')) el('goal-weekly-joins').value = goals.weekly_joins;
  if (el('goal-monthly-net')) el('goal-monthly-net').value = goals.monthly_net;
  if (el('goal-member-base')) el('goal-member-base').value = goals.member_base;
  if (el('goal-max-churn')) el('goal-max-churn').value = goals.max_churn;
}

function readGoalsForm() {
  if (!currentGoalsMetrics) return null;
  const defaults = buildSuggestedGoals(currentGoalsMetrics);
  return {
    weekly_joins: Math.max(1, Math.round(toNumber(el('goal-weekly-joins') && el('goal-weekly-joins').value, defaults.weekly_joins))),
    monthly_net: Math.max(1, Math.round(toNumber(el('goal-monthly-net') && el('goal-monthly-net').value, defaults.monthly_net))),
    member_base: Math.max(1, Math.round(toNumber(el('goal-member-base') && el('goal-member-base').value, defaults.member_base))),
    max_churn: Math.max(0.1, roundTo(toNumber(el('goal-max-churn') && el('goal-max-churn').value, defaults.max_churn), 1)),
  };
}

function formatGoalValue(value, mode) {
  if (!Number.isFinite(value)) return '-';
  if (mode === 'signed') {
    const rounded = Math.round(value);
    return (rounded >= 0 ? '+' : '') + rounded;
  }
  if (mode === 'percent') {
    return `${roundTo(value, 1).toFixed(1).replace(/\.0$/, '')}%`;
  }
  return `${Math.round(value)}`;
}

function formatGoalGap(value, mode) {
  const abs = Math.abs(value);
  return mode === 'percent' ? formatGoalValue(abs, 'percent') : formatGoalValue(abs, 'number');
}

function buildGoalState(current, target, mode, format) {
  const text = getUiText();
  if (mode === 'max') {
    const reached = current <= target;
    const progress = target > 0 ? (reached ? 100 : Math.max(0, 100 - (((current - target) / target) * 100))) : 0;
    return {
      progress: Math.max(0, Math.min(100, progress)),
      tone: reached ? 'success' : current <= target * 1.15 ? 'warning' : 'danger',
      status: reached ? text.goals.states.underLimit : text.goals.states.aboveLimit,
      detail: reached ? text.goals.details.marginOf(formatGoalGap(target - current, format)) : text.goals.details.aboveBy(formatGoalGap(current - target, format)),
    };
  }

  const progress = target > 0 ? Math.min(100, (current / target) * 100) : 0;
  const reached = current >= target;
  return {
    progress: Math.max(0, Math.min(100, progress)),
    tone: reached ? 'success' : progress >= 70 ? 'warning' : 'danger',
    status: reached ? text.goals.states.goalHit : progress >= 70 ? text.goals.states.onTrack : text.goals.states.attention,
    detail: reached ? text.goals.details.exceededBy(formatGoalGap(current - target, format)) : text.goals.details.missing(formatGoalGap(target - current, format)),
  };
}

function renderGoalsInsights(cards) {
  const text = getUiText();
  const list = el('goals-insights');
  if (!list) return;
  list.innerHTML = cards.map(function(card) {
    return `
      <li class="goals-insight goals-insight--${card.state.tone}">
        <div class="goals-insight-copy">
          <strong>${card.title}</strong>
          <p>${card.state.detail}. ${text.goals.details.currentOfTarget(formatGoalValue(card.current, card.format), formatGoalValue(card.target, card.targetFormat || card.format))}</p>
        </div>
        <span class="goals-insight-tag">${card.state.status}</span>
      </li>
    `;
  }).join('');
}

function renderGoalsMetrics(metrics, goals) {
  const text = getUiText();
  const cards = [
    {
      title: text.goals.titles.weeklyJoins,
      label: metrics.weeklyLabel,
      current: metrics.weeklyJoins,
      target: goals.weekly_joins,
      mode: 'min',
      format: 'number',
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 12h5l3-8 4 16 3-8h3"/></svg>',
    },
    {
      title: text.goals.titles.monthlyNet,
      label: metrics.monthlyLabel,
      current: metrics.monthlyNet,
      target: goals.monthly_net,
      mode: 'min',
      format: 'signed',
      targetFormat: 'number',
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 17 9 11 13 15 21 7"/><path d="M14 7h7v7"/></svg>',
    },
    {
      title: text.goals.titles.memberBase,
      label: text.goals.labels.currentTotal,
      current: metrics.membersTotal,
      target: goals.member_base,
      mode: 'min',
      format: 'number',
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="9" cy="7" r="4"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/><path d="M21 21v-2a4 4 0 0 0-3-3.85"/></svg>',
    },
    {
      title: text.goals.titles.maxChurn,
      label: text.goals.labels.baseHealth,
      current: metrics.churnRate,
      target: goals.max_churn,
      mode: 'max',
      format: 'percent',
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
    }
  ].map(function(card) {
    return Object.assign(card, { state: buildGoalState(card.current, card.target, card.mode, card.format) });
  });

  const grid = el('goals-metrics-grid');
  if (grid) {
    grid.innerHTML = cards.map(function(card) {
      return `
        <article class="goal-card goal-card--${card.state.tone}">
          <div class="goal-card-head">
            <span class="goal-card-icon">${card.icon}</span>
            <span class="goal-card-status">${card.state.status}</span>
          </div>
          <span class="goal-card-label">${card.title}</span>
          <strong class="goal-card-value">${formatGoalValue(card.current, card.format)}</strong>
          <div class="goal-card-meta">
            <span>${card.label}</span>
            <span>${text.goals.labels.goalPrefix} ${formatGoalValue(card.target, card.targetFormat || card.format)}</span>
          </div>
          <div class="goal-progress">
            <div class="goal-progress-bar" style="width:${card.state.progress}%"></div>
          </div>
          <div class="goal-card-foot">${card.state.detail}</div>
        </article>
      `;
    }).join('');
  }

  const avg = cards.length ? Math.round(cards.reduce(function(sum, card) {
    return sum + card.state.progress;
  }, 0) / cards.length) : 0;

  if (el('goals-score')) el('goals-score').textContent = `${avg}%`;
  if (el('goals-score-copy')) {
    el('goals-score-copy').textContent =
      avg >= 100 ? text.goals.summaries.perfect :
      avg >= 75 ? text.goals.summaries.good :
      text.goals.summaries.low;
  }
  if (el('goals-group-title')) el('goals-group-title').textContent = text.goals.groupTitle(metrics.groupName);
  if (el('goals-group-caption')) {
    el('goals-group-caption').textContent = text.goals.groupCaption(metrics.groupName);
  }
  if (el('goals-week-label')) el('goals-week-label').textContent = metrics.weeklyLabel;
  if (el('goals-month-label')) el('goals-month-label').textContent = metrics.monthlyLabel;
  if (el('goals-members-live')) el('goals-members-live').textContent = `${metrics.membersTotal}`;

  renderGoalsInsights(cards);
}

function resetGoalsVisualState() {
  const text = getUiText();
  if (el('goals-group-title')) el('goals-group-title').textContent = text.goals.defaultTitle;
  if (el('goals-group-caption')) el('goals-group-caption').textContent = text.goals.defaultCaption;
  if (el('goals-week-label')) el('goals-week-label').textContent = '-';
  if (el('goals-month-label')) el('goals-month-label').textContent = '-';
  if (el('goals-members-live')) el('goals-members-live').textContent = '-';
  if (el('goals-score')) el('goals-score').textContent = '0%';
  if (el('goals-score-copy')) el('goals-score-copy').textContent = text.goals.scoreEmpty;
  if (el('goals-metrics-grid')) el('goals-metrics-grid').innerHTML = '';
  if (el('goals-insights')) {
    el('goals-insights').innerHTML = `<li class="goals-insight goals-insight--neutral"><div class="goals-insight-copy"><strong>${text.goals.labels.noGroupTitle}</strong><p>${text.goals.insightEmptyCopy}</p></div><span class="goals-insight-tag">${text.goals.labels.waiting}</span></li>`;
  }
}

async function loadGoals() {
  const empty = el('goals-empty');
  const content = el('goals-content');
  if (!chatId) {
    currentGoalsMetrics = null;
    if (empty) empty.style.display = 'flex';
    if (content) content.style.display = 'none';
    setGoalsFormDisabled(true);
    resetGoalsVisualState();
    return;
  }

  if (empty) empty.style.display = 'none';
  if (content) content.style.display = 'block';
  setGoalsFormDisabled(false);

  const results = await Promise.all([
    api('/api/stats/' + chatId),
    api('/api/reports/' + chatId),
    api('/api/members/' + chatId),
  ]);
  currentGoalsMetrics = buildGoalsMetrics(results[0], results[1], results[2]);
  const goals = getStoredGoals(currentGoalsMetrics);
  writeGoalsForm(goals);
  renderGoalsMetrics(currentGoalsMetrics, goals);
}

function previewGoals() {
  if (!currentGoalsMetrics) return;
  const goals = readGoalsForm();
  if (!goals) return;
  renderGoalsMetrics(currentGoalsMetrics, goals);
}

function saveGoals() {
  if (!chatId || !currentGoalsMetrics) {
    showToast(getUiText().goals.selectWarning, 'warning');
    return;
  }
  const goals = readGoalsForm();
  goalSettings[getGoalStorageKey()] = goals;
  saveStoredGoals();
  renderGoalsMetrics(currentGoalsMetrics, goals);
  showToast(getUiText().goals.saveToast, 'success');
}

function resetGoals() {
  if (!chatId || !currentGoalsMetrics) {
    showToast(getUiText().goals.selectWarning, 'warning');
    return;
  }
  delete goalSettings[getGoalStorageKey()];
  saveStoredGoals();
  const goals = getStoredGoals(currentGoalsMetrics);
  writeGoalsForm(goals);
  renderGoalsMetrics(currentGoalsMetrics, goals);
  showToast(getUiText().goals.resetToast, 'info');
}

function getFinanceStatusMeta(status) {
  const key = String(status || 'pending').toLowerCase();
  const labels = getUiText().statuses;
  const map = {
    paid: {label: labels.paid, tone: 'success'},
    approved: {label: labels.approved, tone: 'success'},
    completed: {label: labels.completed, tone: 'success'},
    success: {label: labels.success, tone: 'success'},
    succeeded: {label: labels.succeeded, tone: 'success'},
    pending: {label: labels.pending, tone: 'warning'},
    created: {label: labels.created, tone: 'warning'},
    processing: {label: labels.processing, tone: 'warning'},
    waiting_payment: {label: labels.waiting_payment, tone: 'warning'},
    waiting: {label: labels.waiting, tone: 'warning'},
    open: {label: labels.open, tone: 'warning'},
    expired: {label: labels.expired, tone: 'danger'},
    failed: {label: labels.failed, tone: 'danger'},
    cancelled: {label: labels.cancelled, tone: 'danger'},
    canceled: {label: labels.canceled, tone: 'danger'},
    refused: {label: labels.refused, tone: 'danger'},
    voided: {label: labels.voided, tone: 'danger'},
  };
  return map[key] || {label: key || labels.pending, tone: 'neutral'};
}

function getFinanceScope() {
  const hasGroup = Boolean(chatId);
  return {
    hasGroup,
    label: hasGroup ? getSelectedGroupLabel() : getUiText().finance.scopeGlobal,
    overviewUrl: hasGroup ? `/api/finance/overview/${chatId}` : '/api/finance/overview',
    paymentsUrl: hasGroup ? `/api/finance/payments/${chatId}` : '/api/finance/payments',
  };
}

function resetFinanceVisualState() {
  const text = getUiText();
  if (el('finance-group-title')) el('finance-group-title').textContent = text.finance.heroTitle;
  if (el('finance-group-caption')) el('finance-group-caption').textContent = text.finance.heroCaption;
  if (el('finance-active-payment')) {
    el('finance-active-payment').className = 'finance-active-empty';
    el('finance-active-payment').innerHTML = text.finance.emptyActive;
  }
  if (el('finance-payments-body')) {
    el('finance-payments-body').innerHTML = `<tr><td colspan="6" class="muted" style="padding:18px;text-align:center">${text.finance.emptyPayments}</td></tr>`;
  }
}

function fillFinanceSettings(settings) {
  const text = getUiText();
  financeState.settings = settings || {};
  const apiKeyInput = el('pixgo-api-key');
  const webhookSecretInput = el('pixgo-webhook-secret');
  const webhookUrlInput = el('pixgo-webhook-url');
  const defaultDescriptionInput = el('pixgo-default-description');
  const financeDescription = el('finance-description');
  const gatewayStatus = el('finance-gateway-status');
  const webhookEndpoint = el('finance-webhook-endpoint');

  if (apiKeyInput) {
    apiKeyInput.value = '';
    apiKeyInput.placeholder = settings && settings.api_key_set
      ? (currentLang === 'en' ? `Configured API key (${settings.api_key_preview})` : `API key configurada (${settings.api_key_preview})`)
      : text.finance.placeholders.apiKey;
  }
  if (webhookSecretInput) {
    webhookSecretInput.value = '';
    webhookSecretInput.placeholder = settings && settings.webhook_secret_set
      ? (currentLang === 'en' ? `Configured secret (${settings.webhook_secret_preview})` : `Secret configurado (${settings.webhook_secret_preview})`)
      : text.common.optional;
  }
  if (webhookUrlInput) webhookUrlInput.value = settings && settings.webhook_url ? settings.webhook_url : '';
  if (defaultDescriptionInput) defaultDescriptionInput.value = settings && settings.default_description ? settings.default_description : text.finance.placeholders.defaultDescription;
  if (financeDescription && !financeDescription.value.trim()) {
    financeDescription.value = settings && settings.default_description ? settings.default_description : text.finance.placeholders.defaultDescription;
  }
  if (gatewayStatus) {
    gatewayStatus.textContent = settings && settings.api_key_set
      ? text.finance.gatewayReady
      : text.finance.gatewayEmpty;
  }
  if (webhookEndpoint) webhookEndpoint.textContent = `${window.location.origin}/api/finance/pixgo/webhook`;
}

function renderFinanceSummary(summary) {
  const data = summary || {};
  if (el('finance-total-received')) el('finance-total-received').textContent = formatBRL(data.completed_amount || 0);
  if (el('finance-pending-amount')) el('finance-pending-amount').textContent = formatBRL(data.pending_amount || 0);
  if (el('finance-total-payments')) el('finance-total-payments').textContent = String(data.total_count || 0);
  if (el('finance-conversion-rate')) el('finance-conversion-rate').textContent = `${Number(data.conversion_rate || 0).toFixed(1).replace('.0', '')}%`;
}

function buildFinanceSummary(rows) {
  const list = Array.isArray(rows) ? rows : [];
  const completed = list.filter(function(row) {
    const key = String(row && row.status || '').toLowerCase();
    return ['paid', 'approved', 'completed', 'success', 'succeeded'].includes(key);
  });
  const pending = list.filter(function(row) {
    const key = String(row && row.status || '').toLowerCase();
    return ['pending', 'created', 'processing', 'waiting_payment', 'waiting', 'open'].includes(key);
  });
  const expired = list.filter(function(row) {
    const key = String(row && row.status || '').toLowerCase();
    return ['expired', 'cancelled', 'canceled', 'failed', 'refused', 'voided'].includes(key);
  });
  const total = list.length;
  const completedCount = completed.length;
  return {
    total_count: total,
    completed_count: completedCount,
    pending_count: pending.length,
    expired_count: expired.length,
    completed_amount: completed.reduce(function(sum, row) { return sum + Number(row.amount || 0); }, 0),
    pending_amount: pending.reduce(function(sum, row) { return sum + Number(row.amount || 0); }, 0),
    conversion_rate: total ? Number(((completedCount / total) * 100).toFixed(1)) : 0,
  };
}

function fillFinanceAccountFilter() {
  const select = el('finance-account-filter');
  const text = getUiText();
  if (!select) return;
  const accounts = (((financeState.settings || {}).accounts) || []).map(function(item) {
    return item && item.name ? String(item.name).trim() : '';
  }).filter(Boolean);
  const fromRows = (financeState.payments || []).map(function(item) {
    return item && item.provider_account ? String(item.provider_account).trim() : '';
  }).filter(Boolean);
  const unique = Array.from(new Set(accounts.concat(fromRows)));
  const current = financeState.selectedAccount || '';
  select.innerHTML = '';
  const allOption = document.createElement('option');
  allOption.value = '';
  allOption.textContent = text.finance.accountFilterAll;
  select.appendChild(allOption);
  unique.forEach(function(name) {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    select.appendChild(option);
  });
  select.value = unique.includes(current) ? current : '';
  financeState.selectedAccount = select.value || '';
}

function getFilteredFinancePayments() {
  const selected = String(financeState.selectedAccount || '').trim().toLowerCase();
  if (!selected) return Array.isArray(financeState.payments) ? financeState.payments.slice() : [];
  return (financeState.payments || []).filter(function(row) {
    return String(row && row.provider_account || '').trim().toLowerCase() === selected;
  });
}

function applyFinanceAccountFilter() {
  const select = el('finance-account-filter');
  financeState.selectedAccount = select ? String(select.value || '').trim() : '';
  financeState.filteredPayments = getFilteredFinancePayments();
  const filteredSummary = buildFinanceSummary(financeState.filteredPayments);
  const activeId = financeState.activePayment && financeState.activePayment.payment_id ? String(financeState.activePayment.payment_id) : '';
  financeState.activePayment = financeState.filteredPayments.find(function(row) {
    return String(row.payment_id || '') === activeId;
  }) || financeState.filteredPayments[0] || null;
  renderFinanceSummary(filteredSummary);
  renderFinancePayments(financeState.filteredPayments);
  renderFinanceActivePayment(financeState.activePayment);
}

function getFinanceDisplayTimestamp(row) {
  if (!row) return '';
  const status = String(row.status || '').toLowerCase();
  if (['paid', 'approved', 'completed', 'success', 'succeeded'].includes(status) && row.completed_at) {
    return String(row.completed_at).trim();
  }
  return String(row.updated_at || row.created_at || '').trim();
}

function renderFinanceTimestamp(value) {
  const parts = formatPanelDateTimeParts(value);
  if (!parts) return '-';
  return `${escHtml(parts.date)} - ${escHtml(parts.time)}`;
}

function renderFinancePayments(rows) {
  const text = getUiText();
  const tbody = el('finance-payments-body');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!Array.isArray(rows) || !rows.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="muted" style="padding:18px;text-align:center">${text.finance.emptyFiltered}</td></tr>`;
    return;
  }
  rows.forEach(function(row) {
    const meta = getFinanceStatusMeta(row.status);
    const accountLabel = row.provider_account || 'PIXGO';
    const sourceLabel = row.chat_id ? String(row.chat_id) : text.finance.webhookExternal;
    const compactDescription = row.description ? `${accountLabel} - ${row.description}` : accountLabel;
    const updatedLabel = renderFinanceTimestamp(getFinanceDisplayTimestamp(row));
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="finance-table-title">${escHtml(row.external_id || row.payment_id || '-')}</div>
        <div class="finance-table-sub">${escHtml(compactDescription)}</div>
      </td>
      <td>
        <div class="finance-table-title">${escHtml(row.customer_name || text.finance.notProvided)}</div>
        <div class="finance-table-sub">${escHtml(row.customer_email || row.customer_phone || sourceLabel)}</div>
      </td>
      <td><strong>${formatBRL(row.amount)}</strong></td>
      <td><span class="finance-status-badge finance-status-badge--${meta.tone}">${meta.label}</span></td>
      <td class="muted finance-updated-cell">${updatedLabel}</td>
      <td>
        <button class="btn-secondary finance-inline-btn" onclick="refreshFinancePayment('${String(row.payment_id).replace(/'/g, "\\'")}')">â†»</button>
      </td>
    `;
    tr.addEventListener('click', function() {
      financeState.activePayment = row;
      renderFinanceActivePayment(row);
    });
    tbody.appendChild(tr);
  });
}

function renderFinanceActivePayment(payment) {
  const text = getUiText();
  const box = el('finance-active-payment');
  if (!box) return;
  if (!payment) {
    box.className = 'finance-active-empty';
    box.innerHTML = text.finance.emptyActive;
    return;
  }
  const meta = getFinanceStatusMeta(payment.status);
  const qrCode = payment.qr_code || '';
  const qrImage = payment.qr_image_url || '';
  box.className = 'finance-active-card';
  box.innerHTML = `
    <div class="finance-active-head">
      <div>
        <span class="finance-active-kicker">${escHtml(payment.provider_account || 'PIXGO')}</span>
        <strong>${escHtml(payment.description || payment.external_id || payment.payment_id)}</strong>
      </div>
      <span class="finance-status-badge finance-status-badge--${meta.tone}">${meta.label}</span>
    </div>
    <div class="finance-active-grid">
      <div class="finance-active-stat">
        <span>${text.finance.activeLabels.amount}</span>
        <strong>${formatBRL(payment.amount)}</strong>
      </div>
      <div class="finance-active-stat">
        <span>${text.finance.activeLabels.customer}</span>
        <strong>${escHtml(payment.customer_name || text.finance.notProvided)}</strong>
      </div>
      <div class="finance-active-stat">
        <span>${text.finance.activeLabels.payment}</span>
        <strong>${escHtml(payment.payment_id || '-')}</strong>
      </div>
      <div class="finance-active-stat">
        <span>${text.finance.activeLabels.expiresAt}</span>
        <strong>${renderFinanceTimestamp(payment.expires_at)}</strong>
      </div>
    </div>
    <div class="finance-active-code">
      <span>${text.finance.activeLabels.pixCode}</span>
      <textarea readonly>${escHtml(qrCode || text.finance.qrPending)}</textarea>
    </div>
    <div class="finance-active-actions">
      <button class="btn-primary" onclick="copyFinanceQrCode('${String(qrCode).replace(/'/g, "\\'")}')">${text.finance.buttons.copyPix}</button>
      <button class="btn-secondary" onclick="refreshFinancePayment('${String(payment.payment_id).replace(/'/g, "\\'")}')">${text.finance.refreshStatus}</button>
      ${qrImage ? `<button class="btn-secondary" onclick="openFinanceQrImage('${String(qrImage).replace(/'/g, "\\'")}')">${text.finance.buttons.openQr}</button>` : ''}
    </div>
  `;
}

function stopFinancePolling() {
  if (financeState.pollTimer) {
    clearInterval(financeState.pollTimer);
    financeState.pollTimer = null;
  }
  financeState.pollBusy = false;
}

async function pollFinanceUpdates() {
  if (financeState.pollBusy || activeView !== 'finance' || document.hidden) return;
  financeState.pollBusy = true;
  try {
    await loadFinance();
  } catch (e) {
    console.warn('Finance live polling failed:', e);
  } finally {
    financeState.pollBusy = false;
  }
}

function syncFinancePolling() {
  if (activeView !== 'finance') {
    stopFinancePolling();
    return;
  }
  if (financeState.pollTimer) return;
  financeState.pollTimer = setInterval(function() {
    pollFinanceUpdates();
  }, FINANCE_LIVE_REFRESH_MS);
}

async function loadFinance() {
  const scope = getFinanceScope();
  const text = getUiText();
  try {
    const settings = await api('/api/finance/pixgo/settings');
    fillFinanceSettings(settings);
  } catch(e) {
    fillFinanceSettings({});
  }

  if (el('finance-group-title')) el('finance-group-title').textContent = scope.hasGroup ? text.finance.heroGroupTitle(scope.label) : text.finance.heroTitle;
  if (el('finance-group-caption')) {
    el('finance-group-caption').textContent = scope.hasGroup
      ? text.finance.heroGroupCaption(scope.label)
      : text.finance.heroGlobalCaption;
  }
  if (el('finance-empty')) el('finance-empty').style.display = 'none';
  if (el('finance-content')) el('finance-content').style.display = 'block';

  const [overview, payments] = await Promise.all([
    api(scope.overviewUrl),
    api(scope.paymentsUrl),
  ]);
  financeState.summary = overview.summary || null;
  financeState.payments = Array.isArray(payments) ? payments : [];
  fillFinanceAccountFilter();
  financeState.filteredPayments = getFilteredFinancePayments();
  const overviewActiveId = overview.active_payment && overview.active_payment.payment_id ? String(overview.active_payment.payment_id) : '';
  financeState.activePayment = financeState.filteredPayments.find(function(row) {
    return String(row.payment_id || '') === overviewActiveId;
  }) || financeState.filteredPayments[0] || null;
  renderFinanceSummary(buildFinanceSummary(financeState.filteredPayments));
  renderFinancePayments(financeState.filteredPayments);
  renderFinanceActivePayment(financeState.activePayment);
  syncFinancePolling();
}

function getNameSearchConfig(searchType) {
  return NAME_SEARCH_TYPES[searchType] || NAME_SEARCH_TYPES.nome;
}

function getNameSearchTypeLabel(searchType) {
  const cfg = getNameSearchConfig(searchType);
  const langKey = currentLang === 'en' ? 'en' : 'pt';
  return String((cfg.labels && cfg.labels[langKey]) || searchType || 'nome');
}

function getNameSearchRows(rawPayload, fallbackRows) {
  if (Array.isArray(fallbackRows) && fallbackRows.length) return fallbackRows;
  if (Array.isArray(rawPayload)) return rawPayload;
  if (rawPayload && typeof rawPayload === 'object' && Array.isArray(rawPayload.RESULTADOS)) return rawPayload.RESULTADOS;
  return [];
}

function stringifyNameSearchPayload(payload) {
  if (payload === null || typeof payload === 'undefined') return '';
  if (typeof payload === 'string') return payload;
  try {
    return JSON.stringify(payload, null, 2);
  } catch (e) {
    return String(payload);
  }
}

function normalizeNameSearchValue(value) {
  if (value === null || typeof value === 'undefined') return '-';
  const text = String(value).trim();
  if (!text || text.toUpperCase() === 'NULL') return '-';
  return text;
}

function formatNameSearchPhone(item) {
  if (item === null || typeof item === 'undefined') return '';
  if (typeof item === 'string' || typeof item === 'number') return normalizeNameSearchValue(item);
  if (typeof item !== 'object') return '';
  const ddd = normalizeNameSearchValue(item.DDD || item.ddd || '');
  const number = normalizeNameSearchValue(item.TELEFONE || item.telefone || item.NUMERO || item.numero || '');
  if (ddd !== '-' && number !== '-') return `(${ddd}) ${number}`;
  if (number !== '-') return number;
  if (ddd !== '-') return ddd;
  return '';
}

function formatNameSearchEmail(item) {
  if (item === null || typeof item === 'undefined') return '';
  if (typeof item === 'string' || typeof item === 'number') return normalizeNameSearchValue(item);
  if (typeof item !== 'object') return '';
  return normalizeNameSearchValue(item.EMAIL || item.email || item.MAIL || item.mail || '');
}

function formatNameSearchAddress(item) {
  if (item === null || typeof item === 'undefined') return '';
  if (typeof item === 'string' || typeof item === 'number') return normalizeNameSearchValue(item);
  if (typeof item !== 'object') return '';
  const type = normalizeNameSearchValue(item.LOGR_TIPO || item.logr_tipo || '');
  const name = normalizeNameSearchValue(item.LOGR_NOME || item.logr_nome || item.ENDERECO || item.endereco || '');
  const number = normalizeNameSearchValue(item.LOGR_NUMERO || item.logr_numero || item.NUMERO || item.numero || '');
  const city = normalizeNameSearchValue(item.CIDADE || item.cidade || '');
  const uf = normalizeNameSearchValue(item.UF || item.uf || '');
  const cep = normalizeNameSearchValue(item.CEP || item.cep || '');
  const baseParts = [type, name, number].filter(function(v) { return v !== '-'; });
  const cityUf = city !== '-' && uf !== '-' ? `${city}/${uf}` : (city !== '-' ? city : (uf !== '-' ? uf : ''));
  const parts = [];
  if (baseParts.length) parts.push(baseParts.join(' '));
  if (cityUf) parts.push(cityUf);
  if (cep !== '-') parts.push(`CEP ${cep}`);
  return parts.join(' - ') || '';
}

function getNameSearchPlaceholder(searchType) {
  const text = getUiText().nameSearch;
  if (text && text.placeholderByType && text.placeholderByType[searchType]) {
    return text.placeholderByType[searchType];
  }
  return 'Digite o valor para pesquisar';
}

function updateNameSearchTypeUI() {
  const typeSelect = el('name-search-type');
  const activeType = typeSelect ? String(typeSelect.value || nameSearchState.searchType || 'nome').toLowerCase() : (nameSearchState.searchType || 'nome');
  const input = el('name-search-input');
  if (input) input.placeholder = getNameSearchPlaceholder(activeType);
}

function renderNameSearchSummary(state) {
  const current = state || nameSearchState;
  const list = getNameSearchRows(current.raw, current.rows);
  const jsonDump = stringifyNameSearchPayload(current.raw);
  const sizeBytes = jsonDump ? (new Blob([jsonDump]).size || 0) : 0;
  const sizeLabel = sizeBytes >= 1024 ? `${(sizeBytes / 1024).toFixed(1)} KB` : `${sizeBytes} B`;
  if (el('name-search-total')) el('name-search-total').textContent = String(Number(current.total || list.length || 0));
  if (el('name-search-records')) el('name-search-records').textContent = String(list.length);
  if (el('name-search-json-size')) el('name-search-json-size').textContent = sizeLabel;
}

function createNameSearchRecordItem(label, value) {
  const item = document.createElement('div');
  item.className = 'name-search-record-item';

  const itemLabel = document.createElement('div');
  itemLabel.className = 'name-search-record-item-label';
  itemLabel.textContent = label;
  item.appendChild(itemLabel);

  const itemValue = document.createElement('div');
  itemValue.className = 'name-search-record-item-value';
  itemValue.textContent = normalizeNameSearchValue(value);
  item.appendChild(itemValue);

  return item;
}

function buildNameSearchRecordNode(row) {
  const text = getUiText().nameSearch;
  const labels = text.fields || {};
  const data = row && typeof row === 'object' && row.DADOS && typeof row.DADOS === 'object' ? row.DADOS : {};

  const phones = Array.isArray(row && row.TELEFONE) ? row.TELEFONE.map(formatNameSearchPhone).filter(Boolean) : [];
  const emails = Array.isArray(row && row.EMAIL) ? row.EMAIL.map(formatNameSearchEmail).filter(Boolean) : [];
  const addresses = Array.isArray(row && row.ENDERECOS) ? row.ENDERECOS.map(formatNameSearchAddress).filter(Boolean) : [];

  const wrapper = document.createElement('div');
  wrapper.className = 'name-search-record';

  const grid = document.createElement('div');
  grid.className = 'name-search-record-grid';
  grid.appendChild(createNameSearchRecordItem(labels.name || 'Nome', data.NOME || data.name || data.nome || ''));
  grid.appendChild(createNameSearchRecordItem(labels.cpf || 'CPF', data.CPF || data.cpf || ''));
  grid.appendChild(createNameSearchRecordItem(labels.birth || 'Nascimento', data.NASC || data.DT_NASC || data.birth_date || ''));
  grid.appendChild(createNameSearchRecordItem(labels.sex || 'Sexo', data.SEXO || data.sex || ''));
  grid.appendChild(createNameSearchRecordItem(labels.mother || 'Mae', data.NOME_MAE || data.mae || data.mother_name || ''));
  grid.appendChild(createNameSearchRecordItem(labels.father || 'Pai', data.NOME_PAI || data.pai || data.father_name || ''));
  grid.appendChild(createNameSearchRecordItem(labels.rg || 'RG', data.RG || data.rg || ''));
  grid.appendChild(createNameSearchRecordItem(labels.title || 'Titulo eleitor', data.TITULO_ELEITOR || data.titulo || ''));
  grid.appendChild(createNameSearchRecordItem(labels.contactsId || 'Contatos ID', data.CONTATOS_ID || data.contatos_id || ''));
  grid.appendChild(createNameSearchRecordItem(labels.cadastroId || 'Cadastro ID', data.CADASTRO_ID || data.cadastro_id || ''));
  grid.appendChild(createNameSearchRecordItem(labels.phones || 'Telefones', phones.length ? phones.join(' | ') : '-'));
  grid.appendChild(createNameSearchRecordItem(labels.emails || 'Emails', emails.length ? emails.join(' | ') : '-'));
  grid.appendChild(createNameSearchRecordItem(labels.address || 'Endereco', addresses.length ? addresses.slice(0, 2).join(' | ') : '-'));
  wrapper.appendChild(grid);

  const details = document.createElement('details');
  details.className = 'name-search-record-raw';
  const summary = document.createElement('summary');
  summary.textContent = text.recordRawSummary || 'Ver todos os campos deste registro';
  details.appendChild(summary);
  const pre = document.createElement('pre');
  pre.className = 'name-search-json-snippet';
  pre.textContent = stringifyNameSearchPayload(row);
  details.appendChild(pre);
  wrapper.appendChild(details);

  return wrapper;
}

function renderNameSearchRows(state) {
  const text = getUiText().nameSearch;
  const current = state || nameSearchState;
  const tbody = el('name-search-body');
  if (!tbody) return;
  tbody.innerHTML = '';
  const list = getNameSearchRows(current.raw, current.rows);
  if (!list.length) {
    const emptyLabel = current.query ? text.empty : text.idle;
    tbody.innerHTML = `<tr><td colspan="3" class="muted" style="padding:18px;text-align:center">${escHtml(emptyLabel)}</td></tr>`;
    return;
  }

  const typeLabel = getNameSearchTypeLabel(current.searchType);
  const endpointLabel = current.endpoint ? `Endpoint: ${current.endpoint}` : '';
  list.forEach(function(row, idx) {
    const tr = document.createElement('tr');

    const idxTd = document.createElement('td');
    const idxMain = document.createElement('div');
    idxMain.className = 'name-search-main';
    idxMain.textContent = `#${idx + 1}`;
    idxTd.appendChild(idxMain);

    const typeTd = document.createElement('td');
    const typeMain = document.createElement('div');
    typeMain.className = 'name-search-main';
    typeMain.textContent = typeLabel;
    typeTd.appendChild(typeMain);
    if (endpointLabel) {
      const typeSub = document.createElement('div');
      typeSub.className = 'name-search-sub';
      typeSub.textContent = endpointLabel;
      typeTd.appendChild(typeSub);
    }

    const dataTd = document.createElement('td');
    dataTd.appendChild(buildNameSearchRecordNode(row));

    tr.appendChild(idxTd);
    tr.appendChild(typeTd);
    tr.appendChild(dataTd);
    tbody.appendChild(tr);
  });
}

function getNameSearchNodeKind(value) {
  if (value === null) return 'nullValue';
  if (typeof value === 'undefined') return 'undefinedValue';
  if (Array.isArray(value)) return 'array';
  if (typeof value === 'object') return 'object';
  if (typeof value === 'string') return 'string';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'boolean') return 'boolean';
  return 'string';
}

function stringifyNameSearchLeafValue(value) {
  if (typeof value === 'undefined') return 'undefined';
  try {
    const serialized = JSON.stringify(value);
    if (typeof serialized === 'string') return serialized;
  } catch (e) {}
  return String(value);
}

function getNameSearchNodeMeta(value, nodeTypes) {
  const kind = getNameSearchNodeKind(value);
  if (kind === 'array') return `${nodeTypes.array || 'list'} (${value.length})`;
  if (kind === 'object') return `${nodeTypes.object || 'object'} (${Object.keys(value).length})`;
  return nodeTypes[kind] || kind;
}

function createNameSearchStructuredMetaLine(label, value) {
  const line = document.createElement('div');
  line.className = 'name-search-structured-meta';

  const labelNode = document.createElement('span');
  labelNode.className = 'name-search-structured-meta-label';
  labelNode.textContent = `${label}: `;
  line.appendChild(labelNode);

  const valueNode = document.createElement('span');
  valueNode.textContent = normalizeNameSearchValue(value);
  line.appendChild(valueNode);

  return line;
}

function getNameSearchNodePath(parentPath, key) {
  const keyText = String(key);
  if (!parentPath) return keyText;
  if (keyText.startsWith('[')) return `${parentPath}${keyText}`;
  return `${parentPath}.${keyText}`;
}

function getNameSearchNodeValueSummary(value, nodeTypes) {
  const kind = getNameSearchNodeKind(value);
  if (kind === 'object') return Object.keys(value).length ? getNameSearchNodeMeta(value, nodeTypes) : '{}';
  if (kind === 'array') return value.length ? getNameSearchNodeMeta(value, nodeTypes) : '[]';
  return stringifyNameSearchLeafValue(value);
}

function collectNameSearchStructuredRows(key, value, parentPath, text, rows) {
  const nodeTypes = text.nodeTypes || {};
  const kind = getNameSearchNodeKind(value);
  const path = getNameSearchNodePath(parentPath, key);

  rows.push({
    path: path,
    type: nodeTypes[kind] || kind,
    value: getNameSearchNodeValueSummary(value, nodeTypes),
  });

  if (kind === 'array') {
    value.forEach(function(item, idx) {
      collectNameSearchStructuredRows(`[${idx}]`, item, path, text, rows);
    });
    return;
  }

  if (kind === 'object') {
    Object.keys(value).forEach(function(childKey) {
      collectNameSearchStructuredRows(childKey, value[childKey], path, text, rows);
    });
  }
}

function buildNameSearchStructuredTableCard(rows, text) {
  const headers = text.structuredFlatHeaders || {};
  const countText = typeof text.structuredFlatCount === 'function'
    ? text.structuredFlatCount(rows.length)
    : `${rows.length}`;

  const card = document.createElement('div');
  card.className = 'name-search-structured-card';

  const title = document.createElement('div');
  title.className = 'name-search-structured-title';
  title.textContent = text.structuredFlatTitle || 'Tabela completa de campos (caminho -> valor)';
  card.appendChild(title);

  const countLine = document.createElement('div');
  countLine.className = 'name-search-structured-meta';
  countLine.textContent = countText;
  card.appendChild(countLine);

  const tableWrap = document.createElement('div');
  tableWrap.className = 'name-search-flat-wrap';

  const table = document.createElement('table');
  table.className = 'name-search-flat-table';

  const thead = document.createElement('thead');
  thead.innerHTML = `
    <tr>
      <th>${escHtml(headers.path || 'Path')}</th>
      <th>${escHtml(headers.type || 'Type')}</th>
      <th>${escHtml(headers.value || 'Value')}</th>
    </tr>
  `;
  table.appendChild(thead);

  const tbody = document.createElement('tbody');
  rows.forEach(function(row) {
    const tr = document.createElement('tr');

    const pathTd = document.createElement('td');
    pathTd.className = 'name-search-flat-path';
    pathTd.textContent = row.path;
    tr.appendChild(pathTd);

    const typeTd = document.createElement('td');
    typeTd.className = 'name-search-flat-type';
    typeTd.textContent = row.type;
    tr.appendChild(typeTd);

    const valueTd = document.createElement('td');
    valueTd.className = 'name-search-flat-value';
    valueTd.textContent = row.value;
    tr.appendChild(valueTd);

    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  tableWrap.appendChild(table);
  card.appendChild(tableWrap);
  return card;
}

function buildNameSearchTreeNode(key, value, depth, text) {
  const nodeTypes = text.nodeTypes || {};
  const kind = getNameSearchNodeKind(value);
  const label = String(key);

  if (kind === 'object' || kind === 'array') {
    const node = document.createElement('details');
    node.className = 'name-search-tree-node';
    if (depth <= 1) node.open = true;

    const summary = document.createElement('summary');
    summary.className = 'name-search-tree-summary';

    const keyNode = document.createElement('span');
    keyNode.className = 'name-search-tree-key';
    keyNode.textContent = label;
    summary.appendChild(keyNode);

    const metaNode = document.createElement('span');
    metaNode.className = 'name-search-tree-meta';
    metaNode.textContent = getNameSearchNodeMeta(value, nodeTypes);
    summary.appendChild(metaNode);

    node.appendChild(summary);

    const children = document.createElement('div');
    children.className = 'name-search-tree-children';

    const entries = kind === 'array'
      ? value.map(function(item, idx) { return [`[${idx}]`, item]; })
      : Object.keys(value).map(function(childKey) { return [childKey, value[childKey]]; });

    if (!entries.length) {
      const empty = document.createElement('div');
      empty.className = 'name-search-tree-empty';
      empty.textContent = nodeTypes.empty || 'empty';
      children.appendChild(empty);
    } else {
      entries.forEach(function(entry) {
        children.appendChild(buildNameSearchTreeNode(entry[0], entry[1], depth + 1, text));
      });
    }

    node.appendChild(children);
    return node;
  }

  const leaf = document.createElement('div');
  leaf.className = 'name-search-tree-leaf';

  const leafKey = document.createElement('span');
  leafKey.className = 'name-search-tree-key';
  leafKey.textContent = label;
  leaf.appendChild(leafKey);

  const leafMeta = document.createElement('span');
  leafMeta.className = 'name-search-tree-meta';
  leafMeta.textContent = nodeTypes[kind] || kind;
  leaf.appendChild(leafMeta);

  const leafValue = document.createElement('div');
  leafValue.className = 'name-search-tree-value';
  leafValue.textContent = stringifyNameSearchLeafValue(value);
  leaf.appendChild(leafValue);

  return leaf;
}

function renderNameSearchStructuredPayload(state) {
  const text = getUiText().nameSearch;
  const labels = text.labels || {};
  const current = state || nameSearchState;
  const container = el('name-search-structured');
  if (!container) return;

  if (current.raw === null || typeof current.raw === 'undefined') {
    container.className = 'name-search-structured-empty';
    container.textContent = text.rawIdle;
    return;
  }

  const list = getNameSearchRows(current.raw, current.rows);
  container.className = 'name-search-structured-layout';
  container.innerHTML = '';

  const summaryCard = document.createElement('div');
  summaryCard.className = 'name-search-structured-card';

  const summaryTitle = document.createElement('div');
  summaryTitle.className = 'name-search-structured-title';
  summaryTitle.textContent = text.structuredOverviewTitle || 'Resumo da consulta';
  summaryCard.appendChild(summaryTitle);

  summaryCard.appendChild(createNameSearchStructuredMetaLine(labels.query || 'Consulta', current.query));
  summaryCard.appendChild(createNameSearchStructuredMetaLine(labels.type || 'Tipo', getNameSearchTypeLabel(current.searchType)));
  summaryCard.appendChild(createNameSearchStructuredMetaLine(labels.records || 'Registros em RESULTADOS', String(list.length)));
  summaryCard.appendChild(createNameSearchStructuredMetaLine(labels.endpoint || 'Endpoint', current.endpoint));
  summaryCard.appendChild(createNameSearchStructuredMetaLine(labels.source || 'Fonte', current.source));
  container.appendChild(summaryCard);

  const treeCard = document.createElement('div');
  treeCard.className = 'name-search-structured-card name-search-tree-card';

  const treeTitle = document.createElement('div');
  treeTitle.className = 'name-search-structured-title';
  treeTitle.textContent = text.structuredRootSummary || 'JSON bruto completo estruturado';
  treeCard.appendChild(treeTitle);

  const rootKey = text.structuredRootKey || 'ROOT';
  const treeRoot = buildNameSearchTreeNode(rootKey, current.raw, 0, text);
  treeRoot.classList.add('name-search-tree-root');
  treeCard.appendChild(treeRoot);

  container.appendChild(treeCard);

  const flatRows = [];
  collectNameSearchStructuredRows(rootKey, current.raw, '', text, flatRows);
  container.appendChild(buildNameSearchStructuredTableCard(flatRows, text));
}

function renderNameSearchRawPayload(state) {
  const text = getUiText().nameSearch;
  const current = state || nameSearchState;
  const details = el('name-search-json-details');
  const rawNode = el('name-search-json');
  if (!rawNode) return;
  if (current.raw === null || typeof current.raw === 'undefined') {
    rawNode.textContent = text.rawIdle;
    if (details) details.open = false;
    return;
  }
  rawNode.textContent = stringifyNameSearchPayload(current.raw);
}

function loadNameSearch() {
  const text = getUiText().nameSearch;
  const typeSelect = el('name-search-type');
  if (typeSelect) typeSelect.value = nameSearchState.searchType || 'nome';
  updateNameSearchTypeUI();
  renderNameSearchSummary(nameSearchState);
  renderNameSearchRows(nameSearchState);
  renderNameSearchStructuredPayload(nameSearchState);
  renderNameSearchRawPayload(nameSearchState);
  if (!nameSearchState.query && el('name-search-msg')) {
    showMsg('name-search-msg', text.idle, true);
  }
}

async function searchNames() {
  const text = getUiText().nameSearch;
  const input = el('name-search-input');
  const typeSelect = el('name-search-type');
  const query = input ? String(input.value || '').trim() : '';
  const searchType = typeSelect ? String(typeSelect.value || 'nome').trim().toLowerCase() : 'nome';
  const cfg = getNameSearchConfig(searchType);
  const minChars = Number(cfg.minChars || 1);
  const typeLabel = getNameSearchTypeLabel(searchType);

  if (query.length < minChars) {
    const msg = typeof text.minChars === 'function' ? text.minChars(minChars, typeLabel) : text.minChars;
    showMsg('name-search-msg', msg, false);
    renderNameSearchSummary({
      query: query,
      searchType: searchType,
      rows: [],
      raw: null,
      endpoint: '',
      source: '',
      total: 0,
    });
    renderNameSearchRows({
      query: query,
      searchType: searchType,
      rows: [],
      raw: null,
      endpoint: '',
      source: '',
      total: 0,
    });
    renderNameSearchStructuredPayload({ raw: null });
    renderNameSearchRawPayload({ raw: null });
    return;
  }

  const loadingText = typeof text.loading === 'function' ? text.loading(typeLabel) : text.loading;
  showMsg('name-search-msg', loadingText, true);

  try {
    const data = await api(`/api/name-search?tipo=${encodeURIComponent(searchType)}&valor=${encodeURIComponent(query)}`);
    const payload = Object.prototype.hasOwnProperty.call(data, 'raw') ? data.raw : data;
    const rows = getNameSearchRows(payload, data.results);
    nameSearchState = {
      query: query,
      searchType: searchType,
      rows: rows,
      raw: payload,
      endpoint: String(data.endpoint || ''),
      source: String(data.source || ''),
      total: Number(data.total || rows.length || 0),
    };
    renderNameSearchSummary(nameSearchState);
    renderNameSearchRows(nameSearchState);
    renderNameSearchStructuredPayload(nameSearchState);
    renderNameSearchRawPayload(nameSearchState);
    const foundText = typeof text.found === 'function'
      ? text.found(Number(nameSearchState.total || rows.length), query, typeLabel)
      : `${rows.length}`;
    showMsg('name-search-msg', foundText, true);
  } catch (e) {
    nameSearchState = {
      query: query,
      searchType: searchType,
      rows: [],
      raw: null,
      endpoint: '',
      source: '',
      total: 0,
    };
    renderNameSearchSummary(nameSearchState);
    renderNameSearchRows(nameSearchState);
    renderNameSearchStructuredPayload(nameSearchState);
    renderNameSearchRawPayload(nameSearchState);
    showMsg('name-search-msg', (currentLang === 'en' ? 'Search error: ' : 'Erro na busca: ') + e.message, false);
  }
}

function clearNameSearch() {
  const text = getUiText().nameSearch;
  if (el('name-search-input')) el('name-search-input').value = '';
  const typeSelect = el('name-search-type');
  const searchType = typeSelect ? String(typeSelect.value || 'nome').trim().toLowerCase() : 'nome';
  nameSearchState = {
    query: '',
    searchType: searchType,
    rows: [],
    raw: null,
    endpoint: '',
    source: '',
    total: 0,
  };
  updateNameSearchTypeUI();
  renderNameSearchSummary(nameSearchState);
  renderNameSearchRows(nameSearchState);
  renderNameSearchStructuredPayload(nameSearchState);
  renderNameSearchRawPayload(nameSearchState);
  showMsg('name-search-msg', text.idle, true);
}

function onNameSearchTypeChange() {
  const typeSelect = el('name-search-type');
  const selectedType = typeSelect ? String(typeSelect.value || 'nome').trim().toLowerCase() : 'nome';
  nameSearchState.searchType = selectedType;
  updateNameSearchTypeUI();
}

function fillPixelSettings(settings) {
  const text = getUiText().pixel;
  if (el('pixel-id')) el('pixel-id').value = settings && settings.pixel_id ? String(settings.pixel_id) : '';
  if (el('pixel-ad-account-id')) el('pixel-ad-account-id').value = settings && settings.ad_account_id ? String(settings.ad_account_id) : '';
  if (el('pixel-dataset-id')) el('pixel-dataset-id').value = settings && settings.dataset_id ? String(settings.dataset_id) : '';
  if (el('pixel-test-event-code')) el('pixel-test-event-code').value = settings && settings.test_event_code ? String(settings.test_event_code) : '';
  if (el('pixel-access-token')) el('pixel-access-token').value = '';
  if (el('pixel-token-note')) {
    el('pixel-token-note').textContent = settings && settings.access_token_set
      ? text.tokenConfigured(settings.access_token_preview || '')
      : text.tokenMissing;
  }
  if (el('pixel-summary-pixel-id')) el('pixel-summary-pixel-id').textContent = (settings && settings.pixel_id) || text.notInformed;
  if (el('pixel-summary-ad-account')) el('pixel-summary-ad-account').textContent = (settings && settings.ad_account_id) || text.notInformed;
  if (el('pixel-summary-dataset')) el('pixel-summary-dataset').textContent = (settings && settings.dataset_id) || text.notInformed;
  if (el('pixel-summary-token')) el('pixel-summary-token').textContent = settings && settings.access_token_set
    ? (settings.access_token_preview || text.connected)
    : text.tokenNotConfigured;
}

function renderPixelOverview(overview) {
  const text = getUiText().pixel;
  const ready = Boolean(overview && overview.ready);
  if (el('pixel-kicker')) el('pixel-kicker').textContent = text.kicker;
  if (el('pixel-title')) el('pixel-title').textContent = text.title;
  if (el('pixel-copy')) el('pixel-copy').textContent = text.copy;
  if (el('pixel-status-kicker')) el('pixel-status-kicker').textContent = text.statusKicker;
  if (el('pixel-status-title')) el('pixel-status-title').textContent = ready ? text.statusReady : text.statusWaiting;
  if (el('pixel-status-copy')) el('pixel-status-copy').textContent = overview && overview.next_step
    ? String(overview.next_step)
    : (ready ? text.statusCopyReady : text.statusCopyWaiting);
  if (el('pixel-ready-badge')) {
    el('pixel-ready-badge').textContent = ready ? text.connected : text.disconnected;
    el('pixel-ready-badge').classList.toggle('is-ready', ready);
  }
  if (el('pixel-last-sync')) {
    el('pixel-last-sync').textContent = overview && overview.last_sync_at
      ? `${text.lastSyncPrefix}: ${overview.last_sync_at}`
      : text.neverSynced;
  }
  if (el('pixel-campaigns-running')) el('pixel-campaigns-running').textContent = String(overview && overview.campaigns_running || 0);
  if (el('pixel-campaigns-paused')) el('pixel-campaigns-paused').textContent = String(overview && overview.campaigns_paused || 0);
  if (el('pixel-clicks-today')) el('pixel-clicks-today').textContent = String(overview && overview.clicks_today || 0);
  if (el('pixel-leads-today')) el('pixel-leads-today').textContent = String(overview && overview.leads_today || 0);
  if (el('pixel-next-step-title')) el('pixel-next-step-title').textContent = ready ? text.nextStepReady : text.nextStepWaiting;
  if (el('pixel-next-step-copy')) el('pixel-next-step-copy').textContent = overview && overview.next_step
    ? String(overview.next_step)
    : (ready ? text.statusCopyReady : text.statusCopyWaiting);
}

async function loadPixel() {
  try {
    const [settings, overview] = await Promise.all([
      api('/api/meta/settings'),
      api('/api/meta/overview'),
    ]);
    fillPixelSettings(settings || {});
    renderPixelOverview(overview || {});
  } catch (e) {
    showToast((currentLang === 'en' ? 'Could not load Meta settings: ' : 'Erro ao carregar configuracao da Meta: ') + e.message, 'error');
  }
}

async function savePixelSettings() {
  try {
    await postJson('/api/meta/settings', {
      pixel_id: el('pixel-id') ? el('pixel-id').value.trim() : '',
      ad_account_id: el('pixel-ad-account-id') ? el('pixel-ad-account-id').value.trim() : '',
      access_token: el('pixel-access-token') ? el('pixel-access-token').value.trim() : '',
      dataset_id: el('pixel-dataset-id') ? el('pixel-dataset-id').value.trim() : '',
      test_event_code: el('pixel-test-event-code') ? el('pixel-test-event-code').value.trim() : '',
    });
    showToast(getUiText().pixel.saveToast, 'success');
    await loadPixel();
  } catch (e) {
    showToast((currentLang === 'en' ? 'Could not save Meta configuration: ' : 'Erro ao salvar configuracao da Meta: ') + e.message, 'error');
  }
}

async function refreshPixelOverview() {
  await loadPixel();
}

async function saveFinanceSettings() {
  try {
    const payload = {
      api_key: financeInputValue('pixgo-api-key'),
      webhook_secret: financeInputValue('pixgo-webhook-secret'),
      webhook_url: financeInputValue('pixgo-webhook-url'),
      default_description: financeInputValue('pixgo-default-description'),
    };
    await postJson('/api/finance/pixgo/settings', payload);
    showToast(getUiText().finance.saveToast, 'success');
    await loadFinance();
  } catch(e) {
    showToast((currentLang === 'en' ? 'Could not save integration: ' : 'Erro ao salvar integracao: ') + e.message, 'error');
  }
}

async function refreshAllFinancePayments() {
  try {
    const payload = chatId ? { chat_id: chatId } : {};
    const data = await postJson('/api/finance/pixgo/refresh-all', payload);
    const updated = Number(data.updated || 0);
    showToast(getUiText().finance.refreshManyToast(updated), 'success');
    await loadFinance();
  } catch(e) {
    showToast((currentLang === 'en' ? 'Could not refresh payments: ' : 'Erro ao atualizar pagamentos: ') + e.message, 'error');
  }
}

function financeInputValue(id) {
  const node = el(id);
  return node ? node.value.trim() : '';
}

function clearFinanceImport() {
  if (el('finance-import-file')) el('finance-import-file').value = '';
  if (el('finance-import-account')) el('finance-import-account').value = '';
  if (el('finance-import-text')) el('finance-import-text').value = '';
}

async function createFinancePayment() {
  if (!chatId) {
    showToast(getUiText().finance.selectWarning, 'warning');
    return;
  }
  try {
    const payload = {
      chat_id: chatId,
      amount: financeInputValue('finance-amount'),
      description: financeInputValue('finance-description'),
      customer_name: financeInputValue('finance-customer-name'),
      customer_cpf: financeInputValue('finance-customer-cpf'),
      customer_email: financeInputValue('finance-customer-email'),
      customer_phone: financeInputValue('finance-customer-phone'),
      customer_address: financeInputValue('finance-customer-address'),
    };
    const data = await postJson('/api/finance/pixgo/payment', payload);
    showToast(getUiText().finance.createToast, 'success');
    financeState.activePayment = data.payment || null;
    await loadFinance();
    ['finance-amount', 'finance-customer-name', 'finance-customer-cpf', 'finance-customer-email', 'finance-customer-phone', 'finance-customer-address'].forEach(function(id) {
      if (el(id)) el(id).value = '';
    });
  } catch(e) {
    showToast((currentLang === 'en' ? 'Could not create charge: ' : 'Erro ao criar cobranca: ') + e.message, 'error');
  }
}

async function importFinanceHistory() {
  const fileInput = el('finance-import-file');
  const textInput = el('finance-import-text');
  const accountInput = el('finance-import-account');
  const file = fileInput && fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
  const rawText = textInput ? textInput.value.trim() : '';
  const providerAccount = accountInput ? accountInput.value.trim() : '';

  if (!file && !rawText) {
    showToast(getUiText().finance.importEmpty, 'warning');
    return;
  }

  try {
    const form = new FormData();
    if (chatId) form.append('chat_id', String(chatId));
    if (providerAccount) form.append('provider_account', providerAccount);
    if (file) form.append('file', file);
    if (rawText) {
      form.append('raw_text', rawText);
      form.append('filename', file ? file.name : 'manual-import.json');
    }
    const data = await postForm('/api/finance/import', form);
    showToast(getUiText().finance.importToast(Number(data.imported || 0), Array.isArray(data.skipped) ? data.skipped.length : 0), 'success');
    if (Array.isArray(data.skipped) && data.skipped.length) {
      console.warn('Finance import skipped rows:', data.skipped);
    }
    clearFinanceImport();
    await loadFinance();
  } catch (e) {
    showToast((currentLang === 'en' ? 'Could not import history: ' : 'Erro ao importar historico: ') + e.message, 'error');
  }
}

async function lookupFinancePayment() {
  const paymentId = financeInputValue('finance-lookup-payment-id');
  const providerAccount = financeInputValue('finance-lookup-account');
  if (!paymentId) {
    showToast(currentLang === 'en' ? 'Enter the payment ID first.' : 'Informe o payment ID primeiro.', 'warning');
    return;
  }
  try {
    const data = await postJson('/api/finance/pixgo/payment-lookup', {
      payment_id: paymentId,
      provider_account: providerAccount,
    });
    showToast(getUiText().finance.lookupToast, 'success');
    financeState.activePayment = data.payment || null;
    await loadFinance();
  } catch (e) {
    showToast((currentLang === 'en' ? 'Could not load transaction: ' : 'Erro ao consultar transacao: ') + e.message, 'error');
  }
}

async function refreshFinancePayment(paymentId) {
  try {
    await postJson('/api/finance/pixgo/payment/' + encodeURIComponent(paymentId) + '/refresh', {});
    showToast(getUiText().finance.statusToast, 'success');
    await loadFinance();
  } catch(e) {
    showToast((currentLang === 'en' ? 'Could not refresh payment: ' : 'Erro ao consultar pagamento: ') + e.message, 'error');
  }
}

window.copyFinanceQrCode = function(value) {
  if (!value) {
    showToast(getUiText().finance.qrMissing, 'warning');
    return;
  }
  navigator.clipboard.writeText(value).then(function() {
    showToast(getUiText().finance.copyToast, 'success');
  }).catch(function() {
    showToast(getUiText().finance.copyError, 'error');
  });
};

window.openFinanceQrImage = function(url) {
  if (!url) {
    showToast(getUiText().finance.qrImageMissing, 'warning');
    return;
  }
  window.open(url, '_blank', 'noopener');
};

window.clearFinanceImport = clearFinanceImport;
window.importFinanceHistory = importFinanceHistory;
window.lookupFinancePayment = lookupFinancePayment;
window.applyFinanceAccountFilter = applyFinanceAccountFilter;

function renderMembersSummary(count) {
  const safe = count || {};
  el('m-total').textContent  = safe.total  || 0;
  el('m-admins').textContent = safe.admins || 0;
  el('m-common').textContent = (safe.total || 0) - (safe.admins || 0);
}

async function fetchMembersSnapshot() {
  const data = await api('/api/members/' + chatId);
  allMembers = data.members || [];
  renderMembersSummary(data.count);
  filterMembers();
  return data;
}

async function backgroundSyncMembers(force) {
  if (!chatId) return null;
  const cacheKey = String(chatId);
  const now = Date.now();
  if (!force && memberAutoSyncAt[cacheKey] && (now - memberAutoSyncAt[cacheKey]) < MEMBER_AUTO_SYNC_MS) {
    return null;
  }
  memberAutoSyncAt[cacheKey] = now;
  try {
    const result = await api('/api/members/' + chatId + '/sync', { method: 'POST' });
    if (result && result.ok && activeView === 'members' && String(chatId) === cacheKey) {
      await fetchMembersSnapshot();
    }
    if (!result || !result.ok) {
      memberAutoSyncAt[cacheKey] = now - MEMBER_AUTO_SYNC_MS + 10000;
    }
    return result;
  } catch(_) {
    memberAutoSyncAt[cacheKey] = now - MEMBER_AUTO_SYNC_MS + 10000;
    return null;
  }
}

async function loadMembers() {
  const text = getUiText();
  if (!chatId) {
    el('members-body').innerHTML = `<tr><td colspan="5" class="muted" style="padding:20px;text-align:center">${text.members.noGroup}</td></tr>`;
    el('m-total').textContent  = '-';
    el('m-admins').textContent = '-';
    el('m-common').textContent = '-';
    return;
  }
  await fetchMembersSnapshot();
  backgroundSyncMembers(false);
}

function renderMembersTable(members) {
  const text = getUiText();
  const tbody = el('members-body');
  const empty = el('members-empty');
  tbody.innerHTML = '';
  if (!members.length) {
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  members.forEach(function(m, i) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + (i + 1) + '</td>' +
      '<td>@' + (m.username || '-') + '</td>' +
      '<td>' + (m.full_name || '-') + '</td>' +
      '<td>' + (m.is_admin ? '<span style="color:var(--yellow);font-weight:600">' + text.members.admin + '</span>' : '<span class="muted">' + text.members.member + '</span>') + '</td>' +
      '<td class="muted small">' + (m.last_seen ? fmt(m.last_seen) : '-') + '</td>';
    tbody.appendChild(tr);
  });
}

window.filterMembers = function() {
  const q = (el('member-search').value || '').toLowerCase();
  const role = (el('member-role-filter') && el('member-role-filter').value) || 'all';
  if (!q && role === 'all') { renderMembersTable(allMembers); return; }
  renderMembersTable(allMembers.filter(function(m) {
    const matchesQuery =
      (m.username  || '').toLowerCase().includes(q) ||
      (m.full_name || '').toLowerCase().includes(q);
    const matchesRole =
      role === 'all' ||
      (role === 'admin' && m.is_admin) ||
      (role === 'member' && !m.is_admin);
    return matchesQuery && matchesRole;
  }));
};

window.syncMembers = async function() {
  const text = getUiText();
  if (!chatId) { showMsg('sync-msg', text.members.selectWarning, false); return; }
  showMsg('sync-msg', text.members.syncNow, true);
  try {
    const r = await backgroundSyncMembers(true) || { ok: false, msg: text.members.syncUnavailable };
    showMsg('sync-msg', r.msg, r.ok);
  } catch(e) { showMsg('sync-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false); }
};

window.syncFull = async function() {
  const text = getUiText();
  if (!chatId) { showMsg('sync-msg', text.members.selectWarning, false); return; }
  showMsg('sync-msg', text.members.syncAll, true);
  try {
    const r = await api('/api/members/' + chatId + '/sync-full', { method: 'POST' });
    showMsg('sync-msg', r.msg, r.ok);
    if (r.ok) {
      memberAutoSyncAt[String(chatId)] = Date.now();
      await loadMembers();
    }
  } catch(e) { showMsg('sync-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false); }
};

async function loadSettings() {
  const text = getUiText();
  const s = await api('/api/settings');
  el('inp-token').placeholder = s.token_set ? text.settings.tokenPlaceholderReady : text.settings.tokenPlaceholderNew;
  renderGroupsTable(s.groups || []);
  renderAppearanceControls();
  updateUserChrome();
}

function renderGroupsTable(groups) {
  const text = getUiText();
  const tbody = el('groups-body');
  tbody.innerHTML = '';
  if (!groups.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="padding:16px;text-align:center;color:#8b949e">${text.common.noGroups}</td></tr>`;
    return;
  }
  groups.forEach(function(g) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td><code>'+g.chat_id+'</code></td>' +
      '<td>'+(g.chat_title||'-')+'</td>' +
      '<td style="color:#8b949e;font-size:12px">'+(g.first_seen?fmt(g.first_seen.replace(' ','T')):'-')+'</td>' +
      '<td style="color:#8b949e;font-size:12px">'+(g.last_event?fmt(g.last_event.replace(' ','T')):'-')+'</td>' +
      '<td><button class="btn-del" onclick="removeGroup('+g.chat_id+')">' + text.common.remove + '</button></td>';
    tbody.appendChild(tr);
  });
}

window.toggleTokenVis = function() {
  const inp = el('inp-token');
  inp.type = inp.type === 'password' ? 'text' : 'password';
};

window.saveToken = async function() {
  const text = getUiText();
  const token = el('inp-token').value.trim();
  if (!token) { showMsg('token-msg', text.settings.tokenRequired, false); return; }
  try {
    const r = await api('/api/settings/token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:token})});
    showMsg('token-msg',r.msg,r.ok);
    if (r.ok) { el('inp-token').value=''; await checkBotStatus(); }
  } catch(e) { showMsg('token-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false); }
};

window.restartBot = async function() {
  try {
    const r = await api('/api/settings/bot/restart',{method:'POST'});
    showMsg('token-msg',r.msg,r.ok);
    await checkBotStatus();
  } catch(e) { showMsg('token-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false); }
};

window.stopBot = async function() {
  try {
    const r = await api('/api/settings/bot/stop',{method:'POST'});
    showMsg('token-msg',r.msg,r.ok);
    await checkBotStatus();
  } catch(e) { showMsg('token-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false); }
};

window.addGroup = async function() {
  const text = getUiText();
  const cid = el('inp-chatid').value.trim();
  const title = el('inp-title').value.trim();
  if (!cid) { showMsg('group-msg', text.settings.groupRequired, false); return; }
  try {
    const r = await api('/api/settings/groups/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:cid,title:title})});
    showMsg('group-msg',r.msg,r.ok);
    if (r.ok) { el('inp-chatid').value=''; el('inp-title').value=''; await loadGroups(); await loadSettings(); }
  } catch(e) { showMsg('group-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false); }
};

window.removeGroup = async function(cid) {
  if (!confirm(getUiText().settings.removeConfirm(cid))) return;
  try {
    await api('/api/settings/groups/'+cid,{method:'DELETE'});
    await loadGroups(); await loadSettings();
  } catch(e) { showToast((currentLang === 'en' ? 'Could not remove group: ' : 'Erro ao remover grupo: ') + e.message, 'error'); }
};

// â”€â”€ COFRE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
var vaultCatId  = null;
var vaultEditId = null;

function isVaultSensitiveLabel(label) {
  return /senha|password|token|secret|secreto|api|key|chave|webhook|pix|cpf|2fa/i.test(String(label || ''));
}

function maskVaultValue(value) {
  const raw = String(value || '');
  if (!raw) return 'â€¢â€¢â€¢â€¢â€¢â€¢';
  if (raw.length <= 4) return 'â€¢'.repeat(Math.max(4, raw.length));
  return raw.slice(0, 2) + 'â€¢'.repeat(Math.min(10, Math.max(4, raw.length - 4))) + raw.slice(-2);
}

function openVaultPasswordGenerator(targetInput) {
  _pwTargetField = targetInput || null;
  el('vault-pw-modal').style.display = 'flex';
  pwGenUpdate();
}

window.vaultCopyField = function(value, label, entryId) {
  if (entryId) {
    fetch('/api/vault/access_log', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ entry_id: entryId, action: `Copiou campo "${label}"` })
    }).catch(function(){});
  }
  navigator.clipboard.writeText(value).then(function() {
    showToast(getUiText().vault.copiedField(label), 'success');
  }).catch(function() {
    showToast(getUiText().vault.noCopyField, 'error');
  });
};

async function loadVault() {
  const text = getUiText();
  var cats = [];
  try { cats = await api('/api/vault/categories'); } catch(e) { return; }
  var ul = el('vault-cats');
  ul.innerHTML = '';
  if (el('vault-cat-meta') && !vaultCatId) {
    el('vault-cat-meta').textContent = text.vault.selectCategoryHint;
  }
  if (!cats.length) {
    ul.innerHTML = `<li class="muted" style="padding:12px">${text.vault.noCategories}</li>`;
    if (el('vault-cat-title')) el('vault-cat-title').textContent = text.vault.selectCategory;
    if (el('vault-cat-meta')) el('vault-cat-meta').textContent = text.vault.noCategories;
    return;
  }
  cats.forEach(function(c) {
    var li   = document.createElement('li');
    li.className = 'vault-cat-item' + (c.id === vaultCatId ? ' active' : '');
    var trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'vault-cat-trigger';
    trigger.onclick = (function(cid,cname){ return function(){ vaultSelectCat(cid,cname); }; })(c.id, c.name||'');
    var icon = document.createElement('span');
    icon.className = 'vault-cat-symbol';
    icon.textContent = c.icon || 'â€¢';
    var copy = document.createElement('span');
    copy.className = 'vault-cat-copy';
    var title = document.createElement('strong');
    title.textContent = c.name || '';
    var meta = document.createElement('small');
    meta.textContent = text.vault.meta;
    copy.appendChild(title);
    copy.appendChild(meta);
    trigger.appendChild(icon);
    trigger.appendChild(copy);
    var btn  = document.createElement('button');
    btn.className   = 'btn-icon-sm';
    btn.textContent = 'Ã—';
    btn.onclick = (function(cid){ return function(){ vaultDeleteCat(cid); }; })(c.id);
    btn.type = 'button';
    btn.title = text.vault.removeCategoryAria;
    btn.setAttribute('aria-label', text.vault.removeCategoryAria);
    btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    li.appendChild(trigger); li.appendChild(btn);
    ul.appendChild(li);
  });
}

window.vaultSelectCat = async function(id, name) {
  const text = getUiText();
  vaultCatId = id;
  el('vault-cat-title').textContent = name;
  el('btn-new-entry').style.display = '';
  await loadVault();
  var entries = [];
  try { entries = await api('/api/vault/entries/' + id); } catch(e) { return; }
  var box = el('vault-entries');
  box.innerHTML = '';
  if (el('vault-cat-meta')) {
    el('vault-cat-meta').textContent = currentLang === 'en'
      ? 'Loading protected entries...'
      : 'Carregando entradas protegidas...';
  }
  if (!entries.length) {
    box.innerHTML = `<p class="muted" style="padding:20px">${text.vault.noEntries}</p>`;
    if (el('vault-cat-meta')) {
      el('vault-cat-meta').textContent = currentLang === 'en'
        ? '0 protected entries'
        : '0 entradas protegidas';
    }
    return;
  }
  if (el('vault-cat-meta')) {
    el('vault-cat-meta').textContent = currentLang === 'en'
      ? `${entries.length} protected ${entries.length === 1 ? 'entry' : 'entries'}`
      : `${entries.length} ${entries.length === 1 ? 'entrada protegida' : 'entradas protegidas'}`;
  }
  entries.forEach(function(e) {
    var card   = document.createElement('div');
    card.className = 'vault-card';
    var hdr    = document.createElement('div');
    hdr.className  = 'vault-card-header';
    var headCopy = document.createElement('div');
    headCopy.className = 'vault-card-heading';
    var strong = document.createElement('strong');
    strong.textContent = e.title || '';
    var meta = document.createElement('small');
    meta.className = 'vault-card-meta';
    meta.textContent = currentLang === 'en'
      ? `${(e.fields || []).length} field${(e.fields || []).length === 1 ? '' : 's'}`
      : `${(e.fields || []).length} ${(e.fields || []).length === 1 ? 'campo' : 'campos'}`;
    var acts   = document.createElement('div');
    acts.className = 'vault-card-tools';
    var bEdit  = document.createElement('button');
    bEdit.className   = 'btn-icon-sm';
    bEdit.textContent = currentLang === 'en' ? 'Edit' : 'Editar';
    bEdit.onclick = (function(eid){ return function(){ vaultEditEntry(eid); }; })(e.id);
    var bDel   = document.createElement('button');
    bDel.className   = 'btn-icon-sm';
    bDel.textContent = getUiText().common.remove;
    bDel.onclick = (function(eid){ return function(){ vaultDeleteEntry(eid); }; })(e.id);
    acts.appendChild(bEdit); acts.appendChild(bDel);
    headCopy.appendChild(strong);
    headCopy.appendChild(meta);
    hdr.appendChild(headCopy);
    hdr.appendChild(acts);
    card.appendChild(hdr);
    (e.fields || []).forEach(function(f) {
      var row = document.createElement('div');
      row.className = 'vault-field';
      var lbl = document.createElement('span');
      lbl.className   = 'vault-field-label';
      lbl.textContent = f.label || '';
      var sensitive = Boolean(f.sensitive || isVaultSensitiveLabel(f.label));
      var content = document.createElement('div');
      content.className = 'vault-field-content';
      var val = document.createElement('span');
      val.className   = 'vault-field-value' + (sensitive ? ' is-sensitive' : '');
      val.textContent = sensitive ? maskVaultValue(f.value || '') : (f.value || '-');
      val.dataset.revealed = '0';
      var actions = document.createElement('div');
      actions.className = 'vault-field-actions';
      if (sensitive) {
        var toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'vault-field-action';
        toggle.textContent = text.vault.show;
        toggle.onclick = (function(target, value, button){
          return function() {
            var revealed = target.dataset.revealed === '1';
            target.dataset.revealed = revealed ? '0' : '1';
            target.textContent = revealed ? maskVaultValue(value) : (value || '-');
            button.textContent = revealed ? text.vault.show : text.vault.hide;
          };
        })(val, f.value || '', toggle);
        actions.appendChild(toggle);
      }
      var copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'vault-field-action primary';
      copyBtn.textContent = text.vault.copy;
      copyBtn.onclick = (function(v, label, entryId){ return function(){
        window.vaultCopyField(v, label, entryId);
      }; })(f.value || '', f.label || text.vault.fieldPlaceholder, e.id);
      actions.appendChild(copyBtn);
      content.appendChild(val);
      content.appendChild(actions);
      row.appendChild(lbl);
      row.appendChild(content);
      card.appendChild(row);
    });
    if (e.notes) {
      var p = document.createElement('p');
      p.className   = 'vault-notes';
      p.textContent = e.notes;
      card.appendChild(p);
    }
    box.appendChild(card);
  });
};

window.vaultNewCategory = function() {
  el('vc-name').value  = '';
  el('vc-icon').value  = '';
  el('vc-color').value = '#58a6ff';
  el('vault-cat-modal').style.display = 'flex';
};

window.vaultSaveCat = async function() {
  const text = getUiText();
  var name  = el('vc-name').value.trim();
  var icon  = el('vc-icon').value.trim() || '';
  var color = el('vc-color').value       || '#58a6ff';
  if (!name) { showToast(text.vault.categoryNameRequired, 'warning'); return; }
  await api('/api/vault/categories', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name:name, icon:icon, color:color})
  });
  el('vault-cat-modal').style.display = 'none';
  await loadVault();
};

window.vaultDeleteCat = async function(id) {
  if (!confirm(getUiText().vault.removeCategoryConfirm)) return;
  await api('/api/vault/categories/' + id, {method:'DELETE'});
  vaultCatId = null;
  el('vault-cat-title').textContent  = getUiText().vault.selectCategory;
  el('btn-new-entry').style.display  = 'none';
  el('vault-entries').innerHTML      = `<p class="muted" style="padding:20px">${getUiText().vault.selectCategory}</p>`;
  await loadVault();
};

window.vaultNewEntry = function() {
  vaultEditId = null;
  el('vault-modal-title').textContent = getUiText().vault.modal.newEntry;
  el('vm-title').value  = '';
  el('vm-notes').value  = '';
  el('vm-fields').innerHTML = '';
  vaultAddField();
  el('vault-modal').style.display = 'flex';
};

window.vaultEditEntry = async function(id) {
  var entries = [];
  try { entries = await api('/api/vault/entries/' + vaultCatId); } catch(e) { return; }
  var entry = null;
  for (var i=0; i<entries.length; i++) { if (entries[i].id === id) { entry = entries[i]; break; } }
  if (!entry) return;
  vaultEditId = id;
  el('vault-modal-title').textContent = getUiText().vault.modal.editEntry;
  el('vm-title').value = entry.title || '';
  el('vm-notes').value = entry.notes || '';
  el('vm-fields').innerHTML = '';
  (entry.fields || []).forEach(function(f) {
    vaultAddField(f.label, f.value, Boolean(f.sensitive || isVaultSensitiveLabel(f.label)));
  });
  el('vault-modal').style.display = 'flex';
};

window.vaultAddField = function(label, value, sensitive) {
  const text = getUiText();
  var div = document.createElement('div');
  div.className = 'vault-field-row';
  var lbl = document.createElement('input');
  lbl.type = 'text'; lbl.placeholder = text.vault.fieldPlaceholder; lbl.className = 'vf-label'; lbl.value = label || '';
  var wrap = document.createElement('div');
  wrap.className = 'vault-field-input-wrap';
  var val = document.createElement('input');
  val.type = sensitive ? 'password' : 'text'; val.placeholder = text.vault.valuePlaceholder; val.className = 'vf-value'; val.value = value || '';
  wrap.appendChild(val);
  var sensitiveWrap = document.createElement('label');
  sensitiveWrap.className = 'vault-field-flag';
  var sensitiveInput = document.createElement('input');
  sensitiveInput.type = 'checkbox';
  sensitiveInput.className = 'vf-sensitive';
  sensitiveInput.checked = Boolean(sensitive);
  sensitiveInput.onchange = function() {
    val.type = sensitiveInput.checked ? 'password' : 'text';
  };
  sensitiveWrap.appendChild(sensitiveInput);
  sensitiveWrap.appendChild(document.createTextNode(' ' + text.vault.sensitiveToggle));
  var toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'btn-icon-sm';
  toggle.textContent = text.vault.see;
  toggle.onclick = function() {
    val.type = val.type === 'password' ? 'text' : 'password';
    toggle.textContent = val.type === 'password' ? text.vault.see : text.vault.hide;
  };
  var pwBtn = document.createElement('button');
  pwBtn.type = 'button';
  pwBtn.className = 'btn-icon-sm';
  pwBtn.textContent = text.vault.generatePassword;
  pwBtn.onclick = function() {
    sensitiveInput.checked = true;
    val.type = 'password';
    openVaultPasswordGenerator(val);
  };
  var btn = document.createElement('button');
  btn.className = 'btn-icon-sm'; btn.textContent = 'Ã—';
  btn.onclick = function() { div.remove(); };
  btn.type = 'button';
  btn.setAttribute('aria-label', text.common.remove);
  btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  div.appendChild(lbl);
  div.appendChild(wrap);
  div.appendChild(sensitiveWrap);
  div.appendChild(toggle);
  div.appendChild(pwBtn);
  div.appendChild(btn);
  el('vm-fields').appendChild(div);
};

window.vaultCloseModal = function() {
  el('vault-modal').style.display = 'none';
};

window.vaultSaveEntry = async function() {
  const text = getUiText();
  var title = el('vm-title').value.trim();
  var notes = el('vm-notes').value.trim();
  if (!title) { showToast(text.vault.entryTitleRequired, 'warning'); return; }
  var fields = [];
  document.querySelectorAll('.vault-field-row').forEach(function(row) {
    var l = row.querySelector('.vf-label').value.trim();
    var v = row.querySelector('.vf-value').value.trim();
    var s = row.querySelector('.vf-sensitive');
    if (l) fields.push({label:l, value:v, sensitive:Boolean((s && s.checked) || isVaultSensitiveLabel(l))});
  });
  var body = {title:title, notes:notes, fields:fields, category_id:vaultCatId};
  if (vaultEditId) {
    await api('/api/vault/entries/'+vaultEditId, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  } else {
    await api('/api/vault/entries', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  }
  el('vault-modal').style.display = 'none';
  await vaultSelectCat(vaultCatId, el('vault-cat-title').textContent);
};

window.vaultDeleteEntry = async function(id) {
  if (!confirm(getUiText().vault.removeEntryConfirm)) return;
  await api('/api/vault/entries/' + id, {method:'DELETE'});
  await vaultSelectCat(vaultCatId, el('vault-cat-title').textContent);
};
// â”€â”€ FIM COFRE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const LOADERS = {
  home:     loadHome,
  vault:    loadVault,
  overview: loadOverview,
  charts:   loadCharts,
  events:   loadEvents,
  reports:  loadReports,
  goals:    loadGoals,
  pixel:    loadPixel,
  finance:  loadFinance,
  'name-search': loadNameSearch,
  members:  loadMembers,
  settings: loadSettings,
};

async function loadActiveView(forceOverviewSkeleton) {
  if (activeView === 'overview') return loadOverview(Boolean(forceOverviewSkeleton));
  if (LOADERS[activeView]) return LOADERS[activeView]();
  if (activeView === 'scheduler') return loadScheduler();
  if (activeView === 'logs') return loadLogs();
  return Promise.resolve();
}

async function refresh(force) {
  if (document.hidden && !force) return;
  if (refreshState.busy) {
    refreshState.queued = true;
    return;
  }
  refreshState.busy = true;
  try {
    await loadGroups(Boolean(force));
    syncExportButtons();
    await checkBotStatus(Boolean(force));
    if (activeView !== 'settings') await loadActiveView(false);
    el('last-refresh').textContent = (currentLang === 'en' ? 'Updated ' : 'Atualizado ') + new Date().toLocaleTimeString(getLocale());
  } catch(e) { console.error('refresh error:', e); }
  finally {
    refreshState.busy = false;
    if (refreshState.queued) {
      refreshState.queued = false;
      setTimeout(function() { refresh(); }, 250);
    }
  }
}

async function loadDashboard() {
  return refresh();
}

async function refreshAll() {
  return refresh();
}

el('group-select').addEventListener('change', async function(e) {
  await selectGroup(e.target.value ? e.target.value : null);
});

(async function() {
  await refresh();
  updateAutoRefreshUI();
  timer = setInterval(function() {
    if (!autoRefreshEnabled || document.hidden) return;
    refresh();
  }, GLOBAL_REFRESH_MS);
})();


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// BLOCO 3 â€” NOVAS FUNCIONALIDADES
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

// â”€â”€ i18n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const LANGS = {
  'pt': {
    home_title:'Inicio',
    nav_overview:'Overview', nav_charts:'GrÃ¡ficos', nav_events:'Eventos',
    nav_reports:'RelatÃ³rios', nav_members:'Membros', nav_vault:'Cofre',
    nav_goals:'Metas', nav_pixel:'PIXEL', nav_finance:'Financeiro', nav_name_search:'Consultas API', nav_settings:'ConfiguraÃ§Ãµes', nav_scheduler:'Agendador', nav_logs:'Logs',
    scheduler_title:'Agendador de Mensagens', sched_queue:'Fila de Mensagens',
    sched_empty:'Nenhuma mensagem agendada.',
    btn_schedule:'Agendar', btn_clear_logs:'Limpar',
    col_message:'Mensagem', col_date:'Data/Hora', col_status:'Status', col_action:'AÃ§Ã£o',
    logs_title:'Log do Bot em Tempo Real', logs_empty:'Aguardando logs do bot...',
    overview_title:'Overview', charts_title:'GrÃ¡ficos', events_title:'Eventos',
    reports_title:'RelatÃ³rios', goals_title:'Metas', pixel_title:'PIXEL', finance_title:'Financeiro', 'name-search_title':'Consultas API', members_title:'Membros', vault_title:'Cofre',
    settings_title:'ConfiguraÃ§Ãµes', scheduler_page:'Agendador', logs_page:'Logs',
  },
  'en': {
    home_title:'Home',
    nav_overview:'Overview', nav_charts:'Charts', nav_events:'Events',
    nav_reports:'Reports', nav_members:'Members', nav_vault:'Vault',
    nav_goals:'Goals', nav_pixel:'PIXEL', nav_finance:'Finance', nav_name_search:'API lookups', nav_settings:'Settings', nav_scheduler:'Scheduler', nav_logs:'Logs',
    scheduler_title:'Message Scheduler', sched_queue:'Message Queue',
    sched_empty:'No scheduled messages.',
    btn_schedule:'Schedule', btn_clear_logs:'Clear',
    col_message:'Message', col_date:'Date/Time', col_status:'Status', col_action:'Action',
    logs_title:'Bot Log (Live)', logs_empty:'Waiting for bot logs...',
    overview_title:'Overview', charts_title:'Charts', events_title:'Events',
    reports_title:'Reports', goals_title:'Goals', pixel_title:'PIXEL', finance_title:'Finance', 'name-search_title':'API lookups', members_title:'Members', vault_title:'Vault',
    settings_title:'Settings', scheduler_page:'Scheduler', logs_page:'Logs',
  }
};



function applyLang() {
  const t = LANGS[currentLang];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
  });
  syncViewChipTitles();
  const lbl = document.getElementById('lang-label');
  if (lbl) lbl.textContent = currentLang === 'pt' ? 'PT' : 'EN';
  updatePageTitle(activeView);
}

function toggleLang() {
  currentLang = currentLang === 'pt' ? 'en' : 'pt';
  localStorage.setItem('lang', currentLang);
  applyLang();
  showToast(currentLang === 'pt' ? 'Idioma: PortuguÃªs' : 'Language: English', 'info');
}

// â”€â”€ Tema claro/escuro â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


function updateAutoRefreshUI() {
  const label = document.getElementById('autorefresh-label');
  const btn = document.getElementById('autorefresh-toggle');
  if (label) label.textContent = autoRefreshEnabled ? 'Auto' : 'Manual';
  if (btn) btn.classList.toggle('is-off', !autoRefreshEnabled);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (document.body) document.body.setAttribute('data-theme', theme);
  const dark  = document.getElementById('theme-icon-dark');
  const light = document.getElementById('theme-icon-light');
  if (dark)  dark.style.display  = theme === 'dark'  ? 'block' : 'none';
  if (light) light.style.display = theme === 'light' ? 'block' : 'none';
  localStorage.setItem('theme', theme);
  currentTheme = theme;
}

function toggleTheme() {
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  showToast(currentTheme === 'dark' ? 'â˜€ï¸ Tema claro ativado' : 'ðŸŒ™ Tema escuro ativado', 'info');
}

// â”€â”€ Toast â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function reorderViewCollections() {
  const railTrack = el('view-rail-track');
  if (railTrack) {
    VIEW_ORDER.forEach(function(view) {
      const chip = document.querySelector(`.view-chip[data-view="${view}"]`);
      if (chip) railTrack.appendChild(chip);
    });
  }
  const launchGrid = document.querySelector('.launch-grid');
  if (launchGrid) {
    LAUNCH_ORDER.forEach(function(view) {
      const card = document.querySelector(`.launch-card[data-view="${view}"]`);
      if (card) launchGrid.appendChild(card);
    });
  }
}

function renderLaunchCards() {
  const copy = getUiText();
  document.querySelectorAll('.launch-card[data-view]').forEach(function(node) {
    const content = copy.launch[node.dataset.view];
    if (!content) return;
    setText(node.querySelector('.launch-card-kicker'), content.kicker);
    setText(node.querySelector('strong'), content.title);
    setText(node.querySelector('p'), content.desc);
    node.setAttribute('title', content.title);
    node.setAttribute('aria-label', content.title);
  });
}

function localizeStaticSections() {
  const text = getUiText();
  document.documentElement.lang = currentLang === 'en' ? 'en' : 'pt-BR';
  setText('.logo-text', text.notifications.title);
  setText('.sidebar-section-title', text.notifications.title);
  setText('.sidebar-clear-btn', text.common.clear);
  const drawerClose = el('sidebar-toggle');
  if (drawerClose) {
    drawerClose.title = text.topbar.closeNotifications;
    drawerClose.setAttribute('aria-label', text.topbar.closeNotifications);
  }
  const langBtn = el('lang-toggle');
  if (langBtn) {
    langBtn.title = text.topbar.languageTitle;
    langBtn.setAttribute('aria-label', text.topbar.languageTitle);
  }
  const themeBtn = el('theme-toggle');
  if (themeBtn) {
    themeBtn.title = text.topbar.themeTitle;
    themeBtn.setAttribute('aria-label', text.topbar.themeTitle);
  }
  const refreshBtn = el('topbar-refresh-btn');
  if (refreshBtn) {
    refreshBtn.title = text.topbar.refreshTitle;
    refreshBtn.setAttribute('aria-label', text.topbar.refreshTitle);
    setButtonLabel(refreshBtn, text.topbar.refresh);
  }
  document.querySelectorAll('[data-export-action="csv"]').forEach(function(btn) {
    btn.title = text.topbar.exportCsvTitle;
    btn.setAttribute('aria-label', text.topbar.exportCsvTitle);
  });
  document.querySelectorAll('[data-export-action="pdf"]').forEach(function(btn) {
    btn.title = text.topbar.exportPdfTitle;
    btn.setAttribute('aria-label', text.topbar.exportPdfTitle);
  });
  const notifyBtn = el('notifications-toggle');
  if (notifyBtn) {
    notifyBtn.title = text.topbar.notificationsTitle;
    notifyBtn.setAttribute('aria-label', text.topbar.notificationsTitle);
  }
  setText('.view-rail-label', text.home.railLabel);
  setText('#group-context-label', text.common.activeGroup);
  setText('#home-kicker', text.home.kicker);
  setText('#home-title', text.home.title);
  setText('#home-copy', text.home.copy);
  setText('#home-group-label', text.home.groupLabel);
  setText('#home-groups-label', text.home.groupsLabel);
  setText('#home-events-label', text.home.eventsLabel);
  setText('#home-members-label', text.home.membersLabel);
  setText('#home-finance-total-label', text.home.financeTotalLabel);
  setText('#home-finance-24h-label', text.home.finance24hLabel);
  setText('#home-finance-approved-24h-label', text.home.financeApproved24hLabel);
  setText('#home-finance-week-label', text.home.financeWeekLabel);
  setText('#home-transactions-header', text.home.transactionsHeader);
  setText('#home-transactions-empty', text.home.transactionsEmpty);

  const chartTitles = document.querySelectorAll('#view-charts .chart-title');
  text.charts.titles.forEach(function(title, idx) {
    setText(chartTitles[idx], title);
  });

  setText('#view-events .table-title > span', text.events.title);
  setPlaceholder('#event-search', text.events.searchPlaceholder);
  const clearEvent = el('event-search-clear');
  if (clearEvent) clearEvent.setAttribute('aria-label', text.events.clearSearchAria);
  const eventFilter = el('event-type-filter');
  if (eventFilter) {
    Array.from(eventFilter.options).forEach(function(option) {
      if (option.value === 'all') option.textContent = text.events.filterAll;
      if (option.value === 'join') option.textContent = text.events.filterJoin;
      if (option.value === 'leave') option.textContent = text.events.filterLeave;
    });
  }
  document.querySelectorAll('#view-events thead th').forEach(function(th, idx) {
    if (typeof text.events.headers[idx] !== 'undefined') th.textContent = text.events.headers[idx];
  });

  const reportTitles = document.querySelectorAll('#view-reports .table-title');
  setText(reportTitles[0], text.reports.titles[0]);
  setText(reportTitles[1], text.reports.titles[1]);
  const reportTables = document.querySelectorAll('#view-reports .table-wrap');
  if (reportTables[0]) {
    reportTables[0].querySelectorAll('thead th').forEach(function(th, idx) {
      if (typeof text.reports.headersWeekly[idx] !== 'undefined') th.textContent = text.reports.headersWeekly[idx];
    });
  }
  if (reportTables[1]) {
    reportTables[1].querySelectorAll('thead th').forEach(function(th, idx) {
      if (typeof text.reports.headersMonthly[idx] !== 'undefined') th.textContent = text.reports.headersMonthly[idx];
    });
  }
  setText('#view-reports .panel-header', text.reports.anomaliesTitle);
  setText('#view-goals .goals-kicker', currentLang === 'en' ? 'Group planning' : 'Planejamento do grupo');
  setText('#goals-empty strong', text.goals.emptyTitle);
  setText('#goals-empty p', text.goals.emptyCopy);

  const pixelMetrics = document.querySelectorAll('#view-pixel .pixel-metric-card span');
  text.pixel.metrics.forEach(function(label, idx) { setText(pixelMetrics[idx], label); });
  setText('#pixel-kicker', text.pixel.kicker);
  setText('#pixel-title', text.pixel.title);
  setText('#pixel-copy', text.pixel.copy);
  setText('#pixel-status-kicker', text.pixel.statusKicker);
  setText('#pixel-credentials-title', text.pixel.credentialsTitle);
  setText('#pixel-roadmap-title', text.pixel.roadmapTitle);
  setText('#pixel-label-pixel-id', text.pixel.fields.pixelId);
  setText('#pixel-label-ad-account-id', text.pixel.fields.adAccountId);
  setText('#pixel-label-access-token', text.pixel.fields.accessToken);
  setText('#pixel-label-dataset-id', text.pixel.fields.datasetId);
  setText('#pixel-label-test-event-code', text.pixel.fields.testEventCode);
  setPlaceholder('#pixel-id', text.pixel.placeholders.pixelId);
  setPlaceholder('#pixel-ad-account-id', text.pixel.placeholders.adAccountId);
  setPlaceholder('#pixel-access-token', text.pixel.placeholders.accessToken);
  setPlaceholder('#pixel-dataset-id', text.pixel.placeholders.datasetId);
  setPlaceholder('#pixel-test-event-code', text.pixel.placeholders.testEventCode);
  setText('#pixel-browser-title', text.pixel.browserTitle);
  setText('#pixel-browser-copy', text.pixel.browserCopy);
  setText('#pixel-capi-title', text.pixel.capiTitle);
  setText('#pixel-capi-copy', text.pixel.capiCopy);
  setText('#pixel-insights-title', text.pixel.insightsTitle);
  setText('#pixel-insights-copy', text.pixel.insightsCopy);
  setText('#pixel-next-step-label', text.pixel.nextStepLabel);
  setText('#pixel-summary-table-title', text.pixel.summaryTitle);
  const pixelSummaryLabels = text.pixel.summaryLabels || [];
  setText('#pixel-summary-pixel-id-label', pixelSummaryLabels[0]);
  setText('#pixel-summary-ad-account-label', pixelSummaryLabels[1]);
  setText('#pixel-summary-dataset-label', pixelSummaryLabels[2]);
  setText('#pixel-summary-token-label', pixelSummaryLabels[3]);
  const pixelButtons = document.querySelectorAll('#view-pixel .goals-form-actions button');
  setButtonLabel(pixelButtons[0], text.pixel.buttons.save);
  setButtonLabel(pixelButtons[1], text.pixel.buttons.refresh);

  const financeMetrics = document.querySelectorAll('#view-finance .finance-metric-card span');
  text.finance.metrics.forEach(function(label, idx) { setText(financeMetrics[idx], label); });
  setText('#finance-account-filter-label', text.finance.accountFilterLabel);
  setText('#view-finance .finance-status-kicker', text.finance.gatewayKicker);
  setText('#view-finance .finance-status-note span', text.finance.suggestedWebhook);
  setText('#view-finance .finance-status-actions .btn-secondary', text.finance.refreshStatus);
  const financePanels = document.querySelectorAll('#view-finance .finance-layout .panel-header');
  setText(financePanels[0], text.finance.newCharge);
  setText(financePanels[1], text.finance.integrationTitle);
  setText(financePanels[2], text.finance.importTitle);
  setText(financePanels[3], text.finance.lookupTitle);
  setText(document.querySelector('#view-finance .finance-layout--secondary .panel-header'), text.finance.activeChargeTitle);
  setText(document.querySelector('#view-finance .finance-table-wrap .table-title'), text.finance.historyTitle);
  document.querySelectorAll('#view-finance .finance-table-wrap thead th').forEach(function(th, idx) {
    if (typeof text.finance.historyHeaders[idx] !== 'undefined') th.textContent = text.finance.historyHeaders[idx];
  });
  const financeLabels = document.querySelectorAll('#view-finance .finance-form-grid > label > span');
  const financeLabelValues = [
    text.finance.fields.amount,
    text.finance.fields.description,
    text.finance.fields.customerName,
    text.finance.fields.cpf,
    text.finance.fields.email,
    text.finance.fields.phone,
    text.finance.fields.address,
    text.finance.fields.apiKey,
    text.finance.fields.webhookPublic,
    text.finance.fields.webhookSecret,
    text.finance.fields.defaultDescription,
    text.finance.fields.importFile,
    text.finance.fields.importAccount,
    text.finance.fields.importText,
    text.finance.fields.lookupPaymentId,
    text.finance.fields.lookupAccount
  ];
  financeLabelValues.forEach(function(value, idx) { setText(financeLabels[idx], value); });
  setPlaceholder('#finance-amount', text.finance.placeholders.amount);
  setPlaceholder('#finance-description', text.finance.placeholders.description);
  setPlaceholder('#finance-customer-name', text.finance.placeholders.customerName);
  setPlaceholder('#finance-customer-cpf', text.finance.placeholders.cpf);
  setPlaceholder('#finance-customer-email', text.finance.placeholders.email);
  setPlaceholder('#finance-customer-phone', text.finance.placeholders.phone);
  setPlaceholder('#finance-customer-address', text.finance.placeholders.address);
  setPlaceholder('#pixgo-api-key', text.finance.placeholders.apiKey);
  setPlaceholder('#pixgo-webhook-url', text.finance.placeholders.webhookPublic);
  setPlaceholder('#pixgo-webhook-secret', text.finance.placeholders.webhookSecret);
  setPlaceholder('#pixgo-default-description', text.finance.placeholders.defaultDescription);
  setPlaceholder('#finance-import-account', text.finance.placeholders.importAccount);
  setPlaceholder('#finance-import-text', text.finance.placeholders.importText);
  setPlaceholder('#finance-lookup-payment-id', text.finance.placeholders.lookupPaymentId);
  setPlaceholder('#finance-lookup-account', text.finance.placeholders.lookupAccount);
  fillFinanceAccountFilter();
  const financeNotes = document.querySelectorAll('#view-finance .goals-form-note');
  setText(financeNotes[0], text.finance.notes.payments);
  setText(financeNotes[1], text.finance.notes.webhook);
  setText(financeNotes[2], text.finance.notes.import);
  setText(financeNotes[3], text.finance.notes.lookup);
  const financeButtons = document.querySelectorAll('#view-finance .goals-form-actions button');
  setButtonLabel(financeButtons[0], text.finance.buttons.refreshPanel);
  setButtonLabel(financeButtons[1], text.finance.buttons.createCharge);
  setButtonLabel(financeButtons[2], text.finance.buttons.saveIntegration);
  setButtonLabel(financeButtons[3], text.finance.buttons.clearImport);
  setButtonLabel(financeButtons[4], text.finance.buttons.importHistory);
  setButtonLabel(financeButtons[5], text.finance.buttons.lookupPayment);

  setText('#name-search-kicker', text.nameSearch.kicker);
  setText('#name-search-title', text.nameSearch.title);
  setText('#name-search-copy', text.nameSearch.copy);
  setText('#name-search-side-label', text.nameSearch.sideLabel);
  setText('#name-search-side-title', text.nameSearch.sideTitle);
  setText('#name-search-side-copy', text.nameSearch.sideCopy);
  setText('#name-search-total-label', text.nameSearch.stats.total);
  setText('#name-search-records-label', text.nameSearch.stats.records);
  setText('#name-search-json-size-label', text.nameSearch.stats.jsonSize);
  setText('#name-search-table-title', text.nameSearch.tableTitle);
  setText('#name-search-structured-title', text.nameSearch.structuredTitle);
  setText('#name-search-json-title', text.nameSearch.rawTitle);
  setText('#name-search-json-summary', text.nameSearch.rawSummary);
  const nameSearchTypeSelect = el('name-search-type');
  if (nameSearchTypeSelect && text.nameSearch.searchTypes) {
    Array.from(nameSearchTypeSelect.options).forEach(function(option) {
      if (typeof text.nameSearch.searchTypes[option.value] !== 'undefined') {
        option.textContent = text.nameSearch.searchTypes[option.value];
      }
    });
  }
  if (!nameSearchState.query && (nameSearchState.raw === null || typeof nameSearchState.raw === 'undefined')) {
    setText('#name-search-json', text.nameSearch.rawIdle);
    setText('#name-search-structured', text.nameSearch.rawIdle);
  }
  updateNameSearchTypeUI();
  setButtonLabel('#name-search-btn', text.nameSearch.buttons.search);
  setButtonLabel('#name-search-clear-btn', text.nameSearch.buttons.clear);
  document.querySelectorAll('#view-name-search thead th').forEach(function(th, idx) {
    if (typeof text.nameSearch.headers[idx] !== 'undefined') th.textContent = text.nameSearch.headers[idx];
  });
  renderNameSearchRows(nameSearchState);
  renderNameSearchStructuredPayload(nameSearchState);
  renderNameSearchRawPayload(nameSearchState);

  const memberLabels = document.querySelectorAll('#view-members .stat-item .lbl');
  text.members.stats.forEach(function(label, idx) { setText(memberLabels[idx], label); });
  setPlaceholder('#member-search', text.members.searchPlaceholder);
  const memberFilter = el('member-role-filter');
  if (memberFilter) {
    Array.from(memberFilter.options).forEach(function(option) {
      if (option.value === 'all') option.textContent = text.members.filters.all;
      if (option.value === 'admin') option.textContent = text.members.filters.admin;
      if (option.value === 'member') option.textContent = text.members.filters.member;
    });
  }
  const memberButtons = document.querySelectorAll('#view-members .members-actions > button');
  setButtonLabel(memberButtons[0], text.members.buttons.sync);
  setButtonLabel(memberButtons[1], text.members.buttons.syncFull);
  document.querySelectorAll('#view-members thead th').forEach(function(th, idx) {
    if (typeof text.members.headers[idx] !== 'undefined') th.textContent = text.members.headers[idx];
  });
  setText('#members-empty', text.members.empty);

  setText('#view-vault .vault-kicker', text.vault.heroKicker);
  setText('#view-vault .vault-hero-main h2', text.vault.heroTitle);
  setText('#view-vault .vault-hero-main p', text.vault.heroCopy);
  setText('#view-vault .vault-main-kicker', text.vault.heroKicker);
  const vaultPills = document.querySelectorAll('#view-vault .vault-hero-pill');
  text.vault.pills.forEach(function(pair, idx) {
    if (!vaultPills[idx]) return;
    setText(vaultPills[idx].querySelector('span'), pair[0]);
    setText(vaultPills[idx].querySelector('strong'), pair[1]);
  });
  setText('#view-vault .vault-sidebar-header span', text.vault.categories);
  const vaultAddCategory = document.querySelector('#view-vault .vault-sidebar-header .btn-icon');
  if (vaultAddCategory) vaultAddCategory.setAttribute('title', text.vault.newCategory);
  setPlaceholder('#vault-global-search', text.vault.searchPlaceholder);
  const vaultToolbarButtons = document.querySelectorAll('#view-vault .vault-toolbar .btn-secondary');
  setButtonLabel(vaultToolbarButtons[0], text.vault.generatePassword);
  setButtonLabel(vaultToolbarButtons[1], text.vault.history);
  setButtonLabel('#btn-new-entry', text.vault.newEntry);
  if (!vaultCatId) setText('#vault-cat-title', text.vault.selectCategory);
  if (!vaultCatId) {
    const muted = document.querySelector('#vault-entries .muted');
    if (muted) muted.textContent = text.vault.selectCategoryHint;
  }
  const vaultModalLabels = document.querySelectorAll('#vault-modal .vault-modal-body > label');
  setText(vaultModalLabels[0], text.vault.modal.titleLabel);
  setText(vaultModalLabels[1], text.vault.modal.fieldsLabel);
  setText(vaultModalLabels[2], text.vault.modal.notesLabel);
  setPlaceholder('#vm-title', text.vault.modal.titlePlaceholder);
  setPlaceholder('#vm-notes', text.vault.modal.notesPlaceholder);
  const vaultActionButtons = document.querySelectorAll('#vault-modal .vault-modal-actions button');
  setButtonLabel(vaultActionButtons[0], text.vault.modal.addField);
  setButtonLabel(vaultActionButtons[1], text.vault.modal.sensitiveField);
  setButtonLabel(vaultActionButtons[2], text.vault.generatePassword);
  const vaultModalFooter = document.querySelectorAll('#vault-modal .vault-modal-footer button');
  setButtonLabel(vaultModalFooter[0], text.common.cancel);
  setButtonLabel(vaultModalFooter[1], text.common.save);
  setText('#vault-pw-modal .vault-modal-header span', text.vault.passwordModal.title);
  const pwLabels = document.querySelectorAll('#vault-pw-modal .vault-modal-body > label');
  setText(pwLabels[0], text.vault.passwordModal.length);
  setText(pwLabels[1], text.vault.passwordModal.generated);
  const pwCheckboxLabels = document.querySelectorAll('#vault-pw-modal .vault-modal-body > div:nth-of-type(2) label');
  setInlineControlLabel(pwCheckboxLabels[0], text.vault.passwordModal.uppercase);
  setInlineControlLabel(pwCheckboxLabels[1], text.vault.passwordModal.numbers);
  setInlineControlLabel(pwCheckboxLabels[2], text.vault.passwordModal.symbols);
  const pwFooter = document.querySelectorAll('#vault-pw-modal .vault-modal-footer button');
  setButtonLabel(pwFooter[0], text.vault.passwordModal.close);
  setButtonLabel(pwFooter[1], text.vault.passwordModal.useInField);
  setText('#vault-history-modal .vault-modal-header span', text.vault.historyTitle);
  setText('#vault-history-modal .vault-modal-footer button', text.common.close);
  setText('#vault-cat-modal .vault-modal-header span', text.vault.categoryModal.title);
  const catModalLabels = document.querySelectorAll('#vault-cat-modal .vault-modal-body > label');
  setText(catModalLabels[0], text.vault.categoryModal.name);
  setText(catModalLabels[1], text.vault.categoryModal.icon);
  setText(catModalLabels[2], text.vault.categoryModal.color);
  setPlaceholder('#vc-name', text.vault.categoryModal.namePlaceholder);
  const catFooter = document.querySelectorAll('#vault-cat-modal .vault-modal-footer button');
  setButtonLabel(catFooter[0], text.common.cancel);
  setButtonLabel(catFooter[1], text.vault.categoryModal.create);
  setPlaceholder('#sched-msg', text.scheduler.placeholder);
  setText('#sched-datetime-label', text.scheduler.datetimeLabel);

  const settingSections = document.querySelectorAll('#view-settings .settings-section');
  setText('#view-settings .settings-kicker', text.settings.heroKicker);
  setText('#view-settings .settings-hero-copy h2', text.settings.heroTitle);
  setText('#view-settings .settings-hero-copy p', text.settings.heroCopy);
  setText('#view-settings .settings-hero-label', text.settings.heroSideLabel);
  setText('#view-settings .settings-hero-side strong', text.settings.heroSideTitle);
  setText('#view-settings .settings-hero-side p', text.settings.heroSideCopy);
  document.querySelectorAll('#view-settings .settings-category-chip').forEach(function(chip) {
    const category = chip.dataset.settingsCategory;
    if (category && text.settings.categories && text.settings.categories[category]) {
      chip.textContent = text.settings.categories[category];
    }
  });
  if (settingSections[0]) {
    setText(settingSections[0].querySelector('.settings-header span'), text.settings.appearanceTitle);
    setText(settingSections[0].querySelector('.settings-copy'), text.settings.appearanceCopy);
    setText('#appearance-profile-label', text.settings.profileLabel);
    setText('#appearance-mode-label', text.settings.modeLabel);
    setText('#appearance-preset-label', text.settings.presetLabel);
    setText('#profile-avatar-url-label', text.settings.profilePhoto);
    setText('#profile-title-label', text.settings.profileTitle);
    setText('#profile-bio-label', text.settings.profileBio);
    setText('#profile-motion-label', text.settings.motionLabel);
    setText('#appearance-mode-light', text.settings.light);
    setText('#appearance-mode-dark', text.settings.dark);
    const motion = el('profile-motion-level');
    if (motion && motion.options.length >= 3) {
      motion.options[0].textContent = text.settings.motionCalm;
      motion.options[1].textContent = text.settings.motionStandard;
      motion.options[2].textContent = text.settings.motionExpressive;
    }
    const profileButtons = settingSections[0].querySelectorAll('.appearance-block--profile .goals-form-actions button');
    setButtonLabel(profileButtons[0], text.settings.profilePreview);
    setButtonLabel(profileButtons[1], text.settings.profileSave);
  }
  if (settingSections[1]) {
    setText(settingSections[1].querySelector('.settings-header span'), text.settings.tokenTitle);
    const tokenButtons = settingSections[1].querySelectorAll('button');
    setButtonLabel(tokenButtons[1], text.settings.buttons.save);
    setButtonLabel(tokenButtons[2], text.settings.buttons.start);
    setButtonLabel(tokenButtons[3], text.settings.buttons.stop);
  }
  if (settingSections[2]) {
    setText(settingSections[2].querySelector('.settings-header span'), text.settings.groupsTitle);
    setPlaceholder('#inp-title', text.settings.groupNamePlaceholder);
    setButtonLabel(settingSections[2].querySelector('.btn-primary'), text.settings.buttons.add);
    settingSections[2].querySelectorAll('th').forEach(function(th, idx) {
      if (typeof text.settings.headers[idx] !== 'undefined') th.textContent = text.settings.headers[idx];
    });
  }
}

function renderAppearanceControls() {
  const lightBtn = el('appearance-mode-light');
  const darkBtn = el('appearance-mode-dark');
  if (lightBtn) lightBtn.classList.toggle('is-active', currentTheme === 'light');
  if (darkBtn) darkBtn.classList.toggle('is-active', currentTheme === 'dark');
  if (el('profile-motion-level') && currentUserProfile.preferences) {
    el('profile-motion-level').value = currentUserProfile.preferences.motion_level || 'standard';
  }
  const grid = el('appearance-preset-grid');
  if (!grid) return;
  grid.innerHTML = Object.entries(THEME_PRESETS).map(function(entry) {
    const key = entry[0];
    const preset = entry[1];
    const name = preset.name[currentLang] || preset.name.pt;
    const desc = preset.desc[currentLang] || preset.desc.pt;
    return `
      <button type="button" class="appearance-preset-card${key === currentThemePreset ? ' is-active' : ''}" onclick="setThemePreset('${key}')">
        <span class="appearance-preset-preview" style="background:${preset.preview}"></span>
        <span class="appearance-preset-meta">
          <strong>${name}</strong>
          <small>${desc}</small>
        </span>
      </button>
    `;
  }).join('');
}

function applyThemePreset(presetKey) {
  const preset = THEME_PRESETS[presetKey] || THEME_PRESETS.corporate;
  const layout = THEME_LAYOUT_SIGNATURES[presetKey] || THEME_LAYOUT_SIGNATURES.corporate;
  const visual = THEME_VISUAL_SIGNATURES[presetKey] || THEME_VISUAL_SIGNATURES.corporate;
  const root = document.documentElement;
  const body = document.body;
  root.dataset.themePreset = presetKey;
  if (body) body.dataset.themePreset = presetKey;
  root.style.setProperty('--theme-accent', preset.accent);
  root.style.setProperty('--theme-accent-2', preset.accent2);
  root.style.setProperty('--theme-accent-soft', preset.soft);
  root.style.setProperty('--theme-accent-strong', preset.strong);
  root.style.setProperty('--theme-accent-glow', preset.glow);
  root.style.setProperty('--theme-hero-a', preset.heroA);
  root.style.setProperty('--theme-hero-b', preset.heroB);
  root.style.setProperty('--theme-icon-bg', preset.iconBg);
  root.style.setProperty('--theme-icon-color', preset.iconColor);
  root.style.setProperty('--theme-shell-start', preset.shellStart || '#f7fbff');
  root.style.setProperty('--theme-shell-end', preset.shellEnd || '#e6eef8');
  root.style.setProperty('--theme-orb-a', preset.orbA || preset.heroA);
  root.style.setProperty('--theme-orb-b', preset.orbB || preset.heroB);
  root.style.setProperty('--theme-surface-a', preset.surfaceA || 'rgba(255,255,255,.94)');
  root.style.setProperty('--theme-surface-b', preset.surfaceB || 'rgba(241,246,252,.94)');
  root.style.setProperty('--theme-card-shadow', preset.cardShadow || preset.glow);
  root.style.setProperty('--theme-ui-font', layout.uiFont);
  root.style.setProperty('--theme-display-font', layout.displayFont);
  root.style.setProperty('--theme-shell-pad', layout.shellPad);
  root.style.setProperty('--theme-panel-radius', layout.panelRadius);
  root.style.setProperty('--theme-card-radius', layout.cardRadius);
  root.style.setProperty('--theme-chip-radius', layout.chipRadius);
  root.style.setProperty('--theme-toolbar-radius', layout.toolbarRadius);
  root.style.setProperty('--theme-panel-padding', layout.panelPadding);
  root.style.setProperty('--theme-card-padding', layout.cardPadding);
  root.style.setProperty('--theme-hero-gap', layout.heroGap);
  root.style.setProperty('--theme-content-gap', layout.contentGap);
  root.style.setProperty('--theme-home-main', layout.homeMain);
  root.style.setProperty('--theme-home-side', layout.homeSide);
  root.style.setProperty('--theme-meta-min', layout.metaMin);
  root.style.setProperty('--theme-launch-min', layout.launchMin);
  root.style.setProperty('--theme-card-min-height', layout.cardMinHeight);
  root.style.setProperty('--theme-hero-title-size', layout.heroTitleSize);
  root.style.setProperty('--theme-body-top', layout.bodyTop);
  root.style.setProperty('--theme-body-bottom', layout.bodyBottom);
  root.style.setProperty('--theme-ambient-glow', layout.ambientGlow);
  root.style.setProperty('--theme-ambient-opacity', layout.ambientOpacity);
  root.style.setProperty('--theme-toolbar-surface', layout.toolbarSurface);
  root.style.setProperty('--theme-toolbar-border', layout.toolbarBorder);
  root.style.setProperty('--theme-panel-border', layout.panelBorder);
  root.style.setProperty('--theme-hero-surface', layout.heroSurface);
  root.style.setProperty('--theme-panel-surface', layout.panelSurface);
  root.style.setProperty('--theme-card-surface', layout.cardSurface);
  root.style.setProperty('--theme-card-shadow-soft', layout.cardShadowSoft);
  root.style.setProperty('--theme-panel-shadow-soft', layout.panelShadowSoft);
  root.style.setProperty('--theme-signature-body-dark', visual.bodyDark);
  root.style.setProperty('--theme-signature-body-light', visual.bodyLight);
  root.style.setProperty('--theme-signature-grid', visual.grid);
  root.style.setProperty('--theme-signature-grid-size', visual.gridSize);
  root.style.setProperty('--theme-signature-grid-opacity', visual.gridOpacity);
  root.style.setProperty('--theme-signature-panel-dark', visual.panelDark);
  root.style.setProperty('--theme-signature-panel-light', visual.panelLight);
  root.style.setProperty('--theme-signature-card-dark', visual.cardDark);
  root.style.setProperty('--theme-signature-card-light', visual.cardLight);
  root.style.setProperty('--theme-signature-control-dark', visual.controlDark);
  root.style.setProperty('--theme-signature-control-light', visual.controlLight);
  root.style.setProperty('--theme-signature-border', visual.border);
  root.style.setProperty('--theme-signature-panel-shadow', visual.panelShadow);
  root.style.setProperty('--theme-signature-card-shadow', visual.cardShadow);
  root.style.setProperty('--theme-signature-backdrop', visual.backdrop);
  root.style.setProperty('--theme-signature-kicker-spacing', visual.kickerSpacing);
  root.style.setProperty('--theme-signature-kicker-shadow', visual.kickerShadow);
  root.style.setProperty('--ds-shell-pad', layout.shellPad);
  root.style.setProperty('--ds-radius-md', layout.cardRadius);
  root.style.setProperty('--ds-radius-lg', layout.panelRadius);
  root.style.setProperty('--ds-shadow', layout.cardShadowSoft);
  root.style.setProperty('--ds-shadow-hover', layout.panelShadowSoft);
  currentThemePreset = presetKey;
  localStorage.setItem('theme_preset', presetKey);
  renderAppearanceControls();
  updateUserChrome();
  persistOwnPreferences();
}

function getInitials(value) {
  return String(value || '?')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(function(part) { return part.charAt(0).toUpperCase(); })
    .join('') || '?';
}

function updateUserAvatarNode(node, avatarUrl, fallbackText) {
  if (!node) return;
  const safeText = getInitials(fallbackText || '?');
  if (avatarUrl) {
    node.innerHTML = `<img src="${escHtml(avatarUrl)}" alt="${escHtml(safeText)}"/>`;
    node.classList.add('has-photo');
  } else {
    node.textContent = safeText;
    node.classList.remove('has-photo');
  }
}

function updateUserChrome() {
  const prefs = currentUserProfile.preferences || {};
  const user = currentUserProfile.user || {};
  const displayName = (user.display_name || user.username || el('current-user-name') && el('current-user-name').textContent || 'User');
  const roleTitle = user.role === 'admin'
    ? (currentLang === 'en' ? 'Administrador' : 'Administrador')
    : (currentLang === 'en' ? 'User' : 'Usuario');
  const title = roleTitle;
  const avatarUrl = prefs.avatar_url || '';
  const bio = prefs.profile_bio || '';
  updateUserAvatarNode(el('current-user-avatar'), avatarUrl, displayName);
  updateUserAvatarNode(el('profile-persona-avatar'), avatarUrl, displayName);
  if (el('current-user-name')) el('current-user-name').textContent = displayName;
  if (el('current-user-role')) el('current-user-role').textContent = title;
  if (el('current-user-dropdown-role')) el('current-user-dropdown-role').textContent = roleTitle;
  if (el('profile-persona-name')) el('profile-persona-name').textContent = displayName;
  if (el('profile-persona-title')) el('profile-persona-title').textContent = title;
  if (el('profile-avatar-url') && document.activeElement !== el('profile-avatar-url')) el('profile-avatar-url').value = avatarUrl;
  if (el('profile-title') && document.activeElement !== el('profile-title')) el('profile-title').value = prefs.profile_title || '';
  if (el('profile-bio') && document.activeElement !== el('profile-bio')) el('profile-bio').value = bio;
  if (el('profile-motion-level')) el('profile-motion-level').value = prefs.motion_level || 'standard';
  document.documentElement.style.setProperty('--motion-multiplier', prefs.motion_level === 'calm' ? '0.72' : (prefs.motion_level === 'expressive' ? '1.18' : '1'));
  document.documentElement.style.setProperty('--user-bio', `"${bio}"`);
}

let _preferencesSaveTimer = null;

function persistOwnPreferences(extra) {
  if (!currentUserProfile.id) return;
  const payload = Object.assign({
    language: currentLang,
    theme_mode: currentTheme,
    theme_preset: currentThemePreset,
    avatar_url: currentUserProfile.preferences && currentUserProfile.preferences.avatar_url || '',
    profile_title: currentUserProfile.preferences && currentUserProfile.preferences.profile_title || '',
    profile_bio: currentUserProfile.preferences && currentUserProfile.preferences.profile_bio || '',
    motion_level: currentUserProfile.preferences && currentUserProfile.preferences.motion_level || 'standard',
  }, extra || {});
  if (_preferencesSaveTimer) clearTimeout(_preferencesSaveTimer);
  _preferencesSaveTimer = setTimeout(async function() {
    try {
      const data = await postJson(`/api/users/${currentUserProfile.id}/preferences`, payload);
      currentUserProfile.preferences = data.preferences || payload;
      updateUserChrome();
    } catch (_) {}
  }, 180);
}

async function loadCurrentUserProfile() {
  try {
    const data = await api('/api/auth/me');
    currentUserProfile.user = data.user || null;
    currentUserProfile.preferences = data.preferences || {};
    currentUserProfile.saas = data.saas || null;
    if (currentUserProfile.user && currentUserProfile.user.id) {
      currentUserProfile.id = Number(currentUserProfile.user.id) || currentUserProfile.id;
    }
    if (currentUserProfile.user && currentUserProfile.user.role === 'admin') {
      try {
        const adminOverview = await api('/api/saas/admin/overview');
        currentUserProfile.saas = Object.assign({}, currentUserProfile.saas || {}, {
          admin_overview: adminOverview.overview || null,
          plans: adminOverview.plans || [],
        });
      } catch (_) {}
    } else {
      try {
        const planData = await api('/api/saas/plans');
        currentUserProfile.saas = Object.assign({}, currentUserProfile.saas || {}, {
          plans: planData.plans || [],
        });
      } catch (_) {}
    }
    if (currentUserProfile.preferences.theme_mode) currentTheme = currentUserProfile.preferences.theme_mode;
    if (currentUserProfile.preferences.theme_preset) currentThemePreset = currentUserProfile.preferences.theme_preset;
    applyThemePreset(currentThemePreset);
    applyTheme(currentTheme);
    updateUserChrome();
  } catch (_) {}
}

window.previewProfileTheme = function() {
  currentUserProfile.preferences = Object.assign({}, currentUserProfile.preferences || {}, {
    avatar_url: (el('profile-avatar-url') && el('profile-avatar-url').value.trim()) || '',
    profile_title: (el('profile-title') && el('profile-title').value.trim()) || '',
    profile_bio: (el('profile-bio') && el('profile-bio').value.trim()) || '',
    motion_level: (el('profile-motion-level') && el('profile-motion-level').value) || 'standard',
  });
  updateUserChrome();
  showMsg('profile-theme-msg', currentLang === 'en' ? 'Preview updated.' : 'Previa atualizada.', true);
};

window.saveProfileTheme = async function() {
  const prefs = {
    avatar_url: (el('profile-avatar-url') && el('profile-avatar-url').value.trim()) || '',
    profile_title: (el('profile-title') && el('profile-title').value.trim()) || '',
    profile_bio: (el('profile-bio') && el('profile-bio').value.trim()) || '',
    motion_level: (el('profile-motion-level') && el('profile-motion-level').value) || 'standard',
  };
  currentUserProfile.preferences = Object.assign({}, currentUserProfile.preferences || {}, prefs);
  updateUserChrome();
  try {
    const data = await postJson(`/api/users/${currentUserProfile.id}/preferences`, Object.assign({
      language: currentLang,
      theme_mode: currentTheme,
      theme_preset: currentThemePreset,
    }, prefs));
    currentUserProfile.preferences = data.preferences || currentUserProfile.preferences;
    updateUserChrome();
    showMsg('profile-theme-msg', getUiText().settings.profileSaved, true);
  } catch (e) {
    showMsg('profile-theme-msg', (currentLang === 'en' ? 'Error: ' : 'Erro: ') + e.message, false);
  }
};

function applyLang() {
  const t = LANGS[currentLang] || LANGS.pt;
  document.querySelectorAll('[data-i18n]').forEach(function(node) {
    const key = node.getAttribute('data-i18n');
    if (t[key]) node.textContent = t[key];
  });
  reorderViewCollections();
  renderLaunchCards();
  localizeStaticSections();
  renderSidebarNotifications();
  renderAppearanceControls();
  updateUserChrome();
  syncViewChipTitles();
  const lbl = document.getElementById('lang-label');
  if (lbl) lbl.textContent = currentLang === 'pt' ? 'PT' : 'EN';
  updatePageTitle(activeView);
}

async function toggleLang() {
  currentLang = currentLang === 'pt' ? 'en' : 'pt';
  localStorage.setItem('lang', currentLang);
  applyLang();
  persistOwnPreferences();
  try {
    await loadActiveView(false);
  } catch(_) {}
  showToast(getUiText().notifications.langToast, 'info');
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (document.body) document.body.setAttribute('data-theme', theme);
  const dark = document.getElementById('theme-icon-dark');
  const light = document.getElementById('theme-icon-light');
  if (dark) dark.style.display = theme === 'dark' ? 'block' : 'none';
  if (light) light.style.display = theme === 'light' ? 'block' : 'none';
  localStorage.setItem('theme', theme);
  currentTheme = theme;
  renderAppearanceControls();
  persistOwnPreferences();
}

function toggleTheme() {
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  showToast(nextTheme === 'dark' ? getUiText().notifications.themeDarkToast : getUiText().notifications.themeLightToast, 'info');
}

window.setThemeMode = function(mode) {
  applyTheme(mode === 'dark' ? 'dark' : 'light');
};

window.setThemePreset = function(presetKey) {
  applyThemePreset(presetKey);
};

async function manualRefresh() {
  showToast(currentLang === 'en' ? 'Refreshing dashboard...' : 'Atualizando dashboard...', 'info', 1800);
  await refresh(true);
}

function toggleAutoRefresh() {
  autoRefreshEnabled = !autoRefreshEnabled;
  localStorage.setItem('auto_refresh', autoRefreshEnabled ? '1' : '0');
  updateAutoRefreshUI();
  showToast(autoRefreshEnabled ? 'Auto refresh ativado' : 'Auto refresh pausado', autoRefreshEnabled ? 'success' : 'warning');
}

function showToast(msg, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  const icons = {
    success: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    warning: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    info:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  };
  toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span class="toast-msg">${msg}</span><button class="toast-close" onclick="this.parentElement.remove()">Ã—</button>`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    setTimeout(() => toast.remove(), 350);
  }, duration);
}

// â”€â”€ Skeleton loading â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function showSkeleton() {
  const sk = document.getElementById('skeleton-cards');
  const rc = document.getElementById('real-cards');
  if (sk) sk.style.display = 'grid';
  if (rc) rc.style.display = 'none';
}

function hideSkeleton() {
  const sk = document.getElementById('skeleton-cards');
  const rc = document.getElementById('real-cards');
  if (sk) sk.style.display = 'none';
  if (rc) rc.style.display = 'grid';
}

// â”€â”€ SSE Alertas em tempo real â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
let _sseSource = null;
let _sseReconnectTimer = null;

function scheduleSseReconnect() {
  if (_sseReconnectTimer) return;
  _sseReconnectTimer = window.setTimeout(function() {
    _sseReconnectTimer = null;
    startSSE();
  }, 5000);
}

function handleIncomingAlert(data) {
  if (!data || data.ping) return;
  const inserted = pushNotificationItem(data);
  if (!inserted) return;
  playNotificationSound(inserted.type);
  if (inserted.type === 'finance') {
    const scope = inserted.chat_title || inserted.provider_account || 'Financeiro';
    const amount = Number(inserted.amount || 0) > 0 ? ` â€¢ ${formatBRL(inserted.amount)}` : '';
    showToast(`ðŸ’° ${scope}${amount}`, 'info', 5000);
    if (activeView === 'home' || activeView === 'overview' || activeView === 'finance') {
      scheduleActiveViewRefresh(260);
    }
    return;
  }
  const actor = getNotificationActor(inserted);
  const label = inserted.type === 'join' ? 'entrou' : 'saiu';
  showToast(`ðŸ‘¤ ${actor} ${label} em ${inserted.chat_title}`, inserted.type === 'join' ? 'success' : 'warning', 5000);
  if (activeView === 'home' || activeView === 'overview' || activeView === 'events' || activeView === 'members') {
    scheduleActiveViewRefresh(260);
  }
}

function startSSE() {
  if (_sseSource) return;
  try {
    _sseSource = new EventSource('/api/alerts/stream');
    _sseSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (!data || data.ping) return;
        if (!getNotificationActor(data) || !data.chat_title) return;
        const icon  = data.type === 'join' ? 'ðŸŸ¢' : 'ðŸ”´';
        const label = data.type === 'join' ? 'entrou' : 'saiu';
        pushNotificationItem(data);
        playNotificationSound(data.type);
        showToast(`${icon} ${getNotificationActor(data)} ${label} em ${data.chat_title}`, data.type === 'join' ? 'success' : 'warning', 5000);
        // atualiza feed se estiver na overview
        if (activeView === 'overview') loadOverview();
      } catch(err) {}
    };
    _sseSource.onerror = () => {
      _sseSource = null;
      setTimeout(startSSE, 5000);
    };
  } catch(e) {}
}

// â”€â”€ Export CSV/PDF â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function getDownloadFilename(header, fallback) {
  if (!header) return fallback;
  const utf8 = header.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8 && utf8[1]) return decodeURIComponent(utf8[1]);
  const ascii = header.match(/filename="?([^"]+)"?/i);
  return ascii && ascii[1] ? ascii[1] : fallback;
}

function getDefaultExportRange() {
  const end = new Date();
  const start = new Date(end.getTime() - (29 * 24 * 60 * 60 * 1000));
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

function initOverviewExportControls() {
  const start = el('overview-export-start');
  const end = el('overview-export-end');
  if (!start || !end) return;
  const range = getDefaultExportRange();
  if (!start.value) start.value = range.start;
  if (!end.value) end.value = range.end;
  if (el('overview-export-group')) el('overview-export-group').textContent = getSelectedGroupLabel();
}

function getOverviewExportOptions() {
  initOverviewExportControls();
  return {
    start_date: (el('overview-export-start') && el('overview-export-start').value) || '',
    end_date: (el('overview-export-end') && el('overview-export-end').value) || '',
    sections: {
      overview: !(el('overview-section-overview')) || el('overview-section-overview').checked,
      charts: !(el('overview-section-charts')) || el('overview-section-charts').checked,
      events: !(el('overview-section-events')) || el('overview-section-events').checked,
      members: !(el('overview-section-members')) || el('overview-section-members').checked,
      finance: !(el('overview-section-finance')) || el('overview-section-finance').checked,
      campaigns: !(el('overview-section-campaigns')) || el('overview-section-campaigns').checked,
      pixel: !(el('overview-section-pixel')) || el('overview-section-pixel').checked,
    }
  };
}

async function downloadExport(kind, options) {
  if (!chatId) {
    showToast(getUiText().finance.selectWarning, 'warning');
    return;
  }
  const groupName = getSelectedGroupLabel();
  const fetchOptions = options ? {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(options),
  } : undefined;
  const response = await apiBinary(`/api/export/${kind}/${encodeURIComponent(chatId)}`, fetchOptions);
  const blob = await response.blob();
  const filename = getDownloadFilename(response.headers.get('Content-Disposition'), `tg-analytics.${kind}`);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
  showToast(
    currentLang === 'en'
      ? (kind === 'csv' ? `CSV exported for ${groupName}.` : `PDF exported for ${groupName}.`)
      : (kind === 'csv' ? `CSV exportado para ${groupName}.` : `PDF exportado para ${groupName}.`),
    'success'
  );
}

async function exportCSV() {
  try {
    await downloadExport('csv', getOverviewExportOptions());
  } catch(e) {
    showToast((currentLang === 'en' ? 'Could not export CSV: ' : 'Erro ao exportar CSV: ') + e.message, 'error');
  }
}

async function exportPDF() {
  try {
    showToast(
      currentLang === 'en'
        ? `Generating executive PDF for ${getSelectedGroupLabel()}...`
        : `Gerando PDF executivo para ${getSelectedGroupLabel()}...`,
      'info'
    );
    await downloadExport('pdf', getOverviewExportOptions());
  } catch(e) {
    showToast((currentLang === 'en' ? 'Could not export PDF: ' : 'Erro ao exportar PDF: ') + e.message, 'error');
  }
}

// â”€â”€ Scheduler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function loadScheduler() {
  const text = getUiText();
  const tbody = document.getElementById('sched-tbody');
  const empty = document.getElementById('sched-empty');
  if (!tbody) return;
  try {
    const url  = chatId ? `/api/scheduler?chat_id=${chatId}` : '/api/scheduler';
    const rows = await api(url);
    tbody.innerHTML = '';
    if (!rows.length) {
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    rows.forEach((r, i) => {
      const tr = document.createElement('tr');
      const status = r.sent ? '<span style="color:var(--green);font-weight:600">âœ“ Enviado</span>' : '<span style="color:var(--yellow);font-weight:600">â³ Pendente</span>';
      tr.innerHTML = `
        <td>${i+1}</td>
        <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.message}</td>
        <td style="white-space:nowrap">${r.send_at}</td>
        <td>${status}</td>
        <td><button class="btn-del" onclick="schedDelete(${r.id})">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
        </button></td>`;
      const statusNode = tr.querySelector('td:nth-child(4) span');
      if (statusNode) statusNode.textContent = `${r.sent ? 'âœ“' : 'â³'} ${r.sent ? text.scheduler.sent : text.scheduler.pending}`;
      tbody.appendChild(tr);
    });
  } catch(e) { showToast(text.scheduler.loadError, 'error'); }
}

async function schedAdd() {
  const text = getUiText();
  const msg = document.getElementById('sched-msg').value.trim();
  const dt  = document.getElementById('sched-dt').value;
  const fb  = document.getElementById('sched-msg-feedback');
  if (!chatId) { showToast(text.scheduler.selectWarning, 'warning'); return; }
  if (!msg)  { showToast(text.scheduler.messageRequired, 'warning'); return; }
  if (!dt)   { showToast(text.scheduler.dateRequired, 'warning'); return; }
  try {
    await fetch('/api/scheduler', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ chat_id: chatId, message: msg, send_at: dt })
    });
    document.getElementById('sched-msg').value = '';
    document.getElementById('sched-dt').value  = '';
    showToast(text.scheduler.scheduled, 'success');
    await loadScheduler();
  } catch(e) { showToast(text.scheduler.scheduleError, 'error'); }
}

async function schedDelete(id) {
  await fetch(`/api/scheduler/${id}`, { method: 'DELETE' });
  showToast(getUiText().scheduler.removed, 'info');
  await loadScheduler();
}

// â”€â”€ Bot logs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
let _logInterval = null;

async function loadLogs() {
  const text = getUiText();
  try {
    const logs = await api('/api/bot/logs');
    const box  = document.getElementById('log-container');
    if (!box) return;
    if (!logs.length) {
      box.innerHTML = `<div class="log-placeholder">${text.logs.waiting}</div>`;
      return;
    }
    const wasBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 30;
    box.innerHTML = logs.map(l =>
      `<div class="log-line"><span class="log-time">${l.time}</span><span class="log-msg">${escHtml(l.msg)}</span></div>`
    ).join('');
    if (wasBottom) box.scrollTop = box.scrollHeight;
  } catch(e) {}
}

function clearLogs() {
  const box = document.getElementById('log-container');
  if (box) box.innerHTML = `<div class="log-placeholder">${getUiText().logs.cleared}</div>`;
}

function escHtml(s) {
  return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// â”€â”€ Gerador de senhas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
let _pwTargetField = null;

function pwGenUpdate() {
  const len   = parseInt(document.getElementById('pw-len').value);
  const upper = document.getElementById('pw-upper').checked;
  const num   = document.getElementById('pw-num').checked;
  const sym   = document.getElementById('pw-sym').checked;
  document.getElementById('pw-len-val').textContent = len;

  let chars = 'abcdefghijklmnopqrstuvwxyz';
  if (upper) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  if (num)   chars += '0123456789';
  if (sym)   chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';

  let pw = '';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  arr.forEach(v => pw += chars[v % chars.length]);

  document.getElementById('pw-result').value = pw;

  // forÃ§a meter
  const score = (upper?1:0)+(num?1:0)+(sym?1:0)+(len>=16?1:0)+(len>=24?1:0);
  const colors = ['#ef4444','#f59e0b','#f59e0b','#22c55e','#22c55e'];
  const labels = ['Muito fraca','Fraca','MÃ©dia','Forte','Muito forte'];
  const fill   = document.getElementById('pw-strength-fill');
  const label  = document.getElementById('pw-strength-label');
  if (fill)  { fill.style.width = `${(score/5)*100}%`; fill.style.background = colors[score-1]||'#ef4444'; }
  if (label) label.textContent = labels[score-1] || 'Muito fraca';
}

function pwCopy() {
  const val = document.getElementById('pw-result').value;
  if (!val) return;
  navigator.clipboard.writeText(val).then(() => showToast(getUiText().vault.passwordCopied, 'success'));
}

function pwUseInField() {
  const val = document.getElementById('pw-result').value;
  if (!val) return;
  const target = _pwTargetField || Array.from(document.querySelectorAll('#vm-fields .vf-value')).pop();
  if (target) {
    target.value = val;
    showToast(getUiText().vault.passwordUsed, 'success');
  }
  _pwTargetField = null;
  el('vault-pw-modal').style.display = 'none';
}

// â”€â”€ Vault busca global â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function vaultGlobalSearch(q) {
  q = q.toLowerCase().trim();
  const cards = document.querySelectorAll('#vault-entries .vault-card');
  if (!q) { cards.forEach(c => c.style.display = ''); return; }
  cards.forEach(c => {
    const text = c.textContent.toLowerCase();
    c.style.display = text.includes(q) ? '' : 'none';
  });
}

// â”€â”€ Vault histÃ³rico â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function showVaultHistory() {
  try {
    const logs = await api('/api/vault/access_log');
    const box  = document.getElementById('vault-history-list');
    if (!box) return;
    if (!logs.length) {
      box.innerHTML = `<p style="color:var(--muted);padding:10px">${getUiText().vault.historyEmpty}</p>`;
    } else {
      box.innerHTML = logs.map(l =>
        `<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--border);font-size:13px">
          <span>${escHtml(l.action)}</span>
          <span style="color:var(--muted);font-size:11px">${l.created_at}</span>
        </div>`
      ).join('');
    }
    el('vault-history-modal').style.display = 'flex';
  } catch(e) { showToast('Erro ao carregar histÃ³rico', 'error'); }
}

// â”€â”€ Hook no vaultCopyField para logar acesso â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


// â”€â”€ Dispatcher atualizado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const _extraLoaders = {
  scheduler: loadScheduler,
  logs: loadLogs,
};

// â”€â”€ Override da navegaÃ§Ã£o para incluir novas views â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function updatePageTitle(view) {
  const t = LANGS[currentLang] || LANGS.pt;
  const titleKey = view + '_title';
  const titleEl = document.getElementById('page-title');
  if (titleEl) titleEl.textContent = t[titleKey] || view.charAt(0).toUpperCase() + view.slice(1);
  const sidebarTitle = document.getElementById('sidebar-current-view');
  const sidebarDesc = document.getElementById('sidebar-current-description');
  const context = (VIEW_CONTEXT[currentLang] || VIEW_CONTEXT.pt)[view];
  if (sidebarTitle) sidebarTitle.textContent = t[titleKey] || view.charAt(0).toUpperCase() + view.slice(1);
  if (sidebarDesc) sidebarDesc.textContent = context || '';
}

function syncViewControls(view) {
  document.querySelectorAll('.nav-item, .view-chip').forEach(node => {
    node.classList.toggle('active', node.dataset.view === view);
  });
  document.querySelectorAll('.launch-card[data-view]').forEach(node => {
    node.classList.toggle('is-current', node.dataset.view === view);
  });
}

function restartLogPolling(view) {
  if (view === 'logs') {
    if (_logInterval) clearInterval(_logInterval);
    _logInterval = setInterval(function() {
      if (document.hidden) return;
      loadLogs();
    }, LOG_REFRESH_MS);
    return;
  }
  if (_logInterval) {
    clearInterval(_logInterval);
    _logInterval = null;
  }
}

function animateViewIn(viewEl) {
  if (!viewEl) return;
  viewEl.classList.remove('animate-in');
  void viewEl.offsetWidth;
  viewEl.classList.add('animate-in');
}

window.toggleUserMenu = function() {
  const wrap = el('topbar-user-menu-wrap');
  if (!wrap) return;
  wrap.classList.toggle('is-open');
};

async function activateView(view, opts) {
  const options = opts || {};
  const forceOverviewSkeleton = options.forceOverviewSkeleton !== false;
  activeView = view;
  syncViewControls(view);
  updatePageTitle(view);
  updateViewRailVisibility(view);
  scrollActiveChipIntoView(view);

  document.querySelectorAll('.view').forEach(v => {
    v.classList.remove('active');
    v.classList.remove('animate-in');
  });

  const viewEl = document.getElementById(`view-${view}`);
  if (viewEl) {
    viewEl.classList.add('active');
    animateViewIn(viewEl);
  }

  restartLogPolling(view);
  if (view !== 'finance') stopFinancePolling();

  if (_extraLoaders[view]) await _extraLoaders[view]();
  else await loadActiveView(forceOverviewSkeleton);
}

document.querySelectorAll('.nav-item, .view-chip, .launch-card[data-view]').forEach(node => {
  node.addEventListener('click', async e => {
    e.preventDefault();
    animateViewChipPress(node);
    await activateView(node.dataset.view, { forceOverviewSkeleton: true });
  });
});

// â”€â”€ Boot extras â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
window.toggleTheme = function() {
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  showToast(nextTheme === 'dark' ? getUiText().notifications.themeDarkToast : getUiText().notifications.themeLightToast, 'info');
};
window.toggleLang = toggleLang;
window.manualRefresh = manualRefresh;
window.toggleAutoRefresh = toggleAutoRefresh;
window.exportCSV = exportCSV;
window.exportPDF = exportPDF;
window.loadPixel = loadPixel;
window.savePixelSettings = savePixelSettings;
window.refreshPixelOverview = refreshPixelOverview;
window.previewGoals = previewGoals;
window.saveGoals = saveGoals;
window.resetGoals = resetGoals;
window.loadFinance = loadFinance;
window.refreshAllFinancePayments = refreshAllFinancePayments;
window.openVaultPasswordGenerator = openVaultPasswordGenerator;
window.saveFinanceSettings = saveFinanceSettings;
window.createFinancePayment = createFinancePayment;
window.refreshFinancePayment = refreshFinancePayment;
window.searchNames = searchNames;
window.clearNameSearch = clearNameSearch;
window.onNameSearchTypeChange = onNameSearchTypeChange;

startSSE = function() {
  if (_sseSource) return;
  try {
    _sseSource = new EventSource('/api/alerts/stream');
    _sseSource.onmessage = (e) => {
      try {
        handleIncomingAlert(JSON.parse(e.data));
        return;
        const data = JSON.parse(e.data);
        if (!data || data.ping) return;
        pushNotificationItem(data);
        playNotificationSound(data.type);
        if (data.type === 'finance') {
          const scope = data.chat_title || data.provider_account || 'Financeiro';
          const amount = Number(data.amount || 0) > 0 ? ` â€¢ ${formatBRL(data.amount)}` : '';
          showToast(`PIX â€¢ ${scope}${amount}`, 'info', 5000);
          if (activeView === 'home' || activeView === 'overview' || activeView === 'finance') {
            scheduleActiveViewRefresh(260);
          }
          return;
        }
        if (!getNotificationActor(data) || !data.chat_title) return;
        const icon = data.type === 'join' ? 'ðŸŸ¢' : 'ðŸ”´';
        const label = data.type === 'join' ? 'entrou' : 'saiu';
        showToast(`${icon} ${getNotificationActor(data)} ${label} em ${data.chat_title}`, data.type === 'join' ? 'success' : 'warning', 5000);
        if (activeView === 'home' || activeView === 'overview' || activeView === 'events' || activeView === 'members') {
          scheduleActiveViewRefresh(260);
        }
      } catch(err) {}
    };
    _sseSource.onerror = () => {
      if (_sseSource) {
        try { _sseSource.close(); } catch(_) {}
      }
      _sseSource = null;
      scheduleSseReconnect();
      return;
      _sseSource = null;
      setTimeout(startSSE, 5000);
    };
  } catch(e) {
    scheduleSseReconnect();
  }
};

document.addEventListener('DOMContentLoaded', () => {
  applyThemePreset(currentThemePreset);
  applyTheme(currentTheme);
  applyLang();
  syncViewChipTitles();
  syncViewControls(activeView);
  updateViewRailVisibility(activeView);
  syncExportButtons();
  initOverviewExportControls();
  renderSidebarNotifications();
  setNotificationsDrawer(false);
  toggleEventSearchClear();
  initViewRailDrag();
  document.addEventListener('pointerdown', ensureAudioContext, { passive: true });
  document.addEventListener('pointerdown', function(e) {
    const notifyToggle = el('notifications-toggle');
    const notifyPanel = el('topbar-notifications-panel');
    if (notifyPanel && notifyToggle && !notifyPanel.contains(e.target) && !notifyToggle.contains(e.target)) {
      setNotificationsDrawer(false);
    }
  }, true);
  document.addEventListener('click', function(e) {
    const wrap = el('topbar-user-menu-wrap');
    if (wrap && !wrap.contains(e.target)) wrap.classList.remove('is-open');
    const notifyToggle = el('notifications-toggle');
    const notifyPanel = el('topbar-notifications-panel');
    if (notifyPanel && notifyToggle && !notifyPanel.contains(e.target) && !notifyToggle.contains(e.target)) {
      setNotificationsDrawer(false);
    }
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeNotificationsDrawer();
      const wrap = el('topbar-user-menu-wrap');
      if (wrap) wrap.classList.remove('is-open');
    }
  });
  animateViewIn(document.getElementById(`view-${activeView}`));
  startSSE();
  pwGenUpdate();
  loadCurrentUserProfile();
});

