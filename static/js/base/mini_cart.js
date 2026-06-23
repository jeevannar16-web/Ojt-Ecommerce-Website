(function(){
  var badgeOnly = !document.getElementById('mini-cart-dropdown');

  function fetchMiniCart(callback) {
    fetch('/store/api/cart-mini/')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (!data || !data.success) return;
        var badge = document.getElementById('cart-count');
        if (badge && data.cart_count !== undefined) badge.textContent = data.cart_count;
        if (badgeOnly) { if (callback) callback(); return; }
        var list = document.getElementById('mini-cart-items');
        var empty = document.getElementById('mini-cart-empty');
        var footer = document.getElementById('mini-cart-footer');
        var totalEl = document.getElementById('mini-cart-total');
        var countEl = document.getElementById('mini-cart-count');
        if (countEl) countEl.textContent = data.cart_count + ' item' + (data.cart_count !== 1 ? 's' : '');
        if (list) {
          list.innerHTML = '';
          if (data.items && data.items.length > 0) {
            if (empty) empty.style.display = 'none';
            if (footer) footer.style.display = 'block';
            if (totalEl) totalEl.textContent = '$' + data.total.toFixed(2);
            data.items.forEach(function(item) {
              var link = document.createElement('a');
              link.href = '/store/products/' + item.product_id + '/';
              link.style.cssText = 'display:flex; align-items:center; gap:12px; padding:10px 16px; border-bottom:1px solid #222; text-decoration:none; color:inherit; transition:background 0.15s;';
              link.onmouseover = function(){ this.style.background = '#1a1a1a'; };
              link.onmouseout = function(){ this.style.background = ''; };
              var img = document.createElement('img');
              img.src = item.image || '/static/images/placeholder.png';
              img.alt = item.name;
              img.style.cssText = 'width:50px; height:50px; border-radius:8px; object-fit:cover; background:#222; flex-shrink:0;';
              link.appendChild(img);
              var info = document.createElement('div');
              info.style.cssText = 'flex:1; min-width:0;';
              var nameEl = document.createElement('div');
              nameEl.style.cssText = 'color:#fff; font-size:0.78rem; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;';
              nameEl.textContent = item.name;
              info.appendChild(nameEl);
              if (item.size) {
                var sizeEl = document.createElement('div');
                sizeEl.style.cssText = 'color:#888; font-size:0.68rem; margin-top:1px;';
                sizeEl.textContent = 'Size: ' + item.size;
                info.appendChild(sizeEl);
              }
              var priceEl = document.createElement('div');
              priceEl.style.cssText = 'color:#888; font-size:0.7rem; margin-top:2px;';
              priceEl.textContent = item.quantity + ' x $' + item.price.toFixed(2);
              info.appendChild(priceEl);
              link.appendChild(info);
              var subEl = document.createElement('div');
              subEl.style.cssText = 'color:#fff; font-weight:600; font-size:0.8rem; white-space:nowrap;';
              subEl.textContent = '$' + item.subtotal.toFixed(2);
              link.appendChild(subEl);
              list.appendChild(link);
            });
          } else {
            if (empty) empty.style.display = 'block';
            if (footer) footer.style.display = 'none';
          }
        }
        if (callback) callback();
      })
      .catch(function() { if (callback) callback(); });
  }

  if (badgeOnly) {
    window.refreshMiniCart = fetchMiniCart;
    return;
  }

  var wrap = document.querySelector('.cart-dropdown-wrap');
  var dropdown = document.getElementById('mini-cart-dropdown');
  var toggleBtn = document.getElementById('cart-toggle-btn');
  if (!dropdown || !toggleBtn || !wrap) return;

  var hideTimer = null;
  var isHovering = false;

  function showDropdown() {
    clearTimeout(hideTimer);
    if (dropdown.style.display === 'block') return;
    fetchMiniCart(function() {
      dropdown.style.display = 'block';
      dropdown.style.opacity = '0';
      dropdown.style.transform = 'translateY(4px)';
      setTimeout(function() {
        dropdown.style.opacity = '1';
        dropdown.style.transform = 'translateY(0)';
      }, 10);
    });
  }

  function hideDropdown() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function() {
      if (!isHovering) {
        dropdown.style.display = 'none';
      }
    }, 200);
  }

  wrap.addEventListener('mouseenter', function() {
    isHovering = true;
    clearTimeout(hideTimer);
    showDropdown();
  });

  wrap.addEventListener('mouseleave', function(e) {
    isHovering = false;
    hideDropdown();
  });

  dropdown.addEventListener('mouseenter', function() {
    isHovering = true;
    clearTimeout(hideTimer);
  });

  dropdown.addEventListener('mouseleave', function() {
    isHovering = false;
    hideDropdown();
  });

  window.refreshMiniCart = fetchMiniCart;
})();

window.addEventListener('pageshow', function(e) {
  if (window.refreshMiniCart) window.refreshMiniCart();
});