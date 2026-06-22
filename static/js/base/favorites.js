function toggleFavorite(event, productId, btn) {
  if (event) event.stopPropagation();
  if (!productId || !btn) return;
  const icon = btn.querySelector('i');
  const span = btn.querySelector('span');
  const wasFav = btn.classList.contains('favorited');
  btn.classList.remove('pop');
  void btn.offsetWidth;
  btn.classList.add('pop');
  if (!wasFav) {
    const p = document.createElement('span');
    p.className = 'heart-particle';
    p.textContent = '♥';
    p.style.cssText = 'position:absolute;font-size:0.75rem;color:#ef4444;pointer-events:none;animation:floatHeart 0.8s ease forwards;left:' + (Math.random() * 60 + 20) + '%';
    btn.appendChild(p);
    setTimeout(() => p.remove(), 800);
  }
  if (wasFav) {
    btn.classList.remove('favorited');
    if (icon) icon.className = 'bi bi-heart';
    if (span) span.textContent = 'Wishlist';
  } else {
    btn.classList.add('favorited');
    if (icon) icon.className = 'bi bi-heart-fill';
    if (span) span.textContent = 'Wishlisted';
  }
  const csrfToken = getCookie('csrftoken');
  if (!csrfToken) {
    showToast('Security error: please refresh the page.', true);
    return;
  }
  fetch('/store/favorites/toggle/' + productId + '/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
    credentials: 'same-origin'
  })
  .then(response => {
    if (response.status === 401) { window.location.href = '/users/login/'; return null; }
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  })
  .then(data => {
    if (!data) return;
    if (data.success) {
      const c = document.querySelector('.global-fav-count');
      if (c && data.total_favorites !== undefined) c.textContent = data.total_favorites;
      showToast(data.message || '✓ Updated!');
    } else {
      if (wasFav) { btn.classList.add('favorited'); if (icon) icon.className = 'bi bi-heart-fill'; }
      else { btn.classList.remove('favorited'); if (icon) icon.className = 'bi bi-heart'; }
      showToast(data.message || 'Something went wrong.', true);
    }
  })
  .catch(error => {
    if (wasFav) { btn.classList.add('favorited'); if (icon) icon.className = 'bi bi-heart-fill'; }
    else { btn.classList.remove('favorited'); if (icon) icon.className = 'bi bi-heart'; }
    showToast('Network error: ' + error.message, true);
  });
}
