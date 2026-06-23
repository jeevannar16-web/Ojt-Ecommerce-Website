(function(){
  var mapContainer = document.getElementById('checkout-map');
  if (!mapContainer) return;

  var latInput = document.getElementById('id_latitude');
  var lngInput = document.getElementById('id_longitude');
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
    initMap(lat, lng);
  });

  function initMap(lat, lng) {
    var map = L.map('checkout-map', {
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
      marker.bindPopup('Delivery Location').openPopup();
      marker.on('dragend', onMarkerMoved);
      map.setView([lat, lng], 14);
    }

    function onMarkerMoved(e) {
      var pos = e.target.getLatLng();
      latInput.value = pos.lat.toFixed(6);
      lngInput.value = pos.lng.toFixed(6);
      reverseGeocode(pos.lat, pos.lng, map);
    }

    function placeMarker(lat, lng) {
      if (marker) map.removeLayer(marker);
      marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      marker.bindPopup('Delivery Location').openPopup();
      marker.on('dragend', onMarkerMoved);
      latInput.value = lat.toFixed(6);
      lngInput.value = lng.toFixed(6);
      map.setView([lat, lng], 14);
      reverseGeocode(lat, lng, map);
    }

    map.on('click', function(e) {
      placeMarker(e.latlng.lat, e.latlng.lng);
    });

    var geocodeTimer = null;

    function reverseGeocode(lat, lng) {
      clearTimeout(geocodeTimer);
      var statusEl = document.getElementById('map-status');
      if (statusEl) statusEl.textContent = 'Looking up address...';

      if (typeof lat !== 'number' || typeof lng !== 'number') return;
      if (Math.abs(lat) < 0.1 && Math.abs(lng) < 0.1) return;

      var url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=' + lat + '&lon=' + lng;
      var dots = 0;
      var statusInterval = setInterval(function() {
        dots = (dots + 1) % 4;
        if (statusEl) statusEl.textContent = 'Looking up address' + '.'.repeat(dots);
      }, 500);

      fetch(url, { headers: { 'Accept-Language': 'en' } })
        .then(function(r) { return r.json(); })
        .then(function(data) {
          clearInterval(statusInterval);
          if (statusEl) statusEl.textContent = '';
          if (!data || data.error) {
            if (statusEl) statusEl.textContent = 'Could not determine address. Please fill in manually.';
            return;
          }
          var addr = data.address || {};
          var street = addr.road || addr.suburb || addr.neighbourhood || '';
          var houseNum = addr.house_number || '';
          if (houseNum && street) street = houseNum + ' ' + street;
          else if (houseNum && !street) street = houseNum;
          var city = addr.city || addr.town || addr.village || addr.county || addr.state_district || '';
          var state = addr.state || '';
          var postcode = addr.postcode || '';
          var country = addr.country || '';

          var addressInput = document.getElementById('shipping_address');
          var cityInput = document.getElementById('city');
          var provinceInput = document.getElementById('province');
          var postalInput = document.getElementById('postal_code');
          var countryInput = document.getElementById('country');

          if (street && addressInput && !addressInput.value) addressInput.value = street;
          if (city && cityInput && !cityInput.value) cityInput.value = city;
          if (state && provinceInput && !provinceInput.value) provinceInput.value = state;
          if (postcode && postalInput && !postalInput.value) postalInput.value = postcode;
          if (country && countryInput && !countryInput.value) countryInput.value = country;

          if (addr.display_name && statusEl) {
            statusEl.textContent = 'Address found: ' + addr.display_name.substring(0, 100) + '...';
            statusEl.style.color = '#2ec4b6';
          }
        })
        .catch(function() {
          clearInterval(statusInterval);
          if (statusEl) statusEl.textContent = 'Geocoding unavailable. Please fill in address manually.';
        });
    }

    var locBtn = document.getElementById('use-my-location');
    if (locBtn) {
      locBtn.addEventListener('click', function() {
        if (!navigator.geolocation) {
          showToast('Geolocation is not supported by your browser.', true);
          return;
        }
        locBtn.disabled = true;
        locBtn.innerHTML = '<span class="loader-ring-sm"></span> Locating...';
        navigator.geolocation.getCurrentPosition(
          function(pos) {
            locBtn.disabled = false;
            locBtn.innerHTML = '<i class="bi bi-crosshair"></i> Use My Location';
            placeMarker(pos.coords.latitude, pos.coords.longitude);
          },
          function(err) {
            locBtn.disabled = false;
            locBtn.innerHTML = '<i class="bi bi-crosshair"></i> Use My Location';
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

    var homeBtn = document.getElementById('home-location-btn');
    if (homeBtn) {
      var homeLat = latInput.value;
      var homeLng = lngInput.value;
      if (homeLat && homeLng && parseFloat(homeLat) !== 0) { homeBtn.style.display = ''; }
      var homeAddress = document.getElementById('home-address');
      var homeCity = document.getElementById('home-city');
      var homeProvince = document.getElementById('home-province');
      var homePostal = document.getElementById('home-postal');
      var homePhone = document.getElementById('home-phone');
      var countryInput = document.getElementById('country');

      homeBtn.addEventListener('click', function() {
        var lat = parseFloat(homeLat);
        var lng = parseFloat(homeLng);
        if (!isNaN(lat) && !isNaN(lng) && lat !== 0) {
          placeMarker(lat, lng);
        }
        var addr = homeAddress ? homeAddress.value : '';
        var city = homeCity ? homeCity.value : '';
        var prov = homeProvince ? homeProvince.value : '';
        var postal = homePostal ? homePostal.value : '';
        var phoneVal = homePhone ? homePhone.value : '';
        var cntry = countryInput ? countryInput.value : '';

        var addressInput = document.getElementById('shipping_address');
        var cityInput = document.getElementById('city');
        var provinceInput = document.getElementById('province');
        var postalInput = document.getElementById('postal_code');
        var phoneInput = document.getElementById('phone_number');

        if (addr && addressInput) addressInput.value = addr;
        if (city && cityInput) cityInput.value = city;
        if (prov && provinceInput) provinceInput.value = prov;
        if (postal && postalInput) postalInput.value = postal;
        if (phoneVal && phoneInput) phoneInput.value = phoneVal;
        if (cntry && countryInput) countryInput.value = cntry;

        showToast('Home address applied!');
      });
    }

    var searchBox = document.getElementById('location-search');
    var searchBtn = document.getElementById('location-search-btn');
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

    var findBtn = document.getElementById('find-on-map-btn');
    if (findBtn) {
      findBtn.addEventListener('click', function() {
        var addr = document.getElementById('shipping_address');
        var city = document.getElementById('city');
        var prov = document.getElementById('province');
        var parts = [];
        if (addr && addr.value.trim()) parts.push(addr.value.trim());
        if (city && city.value.trim()) parts.push(city.value.trim());
        if (prov && prov.value.trim()) parts.push(prov.value.trim());
        var q = parts.join(', ');
        if (!q) { showToast('Please fill in at least a street address and city.', true); return; }
        findBtn.disabled = true;
        findBtn.innerHTML = '<span class="loader-ring-sm"></span> Locating...';
        var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=5';
        fetch(url, { headers: { 'Accept-Language': 'en' } })
          .then(function(r) { return r.json(); })
          .then(function(data) {
            findBtn.disabled = false;
            findBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Find on Map';
            if (!data || data.length === 0) {
              showToast('Could not find that address on the map. Try searching below.', true);
              return;
            }
            var result = data[0];
            placeMarker(parseFloat(result.lat), parseFloat(result.lon));
            showToast('Location found! Adjust marker if needed.');
          })
          .catch(function() {
            findBtn.disabled = false;
            findBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Find on Map';
            showToast('Search failed. Please try again.', true);
          });
      });
    }
  }
})();