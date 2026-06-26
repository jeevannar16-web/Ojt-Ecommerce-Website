// ==============================================================================
// File: search.js
// Description: Search suggestions, history management, keyboard navigation
// ==============================================================================

// ==============================================================================
// SECTION: DOM References & State
// ==============================================================================

(function() {
  const input = document.getElementById('search-input');
  const dropdown = document.getElementById('search-dropdown');
  const clearBtn = document.getElementById('search-clear-btn');
  const historyList = document.getElementById('search-history-list');
  const suggestionsList = document.getElementById('search-suggestions-list');
  const historySection = document.getElementById('search-history-section');
  const suggestionsLabel = document.getElementById('suggestions-label');
  const STORAGE_KEY = 'fitnesshub_search_history';
  let debounceTimer = null;
  let selectedIdx = -1;
  let currentItems = [];





  // ==============================================================================
  // SECTION: Search History Management
  // ==============================================================================

  function getHistory() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
    catch { return []; }
  }

  function setHistory(items) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }

  function addToHistory(term) {
    if (!term.trim()) return;
    let history = getHistory();
    history = history.filter(h => h.toLowerCase() !== term.toLowerCase());
    history.unshift(term);
    if (history.length > 8) history = history.slice(0, 8);
    setHistory(history);
  }

  window.clearHistory = function() {
    setHistory([]);
    renderHistory();
    if (!input.value.trim()) renderSuggestions('');
  };

  window.clearSearch = function() {
    input.value = '';
    clearBtn.style.display = 'none';
    dropdown.style.display = 'none';
    input.focus();
    input.style.borderColor = '#333';
  };





  // ==============================================================================
  // SECTION: Search UI Functions
  // ==============================================================================

  function renderHistory() {
    const history = getHistory();
    if (history.length === 0) {
      historySection.style.display = 'none';
      return;
    }
    historySection.style.display = 'block';
    historyList.innerHTML = history.map((term, i) =>
      `<div class="search-item" data-index="${i}" data-value="${term.replace(/"/g, '&quot;')}" onclick="selectSearchItem('${term.replace(/'/g, "\\'")}')">
        <i class="bi bi-clock-history" style="color:#555; font-size:0.85rem; width:20px;"></i>
        <span>${term}</span>
      </div>`
    ).join('');
  }

  function renderSuggestions(query) {
    if (!query.trim()) {
      suggestionsLabel.textContent = 'Trending';
      suggestionsList.innerHTML = '<div style="padding:20px;text-align:center;color:#555;font-size:0.85rem;">Type to search products...</div>';
      return;
    }
    suggestionsLabel.textContent = 'Suggestions';
    suggestionsList.innerHTML = '<div style="padding:16px;text-align:center;color:#555;"><i class="bi bi-arrow-repeat" style="animation:spin 1s linear infinite;display:inline-block;"></i></div>';
    fetch('/store/search/suggestions/?q=' + encodeURIComponent(query))
      .then(r => r.json())
      .then(data => {
        const products = data.products || [];
        if (products.length === 0) {
          suggestionsList.innerHTML = '<div style="padding:20px;text-align:center;color:#555;font-size:0.85rem;">No products found</div>';
          currentItems = [];
          return;
        }
        suggestionsList.innerHTML = products.map((p, i) =>
          `<a href="/store/products/${p.id}/" class="search-item" data-index="${i}">
            <i class="bi bi-box-seam" style="color:#d4af37; font-size:0.85rem; width:20px;"></i>
            <span style="flex:1;">${highlightMatch(p.name, query)}</span>
            <span style="color:#d4af37; font-weight:700; font-size:0.85rem;">$${parseFloat(p.price).toFixed(2)}</span>
          </a>`
        ).join('');
        currentItems = products;
        selectedIdx = -1;
      })
      .catch(() => {
        suggestionsList.innerHTML = '<div style="padding:20px;text-align:center;color:#666;font-size:0.85rem;">Could not load suggestions</div>';
      });
  }

  function highlightMatch(text, query) {
    const re = new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
    return text.replace(re, '<strong style="color:#fff;">$1</strong>');
  }

  window.selectSearchItem = function(term) {
    addToHistory(term);
    input.value = term;
    dropdown.style.display = 'none';
    clearBtn.style.display = 'block';
    input.closest('form').submit();
  };

  function navigateDropdown(dir) {
    const items = dropdown.querySelectorAll('.search-item');
    if (items.length === 0) return;
    if (selectedIdx >= 0) items[selectedIdx]?.classList.remove('active');
    selectedIdx = Math.max(0, Math.min(selectedIdx + dir, items.length - 1));
    items[selectedIdx]?.classList.add('active');
    items[selectedIdx]?.scrollIntoView({ block: 'nearest' });
  }

  function commitSelected() {
    const items = dropdown.querySelectorAll('.search-item');
    if (selectedIdx >= 0 && items[selectedIdx]) {
      items[selectedIdx].click();
    } else if (input.value.trim()) {
      addToHistory(input.value.trim());
      input.closest('form').submit();
    }
  }





  // ==============================================================================
  // SECTION: Input Event Handlers
  // ==============================================================================

  input.addEventListener('focus', () => {
    input.style.borderColor = '#d4af37';
    if (getHistory().length > 0) {
      renderHistory();
      if (!input.value.trim()) {
        suggestionsLabel.textContent = 'Trending';
        suggestionsList.innerHTML = '<div style="padding:16px;text-align:center;color:#555;font-size:0.82rem;">Type to search products...</div>';
      }
      dropdown.style.display = 'block';
    }
  });
  input.addEventListener('blur', () => {
    setTimeout(() => { dropdown.style.display = 'none'; }, 200);
    if (!input.value.trim()) input.style.borderColor = '#333';
  });

  input.addEventListener('input', function() {
    clearBtn.style.display = this.value ? 'block' : 'none';
    if (this.value.trim()) {
      dropdown.style.display = 'block';
      renderHistory();
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => renderSuggestions(this.value.trim()), 200);
    } else {
      dropdown.style.display = 'none';
    }
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); navigateDropdown(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); navigateDropdown(-1); }
    else if (e.key === 'Enter') { e.preventDefault(); commitSelected(); }
    else if (e.key === 'Escape') { dropdown.style.display = 'none'; input.blur(); }
  });

  document.addEventListener('click', function(e) {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });





  // ==============================================================================
  // SECTION: Initialization
  // ==============================================================================

  if (input.value.trim()) {
    clearBtn.style.display = 'block';
  }

  input.closest('form').addEventListener('submit', function() {
    if (input.value.trim()) addToHistory(input.value.trim());
  });
})();
