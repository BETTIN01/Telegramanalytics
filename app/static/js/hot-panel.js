'use strict';

(function() {
  const USER_CACHE_PREFIX = 'painel_hot_cache_v1_';
  const SAFE_NOTIFICATIONS_KEY = typeof NOTIFICATIONS_KEY !== 'undefined'
    ? NOTIFICATIONS_KEY
    : 'tg_analytics_notifications_v1';
  const SAFE_GOALS_KEY = typeof GOALS_KEY !== 'undefined'
    ? GOALS_KEY
    : 'tg_analytics_goals_v1';
  const HOT_VIEW_ORDER = ['home', 'overview', 'charts', 'events', 'reports', 'goals', 'pixel', 'finance', 'members', 'vault', 'scheduler', 'logs', 'settings'];
  const HOT_LAUNCH_ORDER = ['overview', 'charts', 'events', 'reports', 'goals', 'pixel', 'finance', 'members', 'vault', 'scheduler', 'logs', 'settings'];
  const AUTH_USER = window.PAINEL_HOT_AUTH || null;

  const HOT_COPY = {
    pt: {
      nav: { campaigns: 'Campanhas' },
      topbar: {
        activeProfile: 'Conta conectada',
        adminRole: 'Administrador',
        userRole: 'Usuario',
        welcome: function(name) { return 'Bem-vindo, ' + name; }
      },
      launch: {
        campaigns: {
          kicker: 'Aquisicao',
          title: 'Campanhas',
          desc: 'Marque origem de entrada, acompanhe custo por membro e compare canais.'
        }
      },
      reports: {
        scheduleTitle: 'Relatorio semanal automatico',
        scheduleCopy: 'Automatize PDF ou CSV por e-mail ou Telegram para apresentar resultado recorrente sem trabalho manual.',
        deliveryTelegram: 'Telegram',
        deliveryEmail: 'E-mail',
        destinationPlaceholder: 'Chat ID ou e-mail',
        scheduleBtn: 'Agendar',
        downloadPdf: 'Baixar PDF agora',
        downloadCsv: 'Baixar CSV agora',
        headers: ['#', 'Entrega', 'Destino', 'Formato', 'Agenda', 'Ultimo envio', 'Acao'],
        empty: 'Nenhum envio semanal configurado.',
        scheduleSaved: 'Agenda semanal salva.',
        deliveryUpdated: 'Entrega de relatorios atualizada.',
        sendNow: 'Enviar agora',
        remove: 'Remover',
        weekday: ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo'],
        at: function(time) { return 'Toda ' + time.day + ' as ' + time.hour; }
      },
      campaigns: {
        heroKicker: 'Aquisicao',
        heroTitle: 'Painel de campanhas',
        heroCopy: 'Marque a origem de cada membro, acompanhe custo por membro e compare campanhas, canais e bots por grupo.',
        summaryTitle: 'Origens ativas',
        summaryCopy: 'Selecione um grupo para acompanhar entradas por origem.',
        sourcePanel: 'Nova origem',
        assignPanel: 'Marcar origem do membro',
        fields: {
          name: 'Nome da origem',
          type: 'Tipo',
          cost: 'Custo total (R$)',
          notes: 'Notas',
          member: 'Membro',
          origin: 'Origem'
        },
        placeholders: {
          name: 'Campanha HOT, Canal VIP, Bot Z',
          cost: '0.00',
          notes: 'Observacoes rapidas'
        },
        buttons: {
          saveSource: 'Salvar origem',
          saveAssignment: 'Salvar marcacao',
          deleteSource: 'Excluir origem',
          deleteAssignment: 'Remover'
        },
        tables: {
          report: 'Relatorio por origem',
          assignments: 'Membros marcados',
          reportHeaders: ['Origem', 'Tipo', 'Entradas', 'Saidas', 'Membros marcados', 'Custo', 'Custo por membro', 'Acao'],
          assignmentHeaders: ['#', 'Membro', 'Origem', 'Tipo', 'Marcado em', 'Acao']
        },
        types: {
          campaign: 'Campanha',
          channel: 'Canal',
          bot: 'Bot',
          other: 'Outro'
        },
        empty: {
          report: 'Nenhuma origem cadastrada.',
          assignments: 'Nenhum membro marcado.'
        },
        savedSource: 'Origem salva com sucesso.',
        savedAssignment: 'Origem vinculada ao membro.',
        removedSource: 'Origem removida.',
        removedAssignment: 'Marcacao removida.',
        selectGroup: 'Selecione um grupo primeiro.',
        requiredSource: 'Preencha o nome da origem.',
        requiredAssignment: 'Selecione membro e origem.'
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
        usersTitle: 'Usuarios de acesso',
        usersCopy: 'Crie contas para acessar o painel com senha, papel e preferencias visuais separadas por usuario.',
        userFields: { username: 'usuario', displayName: 'Nome de exibicao', password: 'Senha', role: 'Papel' },
        userHeaders: ['#', 'Usuario', 'Nome', 'Papel', 'Status', 'Ultimo acesso', 'Acao'],
        createUser: 'Criar usuario',
        activeBadge: 'Ativo',
        deleteProfile: 'Excluir',
        adminBadge: 'Administrador',
        userBadge: 'Usuario',
        statusActive: 'Ativo',
        statusInactive: 'Inativo',
        noPermission: 'Apenas administradores podem gerenciar usuarios.',
        reportDeliveryTitle: 'Entrega automatica de relatorios',
        reportDeliveryCopy: 'Configure SMTP para envios por e-mail. Os envios por Telegram usam o proprio bot quando voce informar um chat ID na agenda.',
        smtp: {
          host: 'SMTP host',
          port: 'Porta',
          username: 'Usuario SMTP',
          password: 'Senha SMTP',
          sender: 'Remetente',
          tls: 'Usar TLS',
          save: 'Salvar entrega'
        },
        createdUser: 'Usuario criado.',
        removedUser: 'Usuario removido.',
        fillUser: 'Digite usuario e senha para criar o acesso.',
        keepOneUser: 'Mantenha pelo menos um perfil.',
        deleteProfileConfirm: function(name) { return 'Remover o usuario ' + name + '?'; }
      }
    },
    en: {
      nav: { campaigns: 'Campaigns' },
      topbar: {
        activeProfile: 'Connected account',
        adminRole: 'Administrator',
        userRole: 'User',
        welcome: function(name) { return 'Welcome, ' + name; }
      },
      launch: {
        campaigns: {
          kicker: 'Acquisition',
          title: 'Campaigns',
          desc: 'Tag join sources, track cost per member and compare channels.'
        }
      },
      reports: {
        scheduleTitle: 'Automatic weekly report',
        scheduleCopy: 'Automate PDF or CSV delivery by email or Telegram and keep a client-ready reporting routine.',
        deliveryTelegram: 'Telegram',
        deliveryEmail: 'Email',
        destinationPlaceholder: 'Chat ID or email',
        scheduleBtn: 'Schedule',
        downloadPdf: 'Download PDF now',
        downloadCsv: 'Download CSV now',
        headers: ['#', 'Delivery', 'Destination', 'Format', 'Schedule', 'Last sent', 'Action'],
        empty: 'No weekly deliveries configured yet.',
        scheduleSaved: 'Weekly schedule saved.',
        deliveryUpdated: 'Report delivery updated.',
        sendNow: 'Send now',
        remove: 'Remove',
        weekday: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        at: function(time) { return 'Every ' + time.day + ' at ' + time.hour; }
      },
      campaigns: {
        heroKicker: 'Acquisition',
        heroTitle: 'Campaign panel',
        heroCopy: 'Tag each member source, track cost per member and compare campaigns, channels and bots by group.',
        summaryTitle: 'Active sources',
        summaryCopy: 'Select a group to track entries by source.',
        sourcePanel: 'New source',
        assignPanel: 'Assign member source',
        fields: {
          name: 'Source name',
          type: 'Type',
          cost: 'Total cost',
          notes: 'Notes',
          member: 'Member',
          origin: 'Source'
        },
        placeholders: {
          name: 'HOT Campaign, VIP Channel, Bot Z',
          cost: '0.00',
          notes: 'Quick notes'
        },
        buttons: {
          saveSource: 'Save source',
          saveAssignment: 'Save assignment',
          deleteSource: 'Delete source',
          deleteAssignment: 'Remove'
        },
        tables: {
          report: 'Source report',
          assignments: 'Tagged members',
          reportHeaders: ['Source', 'Type', 'Joins', 'Leaves', 'Tagged members', 'Cost', 'Cost per member', 'Action'],
          assignmentHeaders: ['#', 'Member', 'Source', 'Type', 'Tagged at', 'Action']
        },
        types: {
          campaign: 'Campaign',
          channel: 'Channel',
          bot: 'Bot',
          other: 'Other'
        },
        empty: {
          report: 'No sources created yet.',
          assignments: 'No tagged members yet.'
        },
        savedSource: 'Source saved.',
        savedAssignment: 'Member source linked.',
        removedSource: 'Source deleted.',
        removedAssignment: 'Assignment removed.',
        selectGroup: 'Select a group first.',
        requiredSource: 'Enter a source name.',
        requiredAssignment: 'Select a member and a source.'
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
        usersTitle: 'Access users',
        usersCopy: 'Create accounts with password, role and visual preferences isolated per user.',
        userFields: { username: 'username', displayName: 'Display name', password: 'Password', role: 'Role' },
        userHeaders: ['#', 'Username', 'Name', 'Role', 'Status', 'Last login', 'Action'],
        createUser: 'Create user',
        activeBadge: 'Active',
        deleteProfile: 'Delete',
        adminBadge: 'Administrator',
        userBadge: 'User',
        statusActive: 'Active',
        statusInactive: 'Inactive',
        noPermission: 'Only administrators can manage users.',
        reportDeliveryTitle: 'Automatic report delivery',
        reportDeliveryCopy: 'Configure SMTP for email delivery. Telegram delivery uses the bot itself when you provide a chat ID in the schedule.',
        smtp: {
          host: 'SMTP host',
          port: 'Port',
          username: 'SMTP username',
          password: 'SMTP password',
          sender: 'Sender',
          tls: 'Use TLS',
          save: 'Save delivery'
        },
        createdUser: 'User created.',
        removedUser: 'User removed.',
        fillUser: 'Enter username and password to create the account.',
        keepOneUser: 'Keep at least one profile.',
        deleteProfileConfirm: function(name) { return 'Delete user ' + name + '?'; }
      }
    }
  };

  let hotUsers = [];
  let currentDashboardUser = AUTH_USER;
  let activeDashboardUserId = AUTH_USER && AUTH_USER.id ? String(AUTH_USER.id) : '';
  let hotUserHydrated = false;

  function hotText() {
    return HOT_COPY[currentLang] || HOT_COPY.pt;
  }

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function $all(selector, root) {
    return Array.from((root || document).querySelectorAll(selector));
  }

  function escapeHtmlSafe(value) {
    if (typeof escHtml === 'function') return escHtml(value);
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function money(value) {
    if (typeof formatMoney === 'function') return formatMoney(value);
    const numeric = Number(value || 0);
    const locale = currentLang === 'en' ? 'en-US' : 'pt-BR';
    return numeric.toLocaleString(locale, { style: 'currency', currency: currentLang === 'en' ? 'USD' : 'BRL' });
  }

  function readJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function writeJson(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function cacheKey(userId) {
    return USER_CACHE_PREFIX + String(userId || '');
  }

  function getCurrentUserCache() {
    return {
      language: currentLang,
      theme_mode: currentTheme,
      theme_preset: currentThemePreset,
      auto_refresh: !!autoRefreshEnabled,
      goals: goalSettings || {}
    };
  }

  function snapshotActiveUserCache() {
    if (!activeDashboardUserId) return;
    writeJson(cacheKey(activeDashboardUserId), getCurrentUserCache());
  }

  function applyScopedCache(cache) {
    const scoped = cache || {};
    if (scoped.language) {
      currentLang = scoped.language;
      localStorage.setItem('lang', currentLang);
    }
    if (scoped.theme_mode) {
      currentTheme = scoped.theme_mode;
      localStorage.setItem('theme', currentTheme);
    }
    if (scoped.theme_preset) {
      currentThemePreset = scoped.theme_preset;
      localStorage.setItem('theme_preset', currentThemePreset);
    }
    if (typeof scoped.auto_refresh !== 'undefined') {
      autoRefreshEnabled = !!scoped.auto_refresh;
      localStorage.setItem('auto_refresh', autoRefreshEnabled ? '1' : '0');
      if (typeof updateAutoRefreshUI === 'function') updateAutoRefreshUI();
    }
    if (scoped.goals && typeof scoped.goals === 'object') {
      goalSettings = scoped.goals;
      writeJson(SAFE_GOALS_KEY, goalSettings);
    }
  }

  if (activeDashboardUserId) {
    applyScopedCache(readJson(cacheKey(activeDashboardUserId), {}));
  }

  try {
    if (Array.isArray(VIEW_ORDER)) VIEW_ORDER.splice(0, VIEW_ORDER.length, ...HOT_VIEW_ORDER);
  } catch (_) {}

  try {
    if (Array.isArray(LAUNCH_ORDER)) LAUNCH_ORDER.splice(0, LAUNCH_ORDER.length, ...HOT_LAUNCH_ORDER);
  } catch (_) {}

  try {
    LANGS.pt.nav_pixel = 'PIXEL';
    LANGS.en.nav_pixel = 'PIXEL';
    LANGS.pt.pixel_title = 'PIXEL';
    LANGS.en.pixel_title = 'PIXEL';
  } catch (_) {}

  try {
    UI_COPY.pt.launch.pixel = { kicker: 'Meta', title: 'PIXEL', desc: 'Conecte o Pixel da Meta, acompanhe campanhas, cliques e leads em um unico painel.' };
    UI_COPY.en.launch.pixel = { kicker: 'Meta', title: 'PIXEL', desc: 'Connect Meta Pixel and monitor campaigns, clicks and leads in one place.' };
  } catch (_) {}

  try {
    VIEW_CONTEXT.pt.pixel = 'Conecte a Meta para acompanhar status de campanhas, cliques, leads e preparar o rastreamento do Pixel.';
    VIEW_CONTEXT.en.pixel = 'Connect Meta to track campaign status, clicks, leads and prepare full Pixel tracking.';
  } catch (_) {}

  function syncHotLabels() {
    $all('.view-chip').forEach(function(node) {
      const label = $('.view-chip-label', node);
      const text = label ? label.textContent.trim() : '';
      if (!text) return;
      node.dataset.hotLabel = text;
      node.setAttribute('aria-label', text);
      node.setAttribute('title', text);
    });
    $all('.launch-card').forEach(function(node) {
      const title = $('strong', node);
      const text = title ? title.textContent.trim() : '';
      if (!text) return;
      node.dataset.hotLabel = text;
      node.setAttribute('aria-label', text);
      node.setAttribute('title', text);
    });
  }

  const HOT_SELECT_SELECTOR = [
    '#event-type-filter',
    '#member-role-filter',
    '#report-delivery-type',
    '#report-format',
    '#report-weekday',
    '#campaign-source-type',
    '#campaign-member-select',
    '#campaign-origin-select',
    '#dashboard-user-role'
  ].join(', ');

  function getHotSelectText(select) {
    if (!select || !select.options || !select.options.length) return '-';
    const option = select.options[select.selectedIndex] || select.options[0];
    return option ? option.textContent.trim() : '-';
  }

  function closeAllHotSelects(except) {
    $all('.hot-select.is-open').forEach(function(node) {
      if (except && node === except) return;
      node.classList.remove('is-open');
      const select = node.querySelector('select');
      if (select && select.__hotSelect) setHotSelectAncestors(select.__hotSelect, false);
      const trigger = $('.hot-select-trigger', node);
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    });
  }

  function setHotSelectAncestors(instance, isOpen) {
    if (!instance || !instance.host) return;
    let current = instance.host;
    while (current && current !== document.body) {
      if (current.matches && current.matches('.goal-field, .members-actions, .members-bar, .panel, .panel-body, .settings-section, .settings-body, .table-wrap, .table-tools, .goals-layout, .view')) {
        current.classList.toggle('hot-select-parent-open', !!isOpen);
      }
      current = current.parentElement;
    }
  }

  function syncHotSelect(select) {
    if (!select) return;
    const instance = select.__hotSelect;
    if (!instance) return;

    const valueText = getHotSelectText(select);
    instance.value.textContent = valueText;
    instance.value.title = valueText;
    instance.trigger.disabled = !!select.disabled;
    instance.host.classList.toggle('is-disabled', !!select.disabled);
    instance.trigger.setAttribute('aria-expanded', instance.host.classList.contains('is-open') ? 'true' : 'false');

    instance.menu.innerHTML = '';
    Array.from(select.options || []).forEach(function(option) {
      const optionButton = document.createElement('button');
      optionButton.type = 'button';
      optionButton.className = 'hot-select-option' + (option.selected ? ' is-selected' : '');
      optionButton.dataset.value = option.value;
      optionButton.disabled = !!option.disabled;
      optionButton.setAttribute('role', 'option');
      optionButton.setAttribute('aria-selected', option.selected ? 'true' : 'false');
      optionButton.innerHTML =
        '<span class="hot-select-option-label">' + escapeHtmlSafe(option.textContent.trim()) + '</span>' +
        (option.selected ? '<span class="hot-select-option-check" aria-hidden="true">✓</span>' : '');
      optionButton.addEventListener('click', function() {
        if (select.value !== option.value) {
          select.value = option.value;
          select.dispatchEvent(new Event('change', { bubbles: true }));
        }
        closeAllHotSelects();
        syncHotSelect(select);
      });
      instance.menu.appendChild(optionButton);
    });

    if (!instance.menu.children.length) {
      const emptyState = document.createElement('div');
      emptyState.className = 'hot-select-empty';
      emptyState.textContent = currentLang === 'en' ? 'No options' : 'Sem opcoes';
      instance.menu.appendChild(emptyState);
    }
  }

  function buildHotSelect(select) {
    if (!select) return null;

    let host = select.parentElement && select.parentElement.classList.contains('hot-select')
      ? select.parentElement
      : null;

    if (!host && select.parentElement && select.parentElement.classList.contains('select-wrap')) {
      host = select.parentElement;
      host.classList.add('hot-select', 'hot-select--topbar');
    }

    if (!host) {
      host = document.createElement('div');
      host.className = 'hot-select';
      const computedWidth = window.getComputedStyle(select).width;
      if (select.style.width) host.style.width = select.style.width;
      else if (computedWidth && computedWidth !== 'auto' && computedWidth !== '0px') host.style.width = computedWidth;
      select.parentNode.insertBefore(host, select);
      host.appendChild(select);
    }

    select.classList.add('hot-select-native');

    let trigger = $('.hot-select-trigger', host);
    if (!trigger) {
      trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'hot-select-trigger';
      trigger.setAttribute('aria-haspopup', 'listbox');
      trigger.innerHTML =
        '<span class="hot-select-value"></span>' +
        '<span class="hot-select-caret" aria-hidden="true"></span>';
      host.appendChild(trigger);
    }

    let menu = $('.hot-select-menu', host);
    if (!menu) {
      menu = document.createElement('div');
      menu.className = 'hot-select-menu';
      menu.setAttribute('role', 'listbox');
      host.appendChild(menu);
    }

    const value = $('.hot-select-value', trigger);
    const instance = { select: select, host: host, trigger: trigger, menu: menu, value: value };
    select.__hotSelect = instance;
    host.classList.toggle('hot-select--compact-menu', select.id === 'campaign-member-select');
    host.classList.toggle('hot-select--member-picker', select.id === 'campaign-member-select');
    host.classList.toggle('hot-select--campaign-type', select.id === 'campaign-source-type');
    host.classList.toggle('hot-select--member-filter', select.id === 'member-role-filter');
    host.classList.toggle('hot-select--settings-nav', !!(select.closest && select.closest('#view-settings')));

    if (!select.dataset.hotSelectBound) {
      select.dataset.hotSelectBound = '1';

      trigger.addEventListener('click', function() {
        if (select.disabled) return;
        const willOpen = !host.classList.contains('is-open');
        closeAllHotSelects(host);
        host.classList.toggle('is-open', willOpen);
        setHotSelectAncestors(instance, willOpen);
        trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      });

      select.addEventListener('change', function() {
        syncHotSelect(select);
      });

      const observer = new MutationObserver(function() {
        syncHotSelect(select);
      });
      observer.observe(select, {
        childList: true,
        subtree: true,
        attributes: true,
        characterData: true,
        attributeFilter: ['disabled', 'label']
      });
      select.__hotObserver = observer;
    }

    syncHotSelect(select);
    return instance;
  }

  function refreshHotSelects(root) {
    $all(HOT_SELECT_SELECTOR, root || document).forEach(function(select) {
      buildHotSelect(select);
      syncHotSelect(select);
    });
  }

  function localizeCampaignScreen() {
    const text = hotText().campaigns;
    setText('#view-campaigns .finance-kicker', text.heroKicker);
    setText('#campaigns-title', text.heroTitle);
    setText('#campaigns-copy', text.heroCopy);
    setText('#campaigns-summary-title', text.summaryTitle);
    setText('#campaigns-summary-copy', text.summaryCopy);

    const panels = $all('#view-campaigns .panel-header');
    setText(panels[0], text.sourcePanel);
    setText(panels[1], text.assignPanel);

    const sourceFields = $all('#view-campaigns .goal-field > span');
    setText(sourceFields[0], text.fields.name);
    setText(sourceFields[1], text.fields.type);
    setText(sourceFields[2], text.fields.cost);
    setText(sourceFields[3], text.fields.notes);
    setText(sourceFields[4], text.fields.member);
    setText(sourceFields[5], text.fields.origin);

    setPlaceholder('#campaign-source-name', text.placeholders.name);
    setPlaceholder('#campaign-source-cost', text.placeholders.cost);
    setPlaceholder('#campaign-source-notes', text.placeholders.notes);

    const sourceType = el('campaign-source-type');
    if (sourceType) {
      Array.from(sourceType.options).forEach(function(option) {
        option.textContent = text.types[option.value] || option.textContent;
      });
      syncHotSelect(sourceType);
    }

    const actionButtons = $all('#view-campaigns .goals-form-actions .btn-primary');
    setButtonLabel(actionButtons[0], text.buttons.saveSource);
    setButtonLabel(actionButtons[1], text.buttons.saveAssignment);
    setText('#view-campaigns .table-wrap:nth-of-type(1) .table-title', text.tables.report);
    setText('#view-campaigns .table-wrap:nth-of-type(2) .table-title', text.tables.assignments);

    $all('#view-campaigns .table-wrap:nth-of-type(1) thead th').forEach(function(th, idx) {
      if (typeof text.tables.reportHeaders[idx] !== 'undefined') th.textContent = text.tables.reportHeaders[idx];
    });
    $all('#view-campaigns .table-wrap:nth-of-type(2) thead th').forEach(function(th, idx) {
      if (typeof text.tables.assignmentHeaders[idx] !== 'undefined') th.textContent = text.tables.assignmentHeaders[idx];
    });

    const chipLabel = $('.view-chip[data-view="campaigns"] .view-chip-label');
    setText(chipLabel, hotText().nav.campaigns);

    const card = $('.launch-card[data-view="campaigns"]');
    if (card) {
      setText($('.launch-card-kicker', card), text.heroKicker);
      setText($('strong', card), hotText().launch.campaigns.title);
      setText($('p', card), hotText().launch.campaigns.desc);
    }
  }

  function localizeReportsSchedule() {
    const text = hotText().reports;
    const section = $('#view-reports .settings-section');
    if (!section) return;
    setText($('.settings-header span', section), text.scheduleTitle);
    setText($('.settings-copy', section), text.scheduleCopy);
    const deliveryType = el('report-delivery-type');
    if (deliveryType) {
      const telegramOption = deliveryType.querySelector('option[value="telegram"]');
      const emailOption = deliveryType.querySelector('option[value="email"]');
      if (telegramOption) telegramOption.textContent = text.deliveryTelegram;
      if (emailOption) emailOption.textContent = text.deliveryEmail;
      syncHotSelect(deliveryType);
    }
    setPlaceholder('#report-destination', text.destinationPlaceholder);
    setButtonLabel(section.querySelector('.btn-primary'), text.scheduleBtn);
    const reportButtons = $all('#view-reports .input-row .btn-secondary');
    setButtonLabel(reportButtons[0], text.downloadPdf);
    setButtonLabel(reportButtons[1], text.downloadCsv);
    const weekday = el('report-weekday');
    if (weekday) {
      Array.from(weekday.options).forEach(function(option, idx) {
        option.textContent = text.weekday[idx] || option.textContent;
      });
      syncHotSelect(weekday);
    }
    $all('#view-reports .settings-section thead th').forEach(function(th, idx) {
      if (typeof text.headers[idx] !== 'undefined') th.textContent = text.headers[idx];
    });
  }

  function localizeSettingsExtensions() {
    const text = hotText().settings;
    updateCurrentUserUI();
    setText('#view-settings .settings-kicker', text.heroKicker);
    setText('#view-settings .settings-hero-copy h2', text.heroTitle);
    setText('#view-settings .settings-hero-copy p', text.heroCopy);
    setText('#view-settings .settings-hero-label', text.heroSideLabel);
    setText('#view-settings .settings-hero-side strong', text.heroSideTitle);
    setText('#view-settings .settings-hero-side p', text.heroSideCopy);
    $all('#view-settings .settings-category-chip').forEach(function(chip) {
      const category = chip.dataset.settingsCategory;
      if (category && text.categories && text.categories[category]) {
        chip.textContent = text.categories[category];
      }
    });
    setText('#settings-users-title', text.usersTitle);
    setText('#settings-users-copy', text.usersCopy);
    const accessFields = $all('#view-settings [data-settings-group="access"] .settings-field > span');
    setText(accessFields[0], text.userFields.username);
    setText(accessFields[1], text.userFields.displayName);
    setText(accessFields[2], text.userFields.password);
    setText(accessFields[3], text.userFields.role);
    setPlaceholder('#dashboard-user-username', text.userFields.username);
    setPlaceholder('#dashboard-user-display-name', text.userFields.displayName);
    setPlaceholder('#dashboard-user-password', text.userFields.password);
    setButtonLabel('#view-settings [data-settings-group="access"] .btn-primary', text.createUser);
    $all('#view-settings [data-settings-group="access"] thead th').forEach(function(th, idx) {
      if (typeof text.userHeaders[idx] !== 'undefined') th.textContent = text.userHeaders[idx];
    });
    const roleSelect = el('dashboard-user-role');
    if (roleSelect && roleSelect.options.length >= 2) {
      roleSelect.options[0].textContent = text.userBadge;
      roleSelect.options[1].textContent = text.adminBadge;
      syncHotSelect(roleSelect);
    }

    setText('#settings-report-delivery-title', text.reportDeliveryTitle);
    setText('#settings-report-delivery-copy', text.reportDeliveryCopy);
    setText('#smtp-host-label', text.smtp.host);
    setText('#smtp-port-label', text.smtp.port);
    setText('#smtp-username-label', text.smtp.username);
    setText('#smtp-password-label', text.smtp.password);
    setText('#smtp-sender-label', text.smtp.sender);
    setText('#smtp-tls-label', text.smtp.tls);
    setButtonLabel('#save-report-delivery-btn', text.smtp.save);
  }

  function isAdminUser() {
    return !!(currentDashboardUser && currentDashboardUser.role === 'admin');
  }

  function updateCurrentUserUI() {
    if (!currentDashboardUser) return;
    const text = hotText().topbar;
    const displayName = currentDashboardUser.display_name || currentDashboardUser.username || '';
    const username = currentDashboardUser.username || '';
    const role = currentDashboardUser.role === 'admin' ? text.adminRole : text.userRole;
    setText('#current-user-name', displayName);
    setText('#current-user-role', role);
    setText('#logout-label', currentLang === 'en' ? 'Sign out' : 'Sair');
    const dropdownHead = $('.topbar-user-dropdown-head span');
    if (dropdownHead) dropdownHead.textContent = '@' + username;
    const avatar = el('current-user-avatar');
    if (avatar) avatar.textContent = (displayName.charAt(0) || 'U').toUpperCase();
    setText('#home-welcome', text.welcome(displayName));
  }

  function applyHotLanguage() {
    document.title = 'Painel HOT';
    localizeCampaignScreen();
    localizeReportsSchedule();
    localizeSettingsExtensions();
    syncHotLabels();
    refreshHotSelects();
  }

  const baseApplyLang = typeof applyLang === 'function' ? applyLang : null;
  window.applyLang = function() {
    if (baseApplyLang) baseApplyLang();
    applyHotLanguage();
  };

  const baseApplyThemePreset = typeof applyThemePreset === 'function' ? applyThemePreset : null;
  window.applyThemePreset = function(presetKey) {
    if (baseApplyThemePreset) baseApplyThemePreset(presetKey);
    document.documentElement.dataset.themePreset = presetKey;
    if (document.body) document.body.dataset.themePreset = presetKey;
    snapshotActiveUserCache();
  };

  const baseApplyTheme = typeof applyTheme === 'function' ? applyTheme : null;
  window.applyTheme = function(theme) {
    if (baseApplyTheme) baseApplyTheme(theme);
    document.documentElement.dataset.theme = theme;
    if (document.body) document.body.dataset.theme = theme;
    snapshotActiveUserCache();
  };

  async function persistActiveUserPreferences() {
    if (!activeDashboardUserId) return;
    snapshotActiveUserCache();
    try {
      await api('/api/users/' + encodeURIComponent(activeDashboardUserId) + '/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: currentLang,
          theme_mode: currentTheme,
          theme_preset: currentThemePreset,
        })
      });
    } catch (_) {}
  }

  window.setThemeMode = async function(mode) {
    window.applyTheme(mode === 'dark' ? 'dark' : 'light');
    if (typeof renderAppearanceControls === 'function') renderAppearanceControls();
    await persistActiveUserPreferences();
  };

  window.setThemePreset = async function(presetKey) {
    window.applyThemePreset(presetKey);
    if (typeof renderAppearanceControls === 'function') renderAppearanceControls();
    await persistActiveUserPreferences();
  };

  window.toggleTheme = async function() {
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    window.applyTheme(nextTheme);
    if (typeof renderAppearanceControls === 'function') renderAppearanceControls();
    showToast(nextTheme === 'dark' ? getUiText().notifications.themeDarkToast : getUiText().notifications.themeLightToast, 'info');
    await persistActiveUserPreferences();
  };

  window.toggleLang = async function() {
    currentLang = currentLang === 'pt' ? 'en' : 'pt';
    localStorage.setItem('lang', currentLang);
    window.applyLang();
    try {
      await window.loadActiveView(false);
    } catch (_) {}
    showToast(getUiText().notifications.langToast, 'info');
    await persistActiveUserPreferences();
  };

  window.toggleUserMenu = function() {
    const wrap = el('topbar-user-menu-wrap');
    if (!wrap) return;
    wrap.classList.toggle('is-open');
  };

  window.closeUserMenu = function() {
    const wrap = el('topbar-user-menu-wrap');
    if (wrap) wrap.classList.remove('is-open');
  };

  window.setSettingsCategory = function(categoryKey) {
    const next = categoryKey || 'appearance';
    $all('.settings-category-chip').forEach(function(chip) {
      chip.classList.toggle('is-active', chip.dataset.settingsCategory === next);
    });
    $all('#view-settings .settings-section[data-settings-group]').forEach(function(section) {
      section.style.display = section.dataset.settingsGroup === next ? '' : 'none';
    });
  };

  function renderDashboardUsersTable() {
    const tbody = el('dashboard-users-body');
    if (!tbody) return;
    const text = hotText().settings;
    tbody.innerHTML = '';
    if (!hotUsers.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted" style="padding:18px;text-align:center">' + (isAdminUser() ? text.keepOneUser : text.noPermission) + '</td></tr>';
      return;
    }
    hotUsers.forEach(function(user, index) {
      const isActive = String(user.id) === String(activeDashboardUserId);
      const canDelete = isAdminUser() && !isActive;
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + (index + 1) + '</td>' +
        '<td><strong>' + escapeHtmlSafe(user.username) + '</strong></td>' +
        '<td>' + escapeHtmlSafe(user.display_name || '-') + '</td>' +
        '<td><span class="hot-role-badge hot-role-badge--' + escapeHtmlSafe(user.role || 'user') + '">' + escapeHtmlSafe(user.role === 'admin' ? text.adminBadge : text.userBadge) + '</span></td>' +
        '<td>' + escapeHtmlSafe(user.is_active ? text.statusActive : text.statusInactive) + '</td>' +
        '<td>' + escapeHtmlSafe(user.last_login_at || '-') + '</td>' +
        '<td><div class="hot-inline-actions">' +
          '<button class="btn-secondary btn-secondary--sm is-static" type="button">' + (isActive ? text.activeBadge : (user.is_active ? text.statusActive : text.statusInactive)) + '</button>' +
          (canDelete ? '<button class="btn-danger btn-danger--sm" type="button" onclick="deleteDashboardUser(' + user.id + ')">' + text.deleteProfile + '</button>' : '') +
        '</div></td>';
      tbody.appendChild(tr);
    });
  }

  async function hydrateActiveUser(force, directPreferences) {
    if (!activeDashboardUserId) return;
    if (hotUserHydrated && !force) return;
    let prefs = directPreferences || null;
    if (!prefs) {
      try {
        prefs = await api('/api/users/' + encodeURIComponent(activeDashboardUserId) + '/preferences');
      } catch (_) {
        prefs = null;
      }
    }
    const cache = readJson(cacheKey(activeDashboardUserId), {});
    applyScopedCache(Object.assign({}, prefs || {}, cache || {}));
    if (typeof renderAppearanceControls === 'function') renderAppearanceControls();
    window.applyThemePreset(currentThemePreset || 'corporate');
    window.applyTheme(currentTheme || 'light');
    window.applyLang();
    if (typeof renderSidebarNotifications === 'function') renderSidebarNotifications();
    hotUserHydrated = true;
  }

  async function loadCurrentDashboardUser(forceHydrate) {
    try {
      const result = await api('/api/auth/me');
      currentDashboardUser = result.user || currentDashboardUser;
      activeDashboardUserId = currentDashboardUser && currentDashboardUser.id ? String(currentDashboardUser.id) : '';
      updateCurrentUserUI();
      await hydrateActiveUser(Boolean(forceHydrate), result.preferences || null);
    } catch (error) {
      console.error('loadCurrentDashboardUser', error);
      if (String(error.message).startsWith('401')) {
        window.location.href = '/login';
      }
    }
  }

  async function loadDashboardUsers(forceHydrate) {
    await loadCurrentDashboardUser(forceHydrate);
    try {
      if (!isAdminUser()) {
        hotUsers = currentDashboardUser ? [currentDashboardUser] : [];
        renderDashboardUsersTable();
        return;
      }
      hotUsers = await api('/api/users');
      renderDashboardUsersTable();
    } catch (error) {
      console.error('loadDashboardUsers', error);
      hotUsers = currentDashboardUser ? [currentDashboardUser] : [];
      renderDashboardUsersTable();
    }
  }

  window.createDashboardUser = async function() {
    const username = (el('dashboard-user-username') && el('dashboard-user-username').value || '').trim();
    const displayName = (el('dashboard-user-display-name') && el('dashboard-user-display-name').value || '').trim();
    const password = (el('dashboard-user-password') && el('dashboard-user-password').value || '').trim();
    const role = (el('dashboard-user-role') && el('dashboard-user-role').value || 'user').trim();
    const msg = el('dashboard-user-msg');
    if (!isAdminUser()) {
      if (msg) msg.textContent = hotText().settings.noPermission;
      showToast(hotText().settings.noPermission, 'warning');
      return;
    }
    if (!username || !password) {
      if (msg) msg.textContent = hotText().settings.fillUser;
      showToast(hotText().settings.fillUser, 'warning');
      return;
    }
    try {
      const result = await api('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username, display_name: displayName, password: password, role: role })
      });
      if (el('dashboard-user-username')) el('dashboard-user-username').value = '';
      if (el('dashboard-user-display-name')) el('dashboard-user-display-name').value = '';
      if (el('dashboard-user-password')) el('dashboard-user-password').value = '';
      if (msg) msg.textContent = hotText().settings.createdUser;
      showToast(hotText().settings.createdUser, 'success');
      await loadDashboardUsers(false);
    } catch (error) {
      if (msg) msg.textContent = error.message;
      showToast(error.message, 'error');
    }
  };

  window.deleteDashboardUser = async function(userId) {
    if (!isAdminUser()) {
      showToast(hotText().settings.noPermission, 'warning');
      return;
    }
    const user = hotUsers.find(function(item) { return String(item.id) === String(userId); });
    const label = user ? (user.display_name || user.username) : String(userId);
    if (!confirm(hotText().settings.deleteProfileConfirm(label))) return;
    try {
      await api('/api/users/' + encodeURIComponent(userId), { method: 'DELETE' });
      showToast(hotText().settings.removedUser, 'success');
      await loadDashboardUsers(false);
    } catch (error) {
      showToast(error.message || hotText().settings.keepOneUser, 'warning');
    }
  };

  async function loadReportDeliverySettings() {
    try {
      const settings = await api('/api/settings');
      const delivery = settings.report_delivery || {};
      if (el('smtp-host')) el('smtp-host').value = delivery.smtp_host || '';
      if (el('smtp-port')) el('smtp-port').value = delivery.smtp_port || '587';
      if (el('smtp-username')) el('smtp-username').value = delivery.smtp_username || '';
      if (el('smtp-password')) el('smtp-password').value = '';
      if (el('smtp-sender')) el('smtp-sender').value = delivery.smtp_sender || '';
      if (el('smtp-tls')) el('smtp-tls').checked = String(delivery.smtp_tls || '1') !== '0';
    } catch (error) {
      console.error('loadReportDeliverySettings', error);
    }
  }

  window.saveReportDeliverySettings = async function() {
    const payload = {
      smtp_host: el('smtp-host') ? el('smtp-host').value.trim() : '',
      smtp_port: el('smtp-port') ? el('smtp-port').value.trim() : '587',
      smtp_username: el('smtp-username') ? el('smtp-username').value.trim() : '',
      smtp_password: el('smtp-password') ? el('smtp-password').value.trim() : '',
      smtp_sender: el('smtp-sender') ? el('smtp-sender').value.trim() : '',
      smtp_tls: el('smtp-tls') && el('smtp-tls').checked ? '1' : '0'
    };
    try {
      await api('/api/settings/report-delivery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (el('report-delivery-msg')) el('report-delivery-msg').textContent = hotText().reports.deliveryUpdated;
      if (el('smtp-password')) el('smtp-password').value = '';
      showToast(hotText().reports.deliveryUpdated, 'success');
    } catch (error) {
      if (el('report-delivery-msg')) el('report-delivery-msg').textContent = error.message;
      showToast(error.message, 'error');
    }
  };

  function formatCampaignType(type) {
    const map = hotText().campaigns.types;
    return map[String(type || '').toLowerCase()] || type || '-';
  }

  function renderCampaignSelects(sources, members) {
    const sourceSelect = el('campaign-origin-select');
    const memberSelect = el('campaign-member-select');
    if (sourceSelect) {
      sourceSelect.innerHTML = sources.length
        ? sources.map(function(source) {
            return '<option value="' + source.id + '">' + escapeHtmlSafe(source.name) + '</option>';
          }).join('')
        : '<option value="">' + (currentLang === 'en' ? 'No source' : 'Sem origem') + '</option>';
    }
    if (memberSelect) {
      memberSelect.innerHTML = members.length
        ? members.map(function(member) {
            const label = member.username ? '@' + member.username : (member.full_name || String(member.user_id));
            return '<option value="' + member.user_id + '">' + escapeHtmlSafe(label) + '</option>';
          }).join('')
        : '<option value="">' + (currentLang === 'en' ? 'No member' : 'Sem membro') + '</option>';
    }
    refreshHotSelects();
  }

  function renderCampaignReport(report) {
    const tbody = el('campaign-report-body');
    if (!tbody) return;
    const text = hotText().campaigns;
    tbody.innerHTML = '';
    if (!report.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="muted" style="padding:18px;text-align:center">' + text.empty.report + '</td></tr>';
      return;
    }
    report.forEach(function(row) {
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td><strong>' + escapeHtmlSafe(row.name) + '</strong></td>' +
        '<td>' + escapeHtmlSafe(formatCampaignType(row.source_type)) + '</td>' +
        '<td>' + (row.joined_members || 0) + '</td>' +
        '<td>' + (row.left_members || 0) + '</td>' +
        '<td>' + (row.assigned_members || 0) + '</td>' +
        '<td>' + money(row.cost_amount || 0) + '</td>' +
        '<td>' + money(row.cost_per_member || 0) + '</td>' +
        '<td><button class="btn-danger btn-danger--sm" type="button" onclick="deleteCampaignSource(' + row.id + ')">' + text.buttons.deleteSource + '</button></td>';
      tbody.appendChild(tr);
    });
  }

  function renderCampaignAssignments(rows) {
    const tbody = el('campaign-assignments-body');
    if (!tbody) return;
    const text = hotText().campaigns;
    tbody.innerHTML = '';
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="muted" style="padding:18px;text-align:center">' + text.empty.assignments + '</td></tr>';
      return;
    }
    rows.forEach(function(row, index) {
      const label = row.username ? '@' + row.username : (row.full_name || String(row.user_id));
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + (index + 1) + '</td>' +
        '<td>' + escapeHtmlSafe(label) + '</td>' +
        '<td>' + escapeHtmlSafe(row.source_name || '-') + '</td>' +
        '<td>' + escapeHtmlSafe(formatCampaignType(row.source_type)) + '</td>' +
        '<td>' + escapeHtmlSafe(row.assigned_at || '-') + '</td>' +
        '<td><button class="btn-secondary btn-secondary--sm" type="button" onclick="deleteCampaignAssignment(' + row.id + ')">' + text.buttons.deleteAssignment + '</button></td>';
      tbody.appendChild(tr);
    });
  }

  function updateCampaignSummary(sources, reportRows) {
    setText('#campaigns-summary-title', hotText().campaigns.summaryTitle);
    if (!sources.length) {
      setText('#campaigns-summary-copy', hotText().campaigns.summaryCopy);
      return;
    }
    const totalCost = reportRows.reduce(function(sum, row) { return sum + Number(row.cost_amount || 0); }, 0);
    const totalMembers = reportRows.reduce(function(sum, row) { return sum + Number(row.assigned_members || 0); }, 0);
    const copy = currentLang === 'en'
      ? sources.length + ' active sources with ' + totalMembers + ' tagged members and ' + money(totalCost) + ' in total spend.'
      : sources.length + ' origens ativas com ' + totalMembers + ' membros marcados e ' + money(totalCost) + ' de investimento total.';
    setText('#campaigns-summary-copy', copy);
  }

  async function loadCampaigns() {
    const text = hotText().campaigns;
    if (!chatId) {
      renderCampaignSelects([], []);
      renderCampaignReport([]);
      renderCampaignAssignments([]);
      setText('#campaigns-summary-copy', text.selectGroup);
      return;
    }
    const safeChatId = encodeURIComponent(chatId);
    try {
      const payload = await Promise.all([
        api('/api/campaigns/sources/' + safeChatId),
        api('/api/campaigns/assignments/' + safeChatId),
        api('/api/campaigns/report/' + safeChatId),
        api('/api/members/' + safeChatId),
      ]);
      const sources = payload[0] || [];
      const assignments = payload[1] || [];
      const reportRows = payload[2] || [];
      const memberPayload = payload[3] || {};
      const members = memberPayload.members || [];
      renderCampaignSelects(sources, members);
      renderCampaignReport(reportRows);
      renderCampaignAssignments(assignments);
      updateCampaignSummary(sources, reportRows);
    } catch (error) {
      showToast(error.message, 'error');
    }
  }

  window.saveCampaignSource = async function() {
    if (!chatId) {
      showToast(hotText().campaigns.selectGroup, 'warning');
      return;
    }
    const name = (el('campaign-source-name') && el('campaign-source-name').value || '').trim();
    if (!name) {
      showToast(hotText().campaigns.requiredSource, 'warning');
      return;
    }
    const payload = {
      chat_id: Number(chatId),
      name: name,
      source_type: el('campaign-source-type') ? el('campaign-source-type').value : 'campaign',
      cost_amount: el('campaign-source-cost') ? el('campaign-source-cost').value : '0',
      notes: el('campaign-source-notes') ? el('campaign-source-notes').value.trim() : ''
    };
    try {
      await api('/api/campaigns/sources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (el('campaign-source-name')) el('campaign-source-name').value = '';
      if (el('campaign-source-cost')) el('campaign-source-cost').value = '';
      if (el('campaign-source-notes')) el('campaign-source-notes').value = '';
      showToast(hotText().campaigns.savedSource, 'success');
      await loadCampaigns();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  window.assignCampaignOrigin = async function() {
    if (!chatId) {
      showToast(hotText().campaigns.selectGroup, 'warning');
      return;
    }
    const userId = el('campaign-member-select') ? el('campaign-member-select').value : '';
    const sourceId = el('campaign-origin-select') ? el('campaign-origin-select').value : '';
    if (!userId || !sourceId) {
      showToast(hotText().campaigns.requiredAssignment, 'warning');
      return;
    }
    try {
      await api('/api/campaigns/assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: Number(chatId),
          user_id: Number(userId),
          source_id: Number(sourceId)
        })
      });
      showToast(hotText().campaigns.savedAssignment, 'success');
      await loadCampaigns();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  window.deleteCampaignSource = async function(sourceId) {
    try {
      await api('/api/campaigns/sources/' + encodeURIComponent(sourceId), { method: 'DELETE' });
      showToast(hotText().campaigns.removedSource, 'success');
      await loadCampaigns();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  window.deleteCampaignAssignment = async function(assignmentId) {
    try {
      await api('/api/campaigns/assignments/' + encodeURIComponent(assignmentId), { method: 'DELETE' });
      showToast(hotText().campaigns.removedAssignment, 'success');
      await loadCampaigns();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  async function loadReportSchedules() {
    const tbody = el('report-schedules-body');
    if (!tbody) return;
    const text = hotText().reports;
    if (!chatId) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted" style="padding:18px;text-align:center">' + hotText().campaigns.selectGroup + '</td></tr>';
      return;
    }
    try {
      const rows = await api('/api/reports/schedules?chat_id=' + encodeURIComponent(chatId));
      tbody.innerHTML = '';
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="muted" style="padding:18px;text-align:center">' + text.empty + '</td></tr>';
        return;
      }
      rows.forEach(function(row, index) {
        const weekdayName = text.weekday[Number(row.weekday) || 0] || '-';
        const time = String(row.hour).padStart(2, '0') + ':' + String(row.minute).padStart(2, '0');
        const tr = document.createElement('tr');
        tr.innerHTML =
          '<td>' + (index + 1) + '</td>' +
          '<td>' + escapeHtmlSafe(row.delivery_type === 'email' ? text.deliveryEmail : text.deliveryTelegram) + '</td>' +
          '<td>' + escapeHtmlSafe(row.destination || '-') + '</td>' +
          '<td>' + String(row.format || '').toUpperCase() + '</td>' +
          '<td>' + escapeHtmlSafe(text.at({ day: weekdayName, hour: time })) + '</td>' +
          '<td>' + escapeHtmlSafe(row.last_sent_at || '-') + '</td>' +
          '<td><div class="hot-inline-actions">' +
            '<button class="btn-secondary btn-secondary--sm" type="button" onclick="downloadReportNow(\'' + String(row.format || 'pdf') + '\')">' + text.sendNow + '</button>' +
            '<button class="btn-danger btn-danger--sm" type="button" onclick="deleteReportSchedule(' + row.id + ')">' + text.remove + '</button>' +
          '</div></td>';
        tbody.appendChild(tr);
      });
    } catch (error) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted" style="padding:18px;text-align:center">' + escapeHtmlSafe(error.message) + '</td></tr>';
    }
  }

  window.saveReportSchedule = async function() {
    if (!chatId) {
      showToast(hotText().campaigns.selectGroup, 'warning');
      return;
    }
    const timeValue = el('report-time') ? el('report-time').value : '09:00';
    const parts = String(timeValue || '09:00').split(':');
    const payload = {
      chat_id: Number(chatId),
      delivery_type: el('report-delivery-type') ? el('report-delivery-type').value : 'telegram',
      destination: el('report-destination') ? el('report-destination').value.trim() : '',
      format: el('report-format') ? el('report-format').value : 'pdf',
      weekday: el('report-weekday') ? Number(el('report-weekday').value) : 0,
      hour: Number(parts[0] || 9),
      minute: Number(parts[1] || 0)
    };
    try {
      await api('/api/reports/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (el('report-schedule-msg')) el('report-schedule-msg').textContent = hotText().reports.scheduleSaved;
      showToast(hotText().reports.scheduleSaved, 'success');
      await loadReportSchedules();
    } catch (error) {
      if (el('report-schedule-msg')) el('report-schedule-msg').textContent = error.message;
      showToast(error.message, 'error');
    }
  };

  window.deleteReportSchedule = async function(reportId) {
    try {
      await api('/api/reports/schedules/' + encodeURIComponent(reportId), { method: 'DELETE' });
      await loadReportSchedules();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  window.downloadReportNow = async function(format) {
    if (String(format).toLowerCase() === 'csv') return exportCSV();
    return exportPDF();
  };

  const baseLoadSettings = typeof loadSettings === 'function' ? loadSettings : null;
  window.loadSettings = async function() {
    if (baseLoadSettings) await baseLoadSettings();
    await Promise.allSettled([loadDashboardUsers(false), loadReportDeliverySettings()]);
    applyHotLanguage();
    refreshHotSelects();
  };

  const baseLoadActiveView = typeof loadActiveView === 'function' ? loadActiveView : null;
  window.loadActiveView = async function(forceOverviewSkeleton) {
    if (activeView === 'campaigns') return loadCampaigns();
    const result = baseLoadActiveView ? await baseLoadActiveView(forceOverviewSkeleton) : undefined;
    if (activeView === 'reports') await loadReportSchedules();
    if (activeView === 'settings') await Promise.allSettled([loadDashboardUsers(false), loadReportDeliverySettings()]);
    refreshHotSelects();
    return result;
  };

  try {
    LOADERS.campaigns = loadCampaigns;
    LOADERS.settings = window.loadSettings;
  } catch (_) {}

  function wrapCacheOnly(fnName) {
    const original = window[fnName];
    if (typeof original !== 'function') return;
    window[fnName] = function() {
      const result = original.apply(this, arguments);
      if (result && typeof result.then === 'function') {
        return result.finally(snapshotActiveUserCache);
      }
      snapshotActiveUserCache();
      return result;
    };
  }

  wrapCacheOnly('pushNotificationItem');
  wrapCacheOnly('clearNotifications');
  wrapCacheOnly('saveGoals');
  wrapCacheOnly('resetGoals');

  function initHotDock() {
    const track = el('view-rail-track');
    if (!track) return;
    const chips = $all('.view-chip', track);
    if (!chips.length) return;
    const clear = function() {
      chips.forEach(function(chip) {
        chip.style.removeProperty('--dock-scale');
      });
    };
    track.addEventListener('pointermove', function(event) {
      chips.forEach(function(chip) {
        const rect = chip.getBoundingClientRect();
        const center = rect.left + rect.width / 2;
        const distance = Math.abs(event.clientX - center);
        const influence = Math.max(0, 1 - (distance / 130));
        const scale = 0.92 + (influence * 0.5);
        chip.style.setProperty('--dock-scale', scale.toFixed(3));
      });
    });
    track.addEventListener('pointerleave', clear);
    track.addEventListener('mouseleave', clear);
  }

  document.addEventListener('DOMContentLoaded', function() {
    if (typeof reorderViewCollections === 'function') reorderViewCollections();
    if (typeof renderLaunchCards === 'function') renderLaunchCards();
    initHotDock();
    window.setSettingsCategory('appearance');
    window.applyThemePreset(currentThemePreset || 'corporate');
    window.applyTheme(currentTheme || 'light');
    window.applyLang();
    loadDashboardUsers(true);
    loadReportDeliverySettings();
    if (activeView === 'reports') loadReportSchedules();
    if (activeView === 'campaigns') loadCampaigns();
    refreshHotSelects();
    window.addEventListener('beforeunload', snapshotActiveUserCache);
    document.addEventListener('click', function(event) {
      const wrap = el('topbar-user-menu-wrap');
      if (wrap && !wrap.contains(event.target)) wrap.classList.remove('is-open');
      if (!event.target.closest('.hot-select')) closeAllHotSelects();
    });
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') window.closeUserMenu();
      if (event.key === 'Escape') closeAllHotSelects();
    });
  });
})();
