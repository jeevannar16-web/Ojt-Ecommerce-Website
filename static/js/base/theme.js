// ==============================================================================
// File: theme.js
// Description: 13-theme picker — 8 solid dark + 5 animated premium.
// Uses data-global-theme to avoid conflict with chat's data-theme system.
// ==============================================================================

(function() {
  var STORAGE_KEY = 'fitnesshub_theme';
  var ATTR = 'data-global-theme';
  var html = document.documentElement;
  var metaColorScheme = document.querySelector('meta[name="color-scheme"]');

  var THEMES = [
    // System
    { id: 'system',    label: 'System Default', icon: '💻', color: '#1a1a2e' },
    // Solid Dark
    { id: 'obsidian',  label: 'Obsidian',  icon: '🌑', color: '#08080c' },
    { id: 'midnight',  label: 'Midnight',  icon: '🌃', color: '#080c1a' },
    { id: 'forest',    label: 'Forest',    icon: '🌲', color: '#070e08' },
    { id: 'wine',      label: 'Wine',      icon: '🍷', color: '#100608' },
    { id: 'plum',      label: 'Plum',      icon: '🟣', color: '#0e0614' },
    { id: 'slate',     label: 'Slate',      icon: '🪨', color: '#0c0e12' },
    { id: 'charcoal',  label: 'Charcoal',  icon: '🖤', color: '#14151a' },
    { id: 'copper',    label: 'Copper',    icon: '🔶', color: '#120e0a' },
    // Animated
    { id: 'aurora',    label: 'Aurora',    icon: '🌌', color: '#060a12' },
    { id: 'galaxy',    label: 'Galaxy',    icon: '✨', color: '#04040a' },
    { id: 'sunset',    label: 'Sunset',    icon: '🌅', color: '#120804' },
    { id: 'nebula',    label: 'Nebula',    icon: '🌠', color: '#08040e' },
    { id: 'starlight', label: 'Starlight', icon: '⭐', color: '#0c0806' },
  ];

  function updateBtnIcon(themeId) {
    var btn = document.getElementById('theme-picker-btn');
    if (!btn) return;
    var t = THEMES.find(function(x) { return x.id === themeId; }) || THEMES[1];
    btn.innerHTML = '<span class="tp-btn-icon">' + t.icon + '</span><span class="tp-btn-label">Theme</span>';
  }

  function applyTheme(themeId) {
    if (themeId === 'system') {
      html.removeAttribute(ATTR);
      localStorage.removeItem(STORAGE_KEY);
    } else {
      html.setAttribute(ATTR, themeId);
      localStorage.setItem(STORAGE_KEY, themeId);
    }
    metaColorScheme.content = 'only dark';
    updateBtnIcon(themeId);
    var picker = document.getElementById('theme-picker-dropdown');
    if (picker) picker.classList.remove('open');
  }

  // Restore saved theme
  var saved = localStorage.getItem(STORAGE_KEY);
  if (saved && THEMES.some(function(t) { return t.id === saved; })) {
    applyTheme(saved);
  }

  // Setup picker
  var btn = document.getElementById('theme-picker-btn');
  var picker = document.getElementById('theme-picker-dropdown');
  if (btn && picker) {
    var cur = html.getAttribute(ATTR) || 'obsidian';
    updateBtnIcon(cur);

    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      picker.classList.toggle('open');
    });

    function addSep(label) {
      var sep = document.createElement('div');
      sep.className = 'tp-sep';
      sep.textContent = label;
      picker.appendChild(sep);
    }
    var lastCat = '';
    THEMES.forEach(function(theme, idx) {
      var cat = idx === 0 ? 'system' : (idx <= 8 ? 'solid' : 'animated');
      if (cat !== lastCat && idx > 0) { addSep(cat === 'solid' ? '— Solid —' : '— Animated —'); }
      lastCat = cat;
      var opt = document.createElement('div');
      opt.className = 'tp-opt' + (theme.id === cur ? ' tp-active' : '');
      opt.setAttribute('data-theme-id', theme.id);
      opt.innerHTML = '<span class="tp-opt-swatch" style="background:' + theme.color + '"></span><span class="tp-opt-icon">' + theme.icon + '</span><span class="tp-opt-label">' + theme.label + '</span>';
      opt.addEventListener('click', function() {
        applyTheme(theme.id);
        picker.querySelectorAll('.tp-opt').forEach(function(o) { o.classList.remove('tp-active'); });
        opt.classList.add('tp-active');
        updateBtnIcon(theme.id);
      });
      picker.appendChild(opt);
    });

    document.addEventListener('click', function(e) {
      if (!btn.contains(e.target) && !picker.contains(e.target)) {
        picker.classList.remove('open');
      }
    });
  }
})();
