// profile.js — tab switching with URL hash so the active tab survives page reload

// ==============================================================================
// SECTION: Tab Activation
// ==============================================================================

(function(){
  var tabs = document.querySelectorAll('.profile-tab');
  var panels = document.querySelectorAll('.tab-panel');

  function activateTab(tabId) {
    tabs.forEach(function(t){ t.classList.remove('active'); });
    panels.forEach(function(p){ p.classList.remove('active'); });
    var tab = document.querySelector('.profile-tab[data-tab="' + tabId + '"]');
    var panel = document.getElementById('tab-' + tabId);
    if (tab) tab.classList.add('active');
    if (panel) panel.classList.add('active');
  }

  tabs.forEach(function(tab){
    tab.addEventListener('click', function(e){
      e.preventDefault();
      var tabId = this.getAttribute('data-tab');
      activateTab(tabId);
      var url = new URL(window.location);
      url.searchParams.set('tab', tabId);
      window.history.replaceState({}, '', url);
    });
  });

  var hash = new URL(window.location).searchParams.get('tab');
  if (hash && document.querySelector('.profile-tab[data-tab="' + hash + '"]')) {
    activateTab(hash);
  }
})();
