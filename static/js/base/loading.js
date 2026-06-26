// loading.js — page preloader spinner, offline connection banner, and nav transition feedback

(function () {
  var bar = document.getElementById('page-loader');
  var logo = document.getElementById('loader-logo');
  var banner = document.getElementById('offline-banner');
  if (!bar) return;

  var timer = null;

  // ==============================================================================
  // SECTION: Loader Show/Hide Functions
  // ==============================================================================

  function show() {
    bar.classList.add('active');
    if (logo) logo.classList.add('active');
  }
  function hide() {
    bar.classList.remove('active');
    if (logo) logo.classList.remove('active');
  }
  function showDelayed(delay) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(show, delay || 200);
  }





  // ==============================================================================
  // SECTION: Page Lifecycle Events
  // ==============================================================================

  if (document.readyState === 'loading') show();
  document.addEventListener('DOMContentLoaded', function () { setTimeout(hide, 500); });
  window.addEventListener('beforeunload', show);
  window.addEventListener('pageshow', function (e) { if (e.persisted) setTimeout(hide, 250); });





  // ==============================================================================
  // SECTION: Navigation Click Handler
  // ==============================================================================

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;
    var h = link.getAttribute('href');
    if (!h || h.startsWith('#') || h.startsWith('javascript') || h.startsWith('tel:') || h.startsWith('mailto:')) return;
    if (link.hasAttribute('download') || link.target === '_blank') return;
    if (!(h.startsWith('/') || h.startsWith(window.location.origin))) return;
    showDelayed(250);
  });





  // ==============================================================================
  // SECTION: Form Submit Handler
  // ==============================================================================

  document.addEventListener('submit', function (e) {
    if (e.target.getAttribute('data-no-loader') === 'true') return;
    showDelayed(150);
  });





  // ==============================================================================
  // SECTION: Offline Detection
  // ==============================================================================

  if (navigator.onLine === false && banner) banner.style.display = 'flex';
  window.addEventListener('offline', function () { if (banner) banner.style.display = 'flex'; });
  window.addEventListener('online', function () { if (banner) banner.style.display = 'none'; });
})();
