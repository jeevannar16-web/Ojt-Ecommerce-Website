// ==============================================================================
// File: map.js
// Description: Footer map initialization with Leaflet and OpenStreetMap
// Re-initializes on turbolinks:load to survive body swaps.
// ==============================================================================

(function(){
  function showError(container, msg) {
    if (!container) return;
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';
    container.style.padding = '12px';
    container.style.color = '#888';
    container.style.fontSize = '0.82rem';
    container.style.textAlign = 'center';
    container.textContent = msg;
  }

  function init(attempt) {
    attempt = attempt || 0;
    var container = document.getElementById('footer-map');
    if (!container) return;

    if (container.dataset.mapInit === '1') return;

    if (typeof L === 'undefined') {
      if (attempt < 50) {
        setTimeout(function(){ init(attempt + 1); }, 100);
      } else {
        showError(container, 'Map could not be loaded. Please refresh the page.');
      }
      return;
    }

    try {
      container.dataset.mapInit = '1';

      var homeLat = parseFloat(container.getAttribute('data-home-lat'));
      var homeLng = parseFloat(container.getAttribute('data-home-lng'));
      var hasHome = container.hasAttribute('data-home-lat') && !isNaN(homeLat) && homeLat !== 0;

      var lat = hasHome ? homeLat : 27.7350;
      var lng = hasHome ? homeLng : 85.3180;
      var label = hasHome ? 'Your Home Location' : 'FITNESS HUB — Basundhara, Kathmandu';

      var map = L.map('footer-map', {
        center: [lat, lng],
        zoom: 14,
        zoomControl: true,
        dragging: true,
        scrollWheelZoom: false,
        attributionControl: false,
      });
      L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://www.openstreetmap.fr/" target="_blank">OpenStreetMap France</a>'
      }).addTo(map);
      L.marker([lat, lng]).addTo(map).bindPopup(label);

      if (typeof enhanceMap === 'function') {
        enhanceMap(map, { fullscreen: true, panArrows: false, myLocation: false });
      }
    } catch (e) {
      container.dataset.mapInit = '';
      showError(container, 'Map failed to load. Please try again later.');
    }
  }

  function run(){ init(0); }

  // Initial load: wait for DOM + Leaflet to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
  document.addEventListener('turbolinks:load', run);
})();