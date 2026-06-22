function addToCart(event, productId, btnEl, quantity, size) {
  if (event) event.stopPropagation();
  const btn = btnEl || (event && event.currentTarget) || null;
  if (btn) btn.disabled = true;
  const csrfToken = getCookie('csrftoken');
  if (!csrfToken) {
    showToast('Security error: please refresh the page.', true);
    if (btn) btn.disabled = false;
    return;
  }
  var body = { quantity: quantity || 1 };
  if (size) body.size = size;
  fetch('/store/cart/add/' + productId + '/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(body)
  })
  .then(response => {
    if (response.status === 401) { window.location.href = '/users/login/'; return null; }
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  })
  .then(data => {
    if (!data) return;
    if (data.success) {
      const badge = document.getElementById('cart-count');
      if (badge && data.cart_count !== undefined) badge.textContent = data.cart_count;
      const cartIcon = document.getElementById('cart-count');
      if (cartIcon) { cartIcon.style.transform = 'scale(1.4)'; setTimeout(function(){ cartIcon.style.transform = ''; }, 250); }
      showToast(data.message || '✓ Added to bag!');
    } else {
      showToast(data.message || 'Cannot add this item!', true);
    }
  })
  .catch(function(error) { showToast('Network error: ' + error.message, true); })
  .finally(function() { if (btn) btn.disabled = false; });
}
