    (function() {
        const grid = document.getElementById('product-grid');
        const sentinel = document.getElementById('scroll-sentinel');
        const loader = document.getElementById('loading-indicator');
        const skeleton = document.getElementById('skeleton-container');
        const countEl = document.getElementById('product-count');
        if (!grid || !sentinel) return;

        let currentPage = 2;
        let isLoading = false;
        let hasMore = true;

        const observer = new IntersectionObserver(async (entries) => {
            const entry = entries[0];
            if (!entry.isIntersecting || isLoading || !hasMore) return;

            isLoading = true;
            if (skeleton) skeleton.style.display = 'block';

            try {
                const url = new URL(window.location.href);
                url.searchParams.set('page', currentPage);
                url.pathname = '/store/api/products/';

                const res = await fetch(url.toString());
                const data = await res.json();

                if (skeleton) skeleton.style.display = 'none';

                if (data.cards_html) {
                    const temp = document.createElement('div');
                    temp.innerHTML = data.cards_html;
                    const cards = temp.querySelectorAll('.pcard');
                    cards.forEach((card, i) => {
                        card.style.animationDelay = (0.03 * i) + 's';
                        grid.appendChild(card);
                    });
                    cards.forEach(c => {
                        c.style.animation = 'none';
                        void c.offsetHeight;
                        c.style.animation = '';
                    });
                }

                hasMore = data.has_next;
                currentPage = data.next_page || currentPage + 1;
                if (countEl && data.total) {
                    countEl.textContent = data.total + ' item' + (data.total === 1 ? '' : 's');
                }
                if (!hasMore && loader) loader.style.display = 'none';
            } catch (e) {
                console.warn('Infinite scroll error:', e);
                hasMore = false;
                if (skeleton) skeleton.style.display = 'none';
            } finally {
                isLoading = false;
            }
        }, { rootMargin: '300px' });

        observer.observe(sentinel);

        // Show loader when hasMore and not the last page
        const checkHasMore = function() {
            if (!hasMore && loader) loader.style.display = 'none';
        };
        setTimeout(checkHasMore, 500);
    })();
