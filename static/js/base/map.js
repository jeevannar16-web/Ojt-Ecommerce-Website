(function(){
  var container = document.getElementById('footer-map');
  if (!container) return;

  var homeLat = parseFloat(container.getAttribute('data-home-lat'));
  var homeLng = parseFloat(container.getAttribute('data-home-lng'));
  var hasHome = container.hasAttribute('data-home-lat') && !isNaN(homeLat) && homeLat !== 0;

  var KTM_LAT = 27.7172;
  var KTM_LNG = 85.3240;

  function detectLocation(callback) {
    if (hasHome) { callback(homeLat, homeLng); return; }
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        function(pos) { callback(pos.coords.latitude, pos.coords.longitude); },
        function() { fallbackToIP(callback); },
        { enableHighAccuracy: false, timeout: 5000, maximumAge: 300000 }
      );
      return;
    }
    fallbackToIP(callback);
  }

  var ipFetched = false;
  function fallbackToIP(callback) {
    if (ipFetched) return;
    ipFetched = true;
    fetch('https://ip-api.com/json/?fields=lat,lon')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data && data.lat && data.lon && !isNaN(data.lat) && data.lat !== 0) {
          callback(data.lat, data.lon);
        } else {
          callback(KTM_LAT, KTM_LNG);
        }
      })
      .catch(function() { callback(KTM_LAT, KTM_LNG); });
  }

  detectLocation(function(lat, lng) {
    var map = L.map('footer-map', {
      center: [lat, lng],
      zoom: 13,
      zoomControl: false,
      dragging: false,
      scrollWheelZoom: false,
      attributionControl: false,
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
    }).addTo(map);
    L.marker([lat, lng]).addTo(map)
      .bindPopup(hasHome ? 'Your Home Location' : 'Your Location');
  });
})();