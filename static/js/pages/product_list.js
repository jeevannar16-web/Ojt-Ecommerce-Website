// ==============================================================================
// File: product_list.js
// Description: Product listing with filters, infinite scroll, sort, and pagination
// ==============================================================================

// ==============================================================================
// SECTION: DOM References & State
// ==============================================================================

(function() {
    const grid = document.getElementById('product-grid');
    const sentinel = document.getElementById('scroll-sentinel');
    const loader = document.getElementById('loading-indicator');
    const skeleton = document.getElementById('skeleton-container');
    const countEl = document.getElementById('product-count');
    const filterForm = document.getElementById('filter-form');
    const gridWrap = document.getElementById('pl-grid-wrap');
    if (!grid || !filterForm) return;

    let currentPage = 2;
    let isLoading = false;
    let hasMore = true;

    function collectFormParams() {
        const fd = new FormData(filterForm);
        const params = {};
        for (const [k, v] of fd) {
            if (k === 'type') {
                if (!params[k]) params[k] = [];
                params[k].push(v);
            } else if (v !== '') {
                params[k] = v;
            }
        }
        return params;
    }





    // ==============================================================================
    // SECTION: URL & Parameter Utilities
    // ==============================================================================

    function updateUrlFromParams(params) {
        const url = new URL(window.location.pathname, window.location.origin);
        for (const [k, v] of Object.entries(params)) {
            if (Array.isArray(v)) {
                v.forEach(val => url.searchParams.append(k, val));
            } else {
                url.searchParams.set(k, v);
            }
        }
        window.history.pushState({ params: url.searchParams.toString() }, '', url.toString());
    }





    // ==============================================================================
    // SECTION: Product Loading
    // ==============================================================================

    async function loadProducts(params, append) {
        if (isLoading) return;
        isLoading = true;

        if (!append) {
            currentPage = 2;
            hasMore = true;
            if (loader) loader.style.display = 'none';
            if (skeleton) skeleton.style.display = 'block';
        } else {
            if (loader) loader.style.display = 'flex';
        }

        try {
            const apiUrl = new URL('/store/api/products/', window.location.origin);
            for (const [k, v] of Object.entries(params)) {
                if (Array.isArray(v)) {
                    v.forEach(val => apiUrl.searchParams.append(k, val));
                } else if (v !== undefined && v !== null && v !== '') {
                    apiUrl.searchParams.set(k, v);
                }
            }
            if (append) apiUrl.searchParams.set('page', currentPage);

            const res = await fetch(apiUrl.toString());
            const data = await res.json();

            if (skeleton) skeleton.style.display = 'none';
            if (loader && !append) loader.style.display = 'none';
            if (loader && append) loader.style.display = 'none';

            if (data.cards_html && data.cards_html.trim()) {
                const temp = document.createElement('div');
                temp.innerHTML = data.cards_html;
                const cards = temp.querySelectorAll('.pcard');

                if (append) {
                    cards.forEach((card, i) => {
                        card.style.animationDelay = (0.03 * i) + 's';
                        grid.appendChild(card);
                    });
                } else {
                    grid.innerHTML = '';
                    cards.forEach((card, i) => {
                        card.style.animationDelay = (0.03 * i) + 's';
                        grid.appendChild(card);
                    });
                }

                cards.forEach(c => {
                    c.style.animation = 'none';
                    void c.offsetHeight;
                    c.style.animation = '';
                });
            } else if (!append) {
                const isSearch = data.is_search && params.search;
                grid.innerHTML = [
                    '<div class="empty-state">',
                    '<div class="empty-state-icon">' + (isSearch ? '🔍' : '📦') + '</div>',
                    isSearch
                        ? '<h3>No results found for "' + (params.search || '') + '"</h3><p>Check your spelling or try different keywords.</p>'
                        : '<h3>No products match these filters</h3><p>Try adjusting your price range or equipment type filters.</p>',
                    '<a href="/store/products/" class="pl-btn-browse">Browse All Products</a>',
                    '</div>'
                ].join('');
            }

            if (append) {
                hasMore = data.has_next;
                currentPage = data.next_page || currentPage + 1;
                if (!hasMore && loader) loader.style.display = 'none';
            } else {
                hasMore = data.has_next !== undefined ? data.has_next : true;
                if (data.next_page) currentPage = data.next_page;
            }

            if (countEl && data.total !== undefined) {
                countEl.textContent = data.total + ' item' + (data.total === 1 ? '' : 's');
            }

        } catch (e) {
            console.warn('Load error:', e);
            if (skeleton) skeleton.style.display = 'none';
            if (loader) loader.style.display = 'none';
            if (!append) {
                hasMore = false;
                grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Something went wrong</h3><p>Please try again.</p></div>';
            }
        } finally {
            isLoading = false;
        }
    }





    // ==============================================================================
    // SECTION: Filter Event Handlers
    // ==============================================================================

    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const params = collectFormParams();
        updateUrlFromParams(params);
        loadProducts(params, false);
    });

    document.querySelectorAll('.sort-pill').forEach(function(pill) {
        pill.addEventListener('click', function(e) {
            e.preventDefault();
            const href = pill.getAttribute('href');
            const sortParam = new URL(href, window.location.origin).searchParams.get('sort') || '';
            const sortInput = filterForm.querySelector('input[name="sort"]');
            if (sortInput) sortInput.value = sortParam;

            document.querySelectorAll('.sort-pill').forEach(function(p) {
                p.classList.remove('active');
            });
            pill.classList.add('active');

            const params = collectFormParams();
            updateUrlFromParams(params);
            loadProducts(params, false);
        });
    });

    document.querySelectorAll('.goal-tab').forEach(function(tab) {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const href = tab.getAttribute('href');
            const tabUrl = new URL(href, window.location.origin);
            const goalParam = tabUrl.searchParams.get('goal') || '';
            const goalInput = filterForm.querySelector('input[name="goal"]');
            if (goalInput) goalInput.value = goalParam;

            document.querySelectorAll('.goal-tab').forEach(function(t) {
                t.classList.remove('active');
            });
            tab.classList.add('active');

            const params = collectFormParams();
            updateUrlFromParams(params);
            loadProducts(params, false);
        });
    });

    var clearBtn = document.querySelector('.btn-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            filterForm.querySelectorAll('input[type="number"]').forEach(function(inp) {
                inp.value = '';
            });
            filterForm.querySelectorAll('input[name="type"]').forEach(function(cb) {
                cb.checked = false;
            });
            filterForm.querySelectorAll('input[name="available"]').forEach(function(cb) {
                cb.checked = false;
            });
            filterForm.querySelectorAll('input[type="hidden"]').forEach(function(inp) {
                inp.value = '';
            });
            document.querySelectorAll('.sort-pill').forEach(function(p) {
                p.classList.remove('active');
            });
            var firstSort = document.querySelector('.sort-pill:first-child');
            if (firstSort) firstSort.classList.add('active');
            document.querySelectorAll('.goal-tab').forEach(function(t) {
                t.classList.remove('active');
            });
            var allTab = document.querySelector('.goal-tab:first-child');
            if (allTab) allTab.classList.add('active');

            var sortInput = filterForm.querySelector('input[name="sort"]');
            if (sortInput) sortInput.value = '';

            window.history.pushState({ params: '' }, '', clearBtn.getAttribute('href'));
            loadProducts({}, false);
        });
    }





    // ==============================================================================
    // SECTION: Infinite Scroll
    // ==============================================================================

    if (sentinel) {
        var observer = new IntersectionObserver(async function(entries) {
            var entry = entries[0];
            if (!entry.isIntersecting || isLoading || !hasMore) return;

            isLoading = true;
            if (loader) loader.style.display = 'flex';

            try {
                var url = new URL(window.location.href);
                url.pathname = '/store/api/products/';
                url.searchParams.set('page', currentPage);

                var res = await fetch(url.toString());
                var data = await res.json();

                if (data.cards_html && data.cards_html.trim()) {
                    var temp = document.createElement('div');
                    temp.innerHTML = data.cards_html;
                    var cards = temp.querySelectorAll('.pcard');
                    cards.forEach(function(card, i) {
                        card.style.animationDelay = (0.03 * i) + 's';
                        grid.appendChild(card);
                    });
                    cards.forEach(function(c) {
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
                if (loader) loader.style.display = 'none';
            } finally {
                isLoading = false;
            }
        }, { rootMargin: '300px' });

        observer.observe(sentinel);
    }





    // ==============================================================================
    // SECTION: Pop State Handler
    // ==============================================================================

    window.addEventListener('popstate', function() {
        window.location.href = window.location.href;
    });
})();
