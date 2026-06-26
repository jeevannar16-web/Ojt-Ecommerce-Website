// ==============================================================================
// File: main.js
// Description: Search validation, CSRF cookie, toast notifications, back-to-top
// ==============================================================================

// ==============================================================================
// SECTION: Search Validation
// ==============================================================================

function validateSearch() {
  const input = document.getElementById('search-input');
  if (!input.value.trim()) {
    input.style.borderColor = '#ef4444';
    input.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.15)';
    setTimeout(() => {
      input.style.borderColor = '#333';
      input.style.boxShadow = 'none';
    }, 1500);
    return false;
  }
  return true;
}





// ==============================================================================
// SECTION: Cookie Utility
// ==============================================================================

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}





// ==============================================================================
// SECTION: Toast Notification
// ==============================================================================

function showToast(message, isError = false) {
  const container = document.getElementById('single-toast-container');
  if (!container) { alert(message); return; }
  const toast = document.createElement('div');
  toast.className = 'custom-animated-toast theme-' + (isError ? 'warning' : 'success');
  toast.innerHTML = '<span>' + message + '</span>';
  container.appendChild(toast);
  setTimeout(() => toast.classList.add('reveal-slide'), 10);
  setTimeout(() => {
    toast.style.transition = 'all 0.4s ease';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 400);
  }, 2600);
}





// ==============================================================================
// SECTION: Back to Top Button
// ==============================================================================

(function () {
  const btn = document.getElementById('btt-btn');
  if (!btn) return;
  const arc = btn.querySelector('.btt-arc-fill');
  const CIRCUM = 119.4;
  function updateScroll() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docH > 0 ? Math.min(scrollTop / docH, 1) : 0;
    if (scrollTop > window.innerHeight * 0.3) {
      btn.classList.add('btt-visible');
    } else {
      btn.classList.remove('btt-visible');
    }
    if (arc) arc.style.strokeDashoffset = CIRCUM * (1 - pct);
  }
  window.addEventListener('scroll', updateScroll, { passive: true });
  btn.addEventListener('click', function () {
    btn.style.transition = 'transform 0.15s ease';
    btn.style.transform = 'translateY(4px) scale(0.94)';
    setTimeout(() => { btn.style.transition = ''; btn.style.transform = ''; }, 150);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  updateScroll();
})();
