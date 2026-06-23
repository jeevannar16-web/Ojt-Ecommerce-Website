(function () {
  /* ── Click-toggle dropdowns (lang + user) — delegated ── */
  function toggleDropdown(btn) {
    var container = btn.closest('.nav-lang, .user-dropdown');
    if (!container) return;
    var isOpen = container.classList.contains('open');
    document.querySelectorAll('.nav-lang.open, .user-dropdown.open').forEach(function (el) {
      if (el !== container) el.classList.remove('open');
    });
    container.classList.toggle('open', !isOpen);
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.nav-lang-btn, .user-dropdown > .nav-icon-btn');
    if (btn) { e.stopPropagation(); toggleDropdown(btn); return; }
    var inside = e.target.closest('.nav-lang-drop, .dropdown-content');
    if (inside) return;
    document.querySelectorAll('.nav-lang.open, .user-dropdown.open').forEach(function (el) {
      el.classList.remove('open');
    });
  });

  const track = document.getElementById('elite-nav-track');
  const inner = document.getElementById('elite-nav-inner');
  const prev  = document.getElementById('nav-prev');
  const next  = document.getElementById('nav-next');
  if (!track) return;
  const STEP = 300;
  function sync() {
    const atStart = track.scrollLeft < 4;
    const atEnd   = track.scrollLeft > track.scrollWidth - track.clientWidth - 4;
    prev.disabled = atStart;
    next.disabled = atEnd;
    inner.classList.toggle('show-left-fade',  !atStart);
    inner.classList.toggle('show-right-fade', !atEnd);
  }
  window.eliteSlide = function (dir) {
    track.scrollBy({ left: dir * STEP, behavior: 'smooth' });
  };
  track.addEventListener('scroll', sync, { passive: true });
  window.addEventListener('resize', sync);
  const active = track.querySelector('.elite-cat-item.active-cat');
  if (active) setTimeout(() => active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }), 250);
  let dragging = false, startX = 0, scrollStart = 0;
  track.addEventListener('mousedown', e => {
    dragging = true; track.style.cursor = 'grabbing';
    startX = e.pageX - track.offsetLeft; scrollStart = track.scrollLeft;
  });
  ['mouseleave','mouseup'].forEach(ev => track.addEventListener(ev, () => { dragging = false; track.style.cursor = ''; }));
  track.addEventListener('mousemove', e => {
    if (!dragging) return;
    e.preventDefault();
    track.scrollLeft = scrollStart - (e.pageX - track.offsetLeft - startX) * 1.3;
  });
  track.setAttribute('tabindex', '0');
  track.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') eliteSlide(1);
    if (e.key === 'ArrowLeft')  eliteSlide(-1);
  });
  sync();
})();
