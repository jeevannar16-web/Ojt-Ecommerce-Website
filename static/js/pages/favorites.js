// ==============================================================================
// File: favorites.js
// Description: Remove items from wishlist page with AJAX and DOM animation
// ==============================================================================

// ==============================================================================
// SECTION: Remove Wishlist Item
// ==============================================================================

function removeWishlistItem(event, productId) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const cardElement = document.getElementById(`wishlist-item-${productId}`);
    if (!cardElement) return;

    cardElement.classList.add('removing');

    const targetUrl = "/store/favorites/";

    fetch(targetUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'product_id': productId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Server returned error tracking status configuration mappings.');
        }
        return response.json();
    })
    .then(data => {
        setTimeout(() => {
            cardElement.remove();
            
            const favCounterElements = document.querySelectorAll('.global-fav-count');
            favCounterElements.forEach(el => {
                if (data.total_favorites !== undefined) {
                    el.textContent = data.total_favorites;
                } else {
                    const currentCount = parseInt(el.textContent) || 0;
                    el.textContent = Math.max(0, currentCount - 1);
                }
            });

            const gridContainer = document.getElementById('wishlist-main-grid');
            if (gridContainer && gridContainer.querySelectorAll('.card-product').length === 0) {
                const emptyTemplate = document.getElementById('empty-state-template').innerHTML;
                gridContainer.style.gridTemplateColumns = '1fr';
                gridContainer.innerHTML = emptyTemplate;
            }
        }, 400);
    })
    .catch(error => {
        console.error('Error removing favorite product sequence context execution failure:', error);
        cardElement.classList.remove('removing');
    });
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
