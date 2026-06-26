// order_maps.js — render a Leaflet map for each order's delivery location on the profile page

// ==============================================================================
// SECTION: Order Map Initialization
// ==============================================================================

(function(){
  var maps = document.querySelectorAll('[data-order-map]');
  if (!maps.length) return;

  maps.forEach(function(el) {
    var lat = parseFloat(el.getAttribute('data-lat'));
    var lng = parseFloat(el.getAttribute('data-lng'));
    if (isNaN(lat) || isNaN(lng)) return;

    var map = L.map(el, {
      center: [lat, lng],
      zoom: 15,
      zoomControl: false,
      dragging: false,
      scrollWheelZoom: false,
      attributionControl: false,
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
    }).addTo(map);
    L.marker([lat, lng]).addTo(map)
      .bindPopup('Delivery Location');

    if (typeof enhanceMap === 'function') {
      enhanceMap(map, { fullscreen: true, panArrows: false, myLocation: false });
    }
  });
})();