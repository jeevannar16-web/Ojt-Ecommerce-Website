// checkout_map.js — map picker on checkout with draggable marker, geocoding, and "Use My Location"

// ==============================================================================
// SECTION: DOM Elements & State
// ==============================================================================

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
      setTimeout(function() { reverseGeocode(lat, lng, map); }, 300);
    }





    // ==============================================================================
    // SECTION: Marker & Click Handler
    // ==============================================================================

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





    // ==============================================================================
    // SECTION: Reverse Geocoding
    // ==============================================================================

    var geocodeTimer = null;

    function reverseGeocode(lat, lng) {
      clearTimeout(geocodeTimer);
      if (typeof lat !== 'number' || typeof lng !== 'number') return;
      if (Math.abs(lat) < 0.1 && Math.abs(lng) < 0.1) return;

      var url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=' + lat + '&lon=' + lng;

      fetch(url, { headers: { 'Accept-Language': 'en' } })
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (!data || data.error) return;
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
        })
        .catch(function() {});
    }





    // ==============================================================================
    // SECTION: Home Location Button
    // ==============================================================================

    var homeBtn = document.getElementById('home-location-btn');
    if (homeBtn) {
      var homeLat = latInput.value;
      var homeLng = lngInput.value;
      var homeAddress = document.getElementById('home-address');
      var homeCity = document.getElementById('home-city');
      var homeProvince = document.getElementById('home-province');
      var homePostal = document.getElementById('home-postal');
      var homePhone = document.getElementById('home-phone');
      var countryInput = document.getElementById('country');
      var hasHomeCoords = homeLat && homeLng && parseFloat(homeLat) !== 0;
      var hasHomeAddr = homeAddress && homeAddress.value.trim();

      homeBtn.addEventListener('click', function() {
        var addr = homeAddress ? homeAddress.value : '';
        var city = homeCity ? homeCity.value : '';
        var prov = homeProvince ? homeProvince.value : '';
        var postal = homePostal ? homePostal.value : '';
        var phoneVal = homePhone ? homePhone.value : '';
        var cntry = countryInput ? countryInput.value : '';

        if (hasHomeCoords) {
          var lat = parseFloat(homeLat);
          var lng = parseFloat(homeLng);
          if (!isNaN(lat) && !isNaN(lng) && lat !== 0) placeMarker(lat, lng);
        }
        if (hasHomeAddr) {
          var q = [addr, city, prov].filter(Boolean).join(', ');
          if (q) {
            homeBtn.disabled = true;
            homeBtn.innerHTML = '<span class="loader-ring-sm"></span> Locating...';
            var url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&q=' + encodeURIComponent(q) + '&limit=1&countrycodes=np,in';
            fetch(url, { headers: { 'Accept-Language': 'en' } })
              .then(function(r) { return r.json(); })
              .then(function(data) {
                homeBtn.disabled = false;
                homeBtn.innerHTML = '<i class="bi bi-house-door"></i> Deliver to Home';
                if (data && data.length > 0) {
                  placeMarker(parseFloat(data[0].lat), parseFloat(data[0].lon));
                } else if (hasHomeCoords) {
                  placeMarker(parseFloat(homeLat), parseFloat(homeLng));
                }
              })
              .catch(function() {
                homeBtn.disabled = false;
                homeBtn.innerHTML = '<i class="bi bi-house-door"></i> Deliver to Home';
                if (hasHomeCoords) placeMarker(parseFloat(homeLat), parseFloat(homeLng));
              });
          } else if (hasHomeCoords) {
            placeMarker(parseFloat(homeLat), parseFloat(homeLng));
          }
        } else if (!hasHomeCoords) {
          if (typeof showToast === 'function') {
            showToast('Please save your home address in Profile settings first.', true);
          }
        }

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
      });
    }





    // ==============================================================================
    // SECTION: Location Search Box
    // ==============================================================================

    var searchBox = document.getElementById('location-search');
    var searchBtn = document.getElementById('location-search-btn');
    var suggestions = document.getElementById('location-suggestions');
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
    // SECTION: Find on Map Button
    // ==============================================================================

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
        if (!q) {
          if (typeof showToast === 'function') {
            showToast('Enter an address first, then click Find on Map', true);
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
                showToast('No location found for that address. Try a different address.', true);
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
              showToast('Could not reach location service. Check your connection.', true);
            }
          });
      });
    }

    if (typeof enhanceMap === 'function') {
      enhanceMap(map, {
        fullscreen: true, panArrows: false, myLocation: false
      });
    }
  }
})();