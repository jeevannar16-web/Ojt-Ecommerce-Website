// ==============================================================================
// File: newsletter.js
// Description: AJAX newsletter subscription with validation and feedback
// ==============================================================================

// ==============================================================================
// SECTION: DOM References & Validation
// ==============================================================================

(function() {
  const form = document.getElementById('ajax-newsletter-form');
  const input = document.getElementById('newsletter-email-input');
  const btn = document.getElementById('newsletter-submit-btn');
  const errEl = document.getElementById('nl-error');
  if (!form || !input) return;

  const emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;



  // ==============================================================================
  // SECTION: Input Validation
  // ==============================================================================

  input.addEventListener('input', function() {
    if (errEl) errEl.style.display = 'none';
    input.style.borderColor = '#2a2a2a';
  });





  // ==============================================================================
  // SECTION: Form Submission
  // ==============================================================================

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const email = input.value.trim().toLowerCase();

    if (!email) {
      if (errEl) { errEl.textContent = 'Email is required'; errEl.style.display = 'block'; }
      input.style.borderColor = '#ef4444';
      return;
    }
    if (!emailRegex.test(email)) {
      if (errEl) { errEl.textContent = 'Enter a valid email (e.g. yourname@gmail.com)'; errEl.style.display = 'block'; }
      input.style.borderColor = '#ef4444';
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Sending...';

    fetch('/store/newsletter/subscribe/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({ email: email })
    })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'success') {
        input.value = '';
        showToast(data.message || '✓ Subscribed successfully!');
      } else if (data.status === 'info') {
        showToast(data.message || 'You are already subscribed!');
      } else {
        if (errEl) { errEl.textContent = data.message || 'Subscription failed'; errEl.style.display = 'block'; }
        input.style.borderColor = '#ef4444';
      }
    })
    .catch(() => {
      showToast('Network error. Please try again.', true);
    })
    .finally(() => {
      btn.disabled = false;
      btn.textContent = 'Subscribe';
    });
  });
})();
