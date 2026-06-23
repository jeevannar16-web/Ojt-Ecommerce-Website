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
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        function(pos) { callback(pos.coords.latitude, pos.coords.longitude); },
        function() { fallbackToIP(callback); },
        { enableHighAccuracy: false, timeout: 6000, maximumAge: 300000 }
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

    /* Search box */
    var searchBox = document.getElementById('profile-location-search');
    var searchBtn = document.getElementById('profile-location-search-btn');
    if (searchBox && searchBtn) {
      function doSearch() {
        var q = searchBox.value.trim();
        if (!q) return;
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<span class="loader-ring-sm"></span>';
        var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=5';
        fetch(url, { headers: { 'Accept-Language': 'en' } })
          .then(function(r) { return r.json(); })
          .then(function(data) {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="bi bi-search"></i>';
            if (!data || data.length === 0) {
              showToast('No locations found for "' + q + '"', true);
              return;
            }
            var result = data[0];
            placeMarker(parseFloat(result.lat), parseFloat(result.lon));
          })
          .catch(function() {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="bi bi-search"></i>';
            showToast('Search failed. Please try again.', true);
          });
      }
      searchBtn.addEventListener('click', doSearch);
      searchBox.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); doSearch(); } });
    }

    /* Use My Location */
    var myLocBtn = document.getElementById('profile-use-my-location');
    if (myLocBtn) {
      myLocBtn.addEventListener('click', function() {
        if (!navigator.geolocation) { showToast('Geolocation is not supported by your browser.', true); return; }
        myLocBtn.disabled = true;
        myLocBtn.innerHTML = '<span class="loader-ring-sm"></span> Locating...';
        navigator.geolocation.getCurrentPosition(
          function(pos) {
            myLocBtn.disabled = false;
            myLocBtn.innerHTML = '<i class="bi bi-crosshair"></i> Use My Location';
            placeMarker(pos.coords.latitude, pos.coords.longitude);
          },
          function(err) {
            myLocBtn.disabled = false;
            myLocBtn.innerHTML = '<i class="bi bi-crosshair"></i> Use My Location';
            var msg = 'Unable to retrieve your location. ';
            if (err.code === 1) msg += 'Please allow location access.';
            else if (err.code === 2) msg += 'Position unavailable.';
            else msg += 'Request timed out.';
            showToast(msg, true);
          },
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
      });
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
        if (!q) { showToast('Please fill in at least your address and city above.', true); return; }
        findBtn.disabled = true;
        findBtn.innerHTML = '<span class="loader-ring-sm"></span> Locating...';
        var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=5';
        fetch(url, { headers: { 'Accept-Language': 'en' } })
          .then(function(r) { return r.json(); })
          .then(function(data) {
            findBtn.disabled = false;
            findBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Find on Map';
            if (!data || data.length === 0) {
              showToast('Could not find that address on the map. Try searching above.', true);
              return;
            }
            var result = data[0];
            placeMarker(parseFloat(result.lat), parseFloat(result.lon));
            showToast('Location found! Adjust marker if needed, then Save.');
          })
          .catch(function() {
            findBtn.disabled = false;
            findBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Find on Map';
            showToast('Search failed. Please try again.', true);
          });
      });
    }
  });
})();