// cookie_consent.js — premium cookie consent with overlay, modal preferences, and reminder banner

// ==============================================================================
// SECTION: Configuration & State
// ==============================================================================

(function(){
  'use strict';

  var STORAGE_KEY = 'fithub_cookie_consent';
  var CONSENT_VERSION = 2;
  var REMINDER_DELAY = 5000;
  var REMINDER_DURATION = 8000;

  var defaults = {
    essential: true,
    functional: false,
    analytics: false,
    marketing: false
  };

  var overlay, modalOverlay, toast, reminder;
  var dismissed = false;
  var reminderTimer = null;
  var reminderHideTimer = null;





  // ==============================================================================
  // SECTION: Storage Operations
  // ==============================================================================

  function getConsent(){
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if(!raw) return null;
      var data = JSON.parse(raw);
      if(data.version !== CONSENT_VERSION) return null;
      return data.choices;
    } catch(e){ return null; }
  }

  function setConsent(choices, action){
    var data = {
      version: CONSENT_VERSION,
      timestamp: Date.now(),
      action: action,
      choices: choices
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    applyConsent(choices);
    dismissOverlay(action);
  }



  // ==============================================================================
  // SECTION: Consent Application
  // ==============================================================================

  function applyConsent(choices){
    if(choices.analytics){
      document.documentElement.removeAttribute('data-analytics-off');
    } else {
      document.documentElement.setAttribute('data-analytics-off', '1');
    }
    if(choices.marketing){
      document.documentElement.removeAttribute('data-marketing-off');
    } else {
      document.documentElement.setAttribute('data-marketing-off', '1');
    }
    if(choices.functional){
      document.documentElement.removeAttribute('data-functional-off');
    } else {
      document.documentElement.setAttribute('data-functional-off', '1');
    }
  }



  // ==============================================================================
  // SECTION: UI Management
  // ==============================================================================

  function dismissOverlay(action){
    if(dismissed) return;
    dismissed = true;
    overlay = document.getElementById('cc-overlay');
    if(!overlay) return;
    overlay.classList.add('dismissing');
    setTimeout(function(){
      overlay.style.display = 'none';
      showToast(action);
    }, 350);
  }

  function showToast(action){
    toast = document.getElementById('cc-toast');
    if(!toast) return;
    var msgEl = toast.querySelector('.cc-toast-msg');
    if(!msgEl) return;
    var msgs = {
      accept: 'All cookies accepted. Your privacy preferences are saved.',
      reject: 'Only essential cookies are active. You can change this anytime.',
      customize: 'Your cookie preferences have been saved.'
    };
    msgEl.textContent = msgs[action] || 'Cookie preferences saved.';
    toast.classList.add('show');
    setTimeout(function(){ toast.classList.remove('show'); }, 4000);
  }

  function showReminder(){
    reminder = document.getElementById('cc-reminder');
    if(!reminder) return;
    if(reminder.classList.contains('show')) return;
    reminder.classList.add('show');
    if(reminderHideTimer) clearTimeout(reminderHideTimer);
    reminderHideTimer = setTimeout(function(){
      reminder.classList.remove('show');
    }, REMINDER_DURATION);
  }

  function hideReminder(){
    reminder = document.getElementById('cc-reminder');
    if(!reminder) return;
    reminder.classList.remove('show');
    if(reminderHideTimer) clearTimeout(reminderHideTimer);
  }

  function scheduleReminder(){
    if(reminderTimer) clearTimeout(reminderTimer);
    reminderTimer = setTimeout(showReminder, REMINDER_DELAY);
  }



  // ==============================================================================
  // SECTION: Customization Modal
  // ==============================================================================

  function openCustomize(){
    modalOverlay = document.getElementById('cc-modal-overlay');
    if(!modalOverlay) return;
    var current = getConsent() || defaults;
    for(var key in current){
      var el = document.getElementById('cc-' + key);
      if(el) el.checked = current[key];
    }
    modalOverlay.classList.add('open');
  }

  function closeCustomize(){
    if(modalOverlay) modalOverlay.classList.remove('open');
  }

  function saveCustomize(){
    var choices = {};
    for(var key in defaults){
      var el = document.getElementById('cc-' + key);
      choices[key] = el ? el.checked : defaults[key];
    }
    choices.essential = true;
    setConsent(choices, 'customize');
    closeCustomize();
  }



  // ==============================================================================
  // SECTION: Event Binding
  // ==============================================================================

  function bindModalButtons(){
    var saveBtn = document.getElementById('cc-save');
    if(saveBtn) saveBtn.addEventListener('click', saveCustomize);

    var cancelBtn = document.getElementById('cc-cancel');
    if(cancelBtn) cancelBtn.addEventListener('click', closeCustomize);

    var modOverlay = document.getElementById('cc-modal-overlay');
    if(modOverlay){
      modOverlay.addEventListener('click', function(e){
        if(e.target === this) closeCustomize();
      });
    }

    var reminderLink = document.getElementById('cc-reminder-link');
    if(reminderLink){
      reminderLink.addEventListener('click', function(e){
        e.preventDefault();
        hideReminder();
        openCustomize();
        var modal = document.querySelector('.cc-modal');
        if(modal) modal.scrollTop = 0;
      });
    }

    var reminderClose = document.getElementById('cc-reminder-close');
    if(reminderClose){
      reminderClose.addEventListener('click', hideReminder);
    }
  }



  // ==============================================================================
  // SECTION: Initialization
  // ==============================================================================

  function init(){
    bindModalButtons();

    var existing = getConsent();
    if(existing){
      overlay = document.getElementById('cc-overlay');
      if(overlay) overlay.style.display = 'none';
      applyConsent(existing);
      scheduleReminder();
      return;
    }

    overlay = document.getElementById('cc-overlay');
    if(!overlay) return;
    overlay.style.display = 'flex';

    var acceptBtn = document.getElementById('cc-accept');
    if(acceptBtn){
      acceptBtn.addEventListener('click', function(){
        setConsent({essential: true, functional: true, analytics: true, marketing: true}, 'accept');
      });
    }

    var rejectBtn = document.getElementById('cc-reject');
    if(rejectBtn){
      rejectBtn.addEventListener('click', function(){
        setConsent({essential: true, functional: false, analytics: false, marketing: false}, 'reject');
      });
    }

    var customizeBtn = document.getElementById('cc-customize');
    if(customizeBtn){
      customizeBtn.addEventListener('click', function(e){
        e.preventDefault();
        openCustomize();
      });
    }
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
