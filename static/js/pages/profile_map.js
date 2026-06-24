(function(){
  var container = document.getElementById('profile-map');
  if (!container) return;

  var latInput = document.getElementById('profile-latitude');
  var lngInput = document.getElementById('profile-longitude');
  if (!latInput || !lngInput) return;

  var savedLat = parseFloat(latInput.value);
  var savedLng = parseFloat(lngInput.value);
  var hasSaved = latInput.value && lngInput.value && !isNaN(savedLat) && savedLat !== 0;
  var marker = null;

  var KTM_LAT = 27.7172;
  var KTM_LNG = 85.3240;

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

  detectLocation(function(lat, lng) {
    var map = L.map('profile-map', {
      center: [lat, lng],
      zoom: 14,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
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
})();