(function(w) {
  'use strict';

  var KTM_LAT = 27.7172;
  var KTM_LNG = 85.3240;

  w.enhanceMap = function(map, opts) {
    opts = opts || {};

    /* ─── Full-screen toggle ─── */
    if (opts.fullscreen !== false) {
      var fsControl = L.control({ position: opts.fullscreenPosition || 'topright' });
      fsControl.onAdd = function(map) {
        var btn = L.DomUtil.create('button', 'map-fs-btn');
        btn.setAttribute('type', 'button');
        btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>';
        btn.title = 'Toggle fullscreen';
        btn.setAttribute('aria-label', 'Toggle fullscreen');
        btn.style.cssText = 'background:#1a1a1a;border:1px solid rgba(255,255,255,0.08);border-radius:6px;color:#ccc;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;margin-bottom:4px;transition:background 0.2s;';
        btn.onmouseenter = function() { btn.style.background = '#2a2a2a'; btn.style.color = '#fff'; };
        btn.onmouseleave = function() { btn.style.background = '#1a1a1a'; btn.style.color = '#ccc'; };

        var container = map.getContainer();
        var isFull = false;

        btn.onclick = function(e) {
          e.preventDefault();
          isFull = !isFull;
          if (isFull) {
            container.classList.add('map-fullscreen');
            btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3v3a2 2 0 0 1-2 2H3m0 0h18M3 8v13M21 8v13"/></svg>';
            btn.title = 'Exit fullscreen';
          } else {
            container.classList.remove('map-fullscreen');
            btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>';
            btn.title = 'Toggle fullscreen';
          }
          setTimeout(function() { map.invalidateSize(); }, 300);
        };

        return btn;
      };
      fsControl.addTo(map);
    }

    /* ─── Pan arrows (N, S, E, W) ─── */
    if (opts.panArrows !== false) {
      var panControl = L.control({ position: opts.panPosition || 'topright' });
      panControl.onAdd = function(map) {
        var div = L.DomUtil.create('div', 'map-pan-arrows');
        div.style.cssText = 'display:grid;grid-template-columns:30px 30px 30px;grid-template-rows:30px 30px 30px;gap:2px;margin-top:4px;';

        var dirs = [
          { row: 1, col: 2, label: '↑', d: 'north', latOff: 0.01, lngOff: 0 },
          { row: 2, col: 1, label: '←', d: 'west',  latOff: 0, lngOff: -0.01 },
          { row: 2, col: 3, label: '→', d: 'east',  latOff: 0, lngOff: 0.01 },
          { row: 3, col: 2, label: '↓', d: 'south', latOff: -0.01, lngOff: 0 },
        ];

        for (var r = 1; r <= 3; r++) {
          for (var c = 1; c <= 3; c++) {
            var cell = document.createElement('div');
            var found = false;
            for (var i = 0; i < dirs.length; i++) {
              var d = dirs[i];
              if (d.row === r && d.col === c) {
                found = true;
                var btn = document.createElement('button');
                btn.setAttribute('type', 'button');
                btn.textContent = d.label;
                btn.title = 'Pan ' + d.d;
                btn.setAttribute('aria-label', 'Pan ' + d.d);
                btn.style.cssText = 'background:#1a1a1a;border:1px solid rgba(255,255,255,0.08);border-radius:4px;color:#ccc;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:14px;transition:background 0.2s;';
                btn.onmouseenter = function() { this.style.background = '#2a2a2a'; this.style.color = '#fff'; };
                btn.onmouseleave = function() { this.style.background = '#1a1a1a'; this.style.color = '#ccc'; };
                btn.onclick = (function(d) {
                  return function(e) {
                    e.preventDefault();
                    var center = map.getCenter();
                    map.panTo([center.lat + d.latOff, center.lng + d.lngOff], { animate: true, duration: 0.3 });
                  };
                })(d);
                cell.appendChild(btn);
                break;
              }
            }
            if (!found) {
              cell.style.cssText = 'width:30px;height:30px;';
            }
            div.appendChild(cell);
          }
        }

        return div;
      };
      panControl.addTo(map);
    }

    /* ─── Show current location button ─── */
    if (opts.myLocation !== false) {
      var locControl = L.control({ position: opts.locPosition || 'topright' });
      locControl.onAdd = function(map) {
        var btn = L.DomUtil.create('button', 'map-loc-btn');
        btn.setAttribute('type', 'button');
        btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4m10-10h-4M6 12H2"/></svg>';
        btn.title = 'Show my location';
        btn.setAttribute('aria-label', 'Show my location');
        btn.style.cssText = 'background:#1a1a1a;border:1px solid rgba(255,255,255,0.08);border-radius:6px;color:#ccc;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;margin-bottom:4px;transition:background 0.2s;';
        btn.onmouseenter = function() { btn.style.background = '#2a2a2a'; btn.style.color = '#fff'; };
        btn.onmouseleave = function() { btn.style.background = '#1a1a1a'; btn.style.color = '#ccc'; };

        var marker = null;
        btn.onclick = function(e) {
          e.preventDefault();
          if (navigator.geolocation) {
            btn.style.opacity = '0.5';
            navigator.geolocation.getCurrentPosition(
              function(pos) {
                btn.style.opacity = '1';
                var lat = pos.coords.latitude;
                var lng = pos.coords.longitude;
                map.setView([lat, lng], 15, { animate: true });
                if (marker) map.removeLayer(marker);
                marker = L.marker([lat, lng]).addTo(map).bindPopup('You are here').openPopup();
                if (opts.onMyLocation) opts.onMyLocation(lat, lng);
              },
              function() {
                btn.style.opacity = '1';
                if (opts.onLocationFail) opts.onLocationFail();
              }
            );
          } else {
            if (opts.onLocationFail) opts.onLocationFail();
          }
        };

        return btn;
      };
      locControl.addTo(map);
    }
  };

})(window);
