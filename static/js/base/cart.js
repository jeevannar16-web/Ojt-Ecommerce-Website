// cart.js — add to cart, update the cart badge, size/stock display, all the cart interaction

// ==============================================================================
// SECTION: Add to Cart
// ==============================================================================

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
      try { updateStockDisplay(productId, data, btn); } catch(e) {}
      var ssEl = document.getElementById('stock-status-display');
      var scEl = document.getElementById('stock-count');
      if (!data.has_sizes && data.stock_remaining !== undefined) {
        if (scEl) scEl.textContent = data.stock_remaining;
        if (ssEl) {
          ssEl.innerHTML = data.stock_remaining > 0
            ? '<span style="color:#2ec4b6;font-weight:bold;display:flex;align-items:center;gap:8px;flex-wrap:wrap;"><span style="width:8px;height:8px;background:#2ec4b6;border-radius:50%;display:inline-block;"></span><span>In Stock</span><span id="stock-count" style="background:rgba(46,196,182,0.12);padding:1px 10px;border-radius:10px;font-size:0.82rem;">' + data.stock_remaining + '</span><span style="font-weight:400;font-size:0.82rem;color:#888;">units available</span></span>'
            : '<span style="color:#e63946;font-weight:bold;display:flex;align-items:center;"><span style="width:8px;height:8px;background:#e63946;border-radius:50%;display:inline-block;margin-right:8px;"></span>Out of Stock</span>';
        }
        var qtyInput = document.getElementById('qty-input');
        if (qtyInput) qtyInput.max = data.stock_remaining;
      }
      if (window.refreshMiniCart) setTimeout(window.refreshMiniCart, 100);
    } else {
      showToast(data.message || 'Cannot add this item!', true);
      if (btn) btn.disabled = false;
    }
  })
  .catch(function(error) { showToast('Network error: ' + error.message, true); if (btn) btn.disabled = false; });
}





// ==============================================================================
// SECTION: Stock Display Update
// ==============================================================================

function updateStockDisplay(productId, data, btnEl) {
  var stockStatus = document.getElementById('stock-status-display');
  var qtyInput = document.getElementById('qty-input');

  if (data.has_sizes && data.sizes) {
    var sizeSelector = document.getElementById('size-selector');
    if (sizeSelector) {
      data.sizes.forEach(function(s) {
        var btns = sizeSelector.querySelectorAll('.size-btn');
        for (var i = 0; i < btns.length; i++) {
          var b = btns[i];
          if (b.textContent.trim() === s.size) {
            b.disabled = s.stock <= 0;
            if (s.stock <= 0) { b.classList.add('size-oos'); b.title = 'Out of stock'; }
            else { b.classList.remove('size-oos'); b.title = ''; }
            break;
          }
        }
      });
    }
  }

  if (stockStatus) {
    if (data.has_sizes && data.sizes) {
      var anyAvail = data.sizes.some(function(s) { return s.stock > 0; });
      stockStatus.innerHTML = anyAvail
        ? '<span style="color:#2ec4b6;font-weight:bold;display:flex;align-items:center;gap:8px;flex-wrap:wrap;"><span style="width:8px;height:8px;background:#2ec4b6;border-radius:50%;display:inline-block;"></span><span>In Stock</span></span>'
        : '<span style="color:#e63946;font-weight:bold;display:flex;align-items:center;"><span style="width:8px;height:8px;background:#e63946;border-radius:50%;display:inline-block;margin-right:8px;"></span>Out of Stock</span>';
    } else if (!data.has_sizes) {
      stockStatus.innerHTML = data.stock_remaining > 0
        ? '<span style="color:#2ec4b6;font-weight:bold;display:flex;align-items:center;gap:8px;flex-wrap:wrap;"><span style="width:8px;height:8px;background:#2ec4b6;border-radius:50%;display:inline-block;"></span><span>In Stock</span><span id="stock-count" style="background:rgba(46,196,182,0.12);padding:1px 10px;border-radius:10px;font-size:0.82rem;">' + data.stock_remaining + '</span><span style="font-weight:400;font-size:0.82rem;color:#888;">units available</span></span>' + (data.stock_remaining <= 5 ? '<div style="margin-top:6px;font-size:0.72rem;color:#f57224;"><i class="bi bi-lightning-fill"></i> Only ' + data.stock_remaining + ' left \u2014 order soon!</div>' : '')
        : '<span style="color:#e63946;font-weight:bold;display:flex;align-items:center;"><span style="width:8px;height:8px;background:#e63946;border-radius:50%;display:inline-block;margin-right:8px;"></span>Out of Stock</span>';
    }
  }

  if (qtyInput) {
    if (data.has_sizes && data.sizes) {
      var selectedSize = document.getElementById('selected-size');
      if (selectedSize && selectedSize.value) {
        var sz = data.sizes.find(function(s) { return s.size === selectedSize.value; });
        qtyInput.max = sz ? sz.stock : 0;
      }
    } else if (!data.has_sizes) {
      qtyInput.max = data.stock_remaining;
    }
    var qv = parseInt(qtyInput.value);
    var qm = parseInt(qtyInput.max);
    if (qv > qm) qtyInput.value = qm;
    var plus = document.getElementById('qty-plus');
    var minus = document.getElementById('qty-minus');
    if (minus) minus.disabled = qv <= 1;
    if (plus) plus.disabled = qv >= qm;
  }

  var fullyOos = data.has_sizes && data.sizes
    ? data.sizes.every(function(s) { return s.stock <= 0; })
    : data.stock_remaining <= 0;

  if (fullyOos) {
    document.querySelectorAll('.btn-add-bag, .btn-shop-now, .qty-picker, .detail-fav-btn').forEach(function(el) { if (el) el.style.display = 'none'; });
  }

  if (stockStatus) {
    var existingMsg = stockStatus.parentNode.querySelector('.oos-full-msg');
    if (fullyOos) {
      if (!existingMsg) {
        var msg = document.createElement('div');
        msg.className = 'oos-full-msg';
        msg.style.cssText = 'margin-top:12px;padding:12px 16px;background:rgba(230,57,70,0.08);border:1px solid rgba(230,57,70,0.2);border-radius:8px;color:#e63946;font-size:0.85rem;font-weight:600;text-align:center;';
        msg.textContent = 'Out of Stock - Currently Unavailable';
        stockStatus.parentNode.appendChild(msg);
      }
    } else if (existingMsg) {
      existingMsg.remove();
    }
  }

  if (btnEl) {
    var card = btnEl.closest ? btnEl.closest('.pcard') : null;
    if (card) {
      var oosOverlay = card.querySelector('.pcard-out-of-stock');
      var imgDiv = card.querySelector('.pcard-img');
      if (fullyOos) {
        if (!oosOverlay && imgDiv) {
          var ov = document.createElement('div');
          ov.className = 'pcard-out-of-stock';
          ov.textContent = 'Out of Stock';
          imgDiv.appendChild(ov);
        }
        btnEl.disabled = true;
      } else {
        if (oosOverlay) oosOverlay.remove();
        btnEl.disabled = false;
      }
    } else if (!fullyOos) {
      btnEl.disabled = false;
    }
  }
}

