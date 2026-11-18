(function(){
  var maps = document.querySelectorAll('[data-order-map]');
  if (!maps.length) return;

  window.initOrderMap = function(el) {
    if (el._leaflet_map) return el._leaflet_map;
    var lat = parseFloat(el.getAttribute('data-lat'));
    var lng = parseFloat(el.getAttribute('data-lng'));
    if (isNaN(lat) || isNaN(lng)) return null;

    var map = L.map(el, {
      center: [lat, lng],
      zoom: 15,
      zoomControl: true,
      dragging: true,
      scrollWheelZoom: true,
      attributionControl: false,
    });
    L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
      maxZoom: 20,
      subdomains: 'abcd',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://www.openstreetmap.fr/" target="_blank">OpenStreetMap France</a>'
    }).addTo(map);
    L.marker([lat, lng]).addTo(map)
      .bindPopup('Delivery Location');

    el._leaflet_map = map;

    if (typeof enhanceMap === 'function') {
      enhanceMap(map, { fullscreen: true, panArrows: false, myLocation: false });
    }
    return map;
  };

  maps.forEach(function(el) {
    if (el.offsetHeight > 0 && el.style.height !== '0px') {
      window.initOrderMap(el);
    }
  });

  var resizeTimer;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
      document.querySelectorAll('[data-order-map]').forEach(function(el) {
        if (el._leaflet_map && el.offsetHeight > 0 && el.style.height !== '0px') {
          el._leaflet_map.invalidateSize();
        }
      });
    }, 200);
  });
})();
