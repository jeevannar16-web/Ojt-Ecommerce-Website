// ==============================================================================
// File: profile_map.js
// Description: Profile map picker for setting default delivery location
// ==============================================================================

// ==============================================================================
// SECTION: DOM Elements & State
// ==============================================================================

(function(){
  function showMapError(container, msg) {
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

  function waitForLeaflet(container, cb, attempt) {
    attempt = attempt || 0;
    if (typeof L !== 'undefined') { cb(); return; }
    if (attempt < 50) {
      setTimeout(function(){ waitForLeaflet(container, cb, attempt + 1); }, 100);
    } else {
      showMapError(container, 'Map could not be loaded. Please refresh the page.');
    }
  }

  var container = document.getElementById('profile-map');
  if (!container) return;

  waitForLeaflet(container, function(){

  var latInput = document.getElementById('profile-latitude');
  var lngInput = document.getElementById('profile-longitude');
  if (!latInput || !lngInput) return;

  var savedLat = parseFloat(latInput.value);
  var savedLng = parseFloat(lngInput.value);
  var hasSaved = latInput.value && lngInput.value && !isNaN(savedLat) && savedLat !== 0;
  var marker = null;

  var KTM_LAT = 27.7172;
  var KTM_LNG = 85.3240;





  // ==============================================================================
  // SECTION: Location Detection
  // ==============================================================================

  function detectLocation(callback) {
    if (hasSaved) { callback(savedLat, savedLng); return; }
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





  // ==============================================================================
  // SECTION: Map Initialization
  // ==============================================================================

  detectLocation(function(lat, lng) {
    var map = L.map('profile-map', {
      center: [lat, lng],
      zoom: 14,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
      maxZoom: 20,
      subdomains: 'abcd',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://www.openstreetmap.fr/" target="_blank">OpenStreetMap France</a>'
    }).addTo(map);

    if (hasSaved) {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      marker.bindPopup('Default Location').openPopup();
      map.setView([lat, lng], 14);
    }

    map.on('click', function(e) {
      placeMarker(e.latlng.lat, e.latlng.lng);
    });

    function placeMarker(lat, lng) {
      if (marker) map.removeLayer(marker);
      marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      marker.bindPopup('Default Location').openPopup();
      marker.on('dragend', function(e) {
        var pos = e.target.getLatLng();
        latInput.value = pos.lat.toFixed(6);
        lngInput.value = pos.lng.toFixed(6);
      });
      latInput.value = lat.toFixed(6);
      lngInput.value = lng.toFixed(6);
      map.setView([lat, lng], 14);
    }





    // ==============================================================================
    // SECTION: Location Search
    // ==============================================================================

    /* Search box with autocomplete */
    var searchBox = document.getElementById('profile-location-search');
    var searchBtn = document.getElementById('profile-location-search-btn');
    var suggestions = document.getElementById('profile-location-suggestions');
    if (searchBox && searchBtn && suggestions) {
      var debounceTimer = null;
      searchBox.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        var q = searchBox.value.trim();
        if (q.length < 3) { suggestions.style.display = 'none'; return; }
        debounceTimer = setTimeout(function() {
          var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=5&countrycodes=np,in';
          fetch(url, { headers: { 'Accept-Language': 'en' } })
            .then(function(r) { return r.json(); })
            .then(function(data) {
              suggestions.innerHTML = '';
              if (!data || data.length === 0) { suggestions.style.display = 'none'; return; }
              data.forEach(function(r) {
                var d = document.createElement('div');
                d.textContent = r.display_name;
                d.addEventListener('click', function() {
                  placeMarker(parseFloat(r.lat), parseFloat(r.lon));
                  searchBox.value = r.display_name.split(',')[0];
                  suggestions.style.display = 'none';
                });
                suggestions.appendChild(d);
              });
              suggestions.style.display = 'block';
            })
            .catch(function() { suggestions.style.display = 'none'; });
        }, 300);
      });
      searchBox.addEventListener('blur', function() { setTimeout(function() { suggestions.style.display = 'none'; }, 200); });
      searchBox.addEventListener('focus', function() {
        if (suggestions.children.length) suggestions.style.display = 'block';
      });
      function doSearch() {
        var q = searchBox.value.trim();
        if (!q) return;
        var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=5&countrycodes=np,in';
        fetch(url, { headers: { 'Accept-Language': 'en' } })
          .then(function(r) { return r.json(); })
          .then(function(data) {
            if (!data || data.length === 0) return;
            var result = data[0];
            placeMarker(parseFloat(result.lat), parseFloat(result.lon));
          })
          .catch(function() {});
      }
      searchBtn.addEventListener('click', doSearch);
      searchBox.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); doSearch(); } });
    }





    // ==============================================================================
    // SECTION: Find on Map from Address
    // ==============================================================================

    /* Find on Map from address fields */
    var findBtn = document.getElementById('profile-find-on-map');
    if (findBtn) {
      findBtn.addEventListener('click', function() {
        var addr = document.querySelector('input[name="address_line1"]');
        var city = document.querySelector('input[name="city"]');
        var state = document.querySelector('input[name="state"]');
        var parts = [];
        if (addr && addr.value.trim()) parts.push(addr.value.trim());
        if (city && city.value.trim()) parts.push(city.value.trim());
        if (state && state.value.trim()) parts.push(state.value.trim());
        var q = parts.join(', ');
        if (!q) {
          if (typeof showToast === 'function') {
            showToast('Please type your address first, then click Find on Map.', true);
          }
          return;
        }
        findBtn.disabled = true;
        findBtn.innerHTML = '<span class="loader-ring-sm"></span> Locating...';
        var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=5';
        fetch(url, { headers: { 'Accept-Language': 'en' } })
          .then(function(r) { return r.json(); })
          .then(function(data) {
            findBtn.disabled = false;
            findBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Find on Map';
            if (!data || data.length === 0) {
              if (typeof showToast === 'function') {
                showToast('Could not find that location. Try a more specific address.', true);
              }
              return;
            }
            var result = data[0];
            placeMarker(parseFloat(result.lat), parseFloat(result.lon));
          })
          .catch(function() {
            findBtn.disabled = false;
            findBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Find on Map';
            if (typeof showToast === 'function') {
              showToast('Location search failed. Try again.', true);
            }
          });
      });
    }

    if (typeof enhanceMap === 'function') {
      enhanceMap(map, {
        fullscreen: true, panArrows: false, myLocation: false
      });
    }
  });
  });
})();