(function () {
  var bar = document.getElementById('page-loader');
  var logo = document.getElementById('loader-logo');
  var banner = document.getElementById('offline-banner');
  if (!bar) return;

  var timer = null;
  var loaded = false;

  function show() {
    bar.classList.add('active');
    if (logo) logo.classList.add('active');
  }
  function hide() {
    loaded = true;
    bar.classList.remove('active');
    if (logo) logo.classList.remove('active');
  }
  function showDelayed(delay) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function() {
      if (!loaded) show();
    }, delay || 200);
  }

  if (document.readyState === 'loading') show();
  document.addEventListener('DOMContentLoaded', function () {
    setTimeout(hide, 400);
  });
  window.addEventListener('beforeunload', function() {
    loaded = false;
    show();
  });
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) { loaded = false; setTimeout(hide, 250); }
  });

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;
    var h = link.getAttribute('href');
    if (!h || h.startsWith('#') || h.startsWith('javascript') || h.startsWith('tel:') || h.startsWith('mailto:')) return;
    if (link.hasAttribute('download') || link.target === '_blank') return;
    if (!(h.startsWith('/') || h.startsWith(window.location.origin))) return;
    loaded = false;
    show();
  });

  document.addEventListener('submit', function (e) {
    if (e.target.getAttribute('data-no-loader') === 'true') return;
    loaded = false;
    show();
  });

  if (navigator.onLine === false && banner) banner.style.display = 'flex';
  window.addEventListener('offline', function () { if (banner) banner.style.display = 'flex'; });
  window.addEventListener('online', function () { if (banner) banner.style.display = 'none'; });
})();
