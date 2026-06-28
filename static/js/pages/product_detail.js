// ==============================================================================
// File: product_detail.js
// Description: Size selection, quantity adjustment, add-to-cart, review submission
// ==============================================================================

// ==============================================================================
// SECTION: Size Selection
// ==============================================================================

function selectSize(btn, size) {
    document.querySelectorAll('.size-btn').forEach(function(b) { b.classList.remove('selected'); });
    btn.classList.add('selected');
    document.getElementById('selected-size').value = size;
    var err = document.getElementById('size-error');
    if (err) err.style.display = 'none';
}





// ==============================================================================
// SECTION: Quantity Adjustment
// ==============================================================================

function changeQty(delta) {
    var input = document.getElementById('qty-input');
    var val = parseInt(input.value) + delta;
    var max = parseInt(input.max);
    if (val < 1) val = 1;
    if (val > max) val = max;
    input.value = val;
    var minus = document.getElementById('qty-minus');
    var plus = document.getElementById('qty-plus');
    if (minus) minus.disabled = val <= 1;
    if (plus) plus.disabled = val >= max;
}





// ==============================================================================
// SECTION: Add to Cart with Size
// ==============================================================================

function addToCartWithSize(event, productId) {
    var sizeInput = document.getElementById('selected-size');
    var hasSizes = document.getElementById('size-selector');
    var selectedSize = null;
    if (hasSizes && sizeInput) {
        if (!sizeInput.value) {
            document.getElementById('size-error').style.display = 'block';
            return;
        }
        selectedSize = sizeInput.value;
    }
    var qty = parseInt(document.getElementById('qty-input').value) || 1;
    addToCart(event, productId, null, qty, selectedSize);
}





// ==============================================================================
// SECTION: Buy Now
// ==============================================================================

function shopNow(evt, productId) {
    var sizeInput = document.getElementById('selected-size');
    var hasSizes = document.getElementById('size-selector');
    var selectedSize = null;
    if (hasSizes && sizeInput) {
        if (!sizeInput.value) {
            document.getElementById('size-error').style.display = 'block';
            return;
        }
        selectedSize = sizeInput.value;
    }
    var qty = parseInt(document.getElementById('qty-input').value) || 1;
    addToCart(evt, productId, null, qty, selectedSize);
    showToast('Taking you to checkout...');
    setTimeout(function() {
        window.location.href = '/store/checkout/';
    }, 800);
}





// ==============================================================================
// SECTION: Review Submission
// ==============================================================================

function submitReview(productId) {
    var ratingInput = document.querySelector('#star-selector input[name="rating"]:checked');
    var comment = document.getElementById('review-comment').value.trim();

    if (!ratingInput) {
        showToast('Please select a star rating!', true);
        return;
    }

    var rating = parseInt(ratingInput.value);

    fetch('/store/products/' + productId + '/review/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating: rating, comment: comment })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.success) {
            showToast(data.created ? '⭐ Review submitted!' : '✅ Review updated!');
            var ratingVal = document.getElementById('product-rating-val');
            var reviewCount = document.getElementById('product-review-count');
            var starsDisplay = document.getElementById('product-stars-display');

            if (ratingVal) ratingVal.textContent = data.new_rating.toFixed(1);
            if (reviewCount) reviewCount.textContent = '(' + data.total_reviews + ' review' + (data.total_reviews !== 1 ? 's' : '') + ')';

            if (starsDisplay) {
                starsDisplay.innerHTML = '';
                for (var i = 1; i <= 5; i++) {
                    var star = document.createElement('i');
                    star.className = i <= Math.round(data.new_rating) ? 'bi bi-star-fill' : 'bi bi-star';
                    star.style.color = i <= Math.round(data.new_rating) ? '#d4af37' : '#333';
                    star.style.fontSize = '1rem';
                    starsDisplay.appendChild(star);
                }
            }
            setTimeout(function() { location.reload(); }, 1200);
        } else {
            showToast(data.message || 'Something went wrong.', true);
        }
    })
    .catch(function() { showToast('Failed to submit review.', true); });
}
