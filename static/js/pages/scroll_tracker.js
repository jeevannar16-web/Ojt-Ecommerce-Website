(function() {
    var sections = [];
    var containers = document.querySelectorAll('.home-section, .admin-card, .seller-card, .sc-section, [data-scroll-section]');
    if (!containers.length) return;

    containers.forEach(function(el) {
        var label = '';
        var h = el.querySelector('h2, h3, .card-hd h3, .seller-card-header h3, .sc-section-header h2');
        if (h) label = h.textContent.trim();
        if (!label) label = 'Section ' + (sections.length + 1);
        var id = el.id || label.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9\-]/g, '');
        if (!el.id) el.id = id;
        sections.push({ el: el, id: id, label: label });
    });

    if (sections.length < 2) return;

    var total = sections.length;
    var circumference = 150.8;

    var progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress-bar';
    progressBar.style.cssText = 'position:fixed;top:0;left:0;width:0%;height:3px;background:linear-gradient(90deg,#d4af37,#f59e0b);z-index:9999;transition:width 0.1s ease;border-radius:0 2px 2px 0;';

    var container = document.createElement('div');
    container.className = 'scroll-circle-container';
    container.style.cssText = 'position:fixed;right:16px;top:50%;transform:translateY(-50%);z-index:9998;display:flex;flex-direction:column;align-items:center;gap:8px;';

    var circleWrap = document.createElement('div');
    circleWrap.className = 'scroll-circle-wrap';
    circleWrap.style.cssText = 'position:relative;width:56px;height:56px;display:flex;align-items:center;justify-content:center;cursor:pointer;';

    var svgNS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('width', '56');
    svg.setAttribute('height', '56');
    svg.setAttribute('viewBox', '0 0 56 56');
    svg.style.cssText = 'position:absolute;top:0;left:0;transform:rotate(-90deg);pointer-events:none;';

    var bgCircle = document.createElementNS(svgNS, 'circle');
    bgCircle.setAttribute('cx', '28');
    bgCircle.setAttribute('cy', '28');
    bgCircle.setAttribute('r', '24');
    bgCircle.setAttribute('fill', 'none');
    bgCircle.setAttribute('stroke', 'rgba(255,255,255,0.06)');
    bgCircle.setAttribute('stroke-width', '3');

    var fgCircle = document.createElementNS(svgNS, 'circle');
    fgCircle.setAttribute('cx', '28');
    fgCircle.setAttribute('cy', '28');
    fgCircle.setAttribute('r', '24');
    fgCircle.setAttribute('fill', 'none');
    fgCircle.setAttribute('stroke', '#d4af37');
    fgCircle.setAttribute('stroke-width', '3');
    fgCircle.setAttribute('stroke-linecap', 'round');
    fgCircle.setAttribute('stroke-dasharray', circumference.toString());
    fgCircle.setAttribute('stroke-dashoffset', circumference.toString());

    svg.appendChild(bgCircle);
    svg.appendChild(fgCircle);

    var pctText = document.createElement('span');
    pctText.className = 'scroll-pct';
    pctText.style.cssText = 'font-size:0.7rem;font-weight:800;color:#f0ece4;font-family:sans-serif;z-index:1;position:relative;text-align:center;line-height:1.2;cursor:pointer;';

    circleWrap.appendChild(svg);
    circleWrap.appendChild(pctText);

    var dotNav = document.createElement('div');
    dotNav.className = 'scroll-dot-nav';
    dotNav.style.cssText = 'display:flex;flex-direction:column;gap:5px;align-items:center;';

    var dots = [];
    sections.forEach(function(s, i) {
        var dot = document.createElement('a');
        dot.href = '#' + s.id;
        dot.title = s.label;
        dot.style.cssText = 'width:7px;height:7px;border-radius:50%;background:#333;display:block;transition:all 0.4s cubic-bezier(.4,0,.2,1);cursor:pointer;position:relative;flex-shrink:0;';
        dot.addEventListener('click', function(e) {
            e.preventDefault();
            navigateToSection(i);
        });

        var tooltip = document.createElement('span');
        tooltip.textContent = s.label;
        tooltip.style.cssText = 'position:absolute;right:16px;top:50%;transform:translateY(-50%);background:rgba(14,14,14,0.95);color:#f0ece4;font-size:0.65rem;padding:4px 10px;border-radius:6px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity 0.2s;border:1px solid rgba(255,255,255,0.06);';
        dot.appendChild(tooltip);
        dot.addEventListener('mouseenter', function() { tooltip.style.opacity = '1'; });
        dot.addEventListener('mouseleave', function() { tooltip.style.opacity = '0'; });

        dotNav.appendChild(dot);
        dots.push(dot);
    });

    container.appendChild(circleWrap);
    container.appendChild(dotNav);

    document.body.appendChild(progressBar);
    document.body.appendChild(container);

    var ticking = false;
    var isNearBottom = false;
    var currentSection = 0;

    function navigateToSection(idx) {
        if (idx < 0) idx = 0;
        if (idx >= total) idx = total - 1;
        var top = sections[idx].el.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({ top: top, behavior: 'smooth' });
    }

    circleWrap.addEventListener('click', function(e) {
        if (e.target === pctText) return;
        var next = (currentSection + 1) % total;
        navigateToSection(next);
    });

    var popup = document.createElement('div');
    popup.className = 'scroll-quick-popup';
    popup.style.cssText = 'position:fixed;right:80px;top:50%;transform:translateY(-50%);background:rgba(14,14,14,0.97);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:10px 0;min-width:180px;z-index:9999;opacity:0;pointer-events:none;transition:all 0.25s cubic-bezier(.4,0,.2,1);box-shadow:0 16px 48px rgba(0,0,0,0.5);backdrop-filter:blur(12px);';
    popup.style.display = 'none';
    document.body.appendChild(popup);

    var popupVisible = false;

    pctText.addEventListener('click', function(e) {
        e.stopPropagation();
        popupVisible = !popupVisible;
        if (popupVisible) {
            popup.innerHTML = '';
            sections.forEach(function(s, i) {
                var item = document.createElement('div');
                item.className = 'scroll-popup-item';
                item.style.cssText = 'padding:8px 16px;color:#aaa;font-size:0.78rem;cursor:pointer;transition:all 0.15s;display:flex;align-items:center;gap:8px;';
                item.textContent = s.label;
                item.addEventListener('mouseenter', function() {
                    this.style.background = 'rgba(212,175,55,0.08)';
                    this.style.color = '#f0ece4';
                });
                item.addEventListener('mouseleave', function() {
                    this.style.background = 'transparent';
                    this.style.color = '#aaa';
                });
                item.addEventListener('click', function() {
                    navigateToSection(i);
                    popupVisible = false;
                    popup.style.display = 'none';
                    popup.style.opacity = '0';
                    popup.style.pointerEvents = 'none';
                });
                if (i === currentSection) {
                    item.style.color = '#d4af37';
                    item.style.fontWeight = '700';
                    var dotInd = document.createElement('span');
                    dotInd.style.cssText = 'width:5px;height:5px;border-radius:50%;background:#d4af37;display:inline-block;';
                    item.insertBefore(dotInd, item.firstChild);
                }
                popup.appendChild(item);
            });
            popup.style.display = 'block';
            setTimeout(function() {
                popup.style.opacity = '1';
                popup.style.pointerEvents = 'auto';
            }, 10);
        } else {
            popup.style.opacity = '0';
            popup.style.pointerEvents = 'none';
            setTimeout(function() { popup.style.display = 'none'; }, 250);
        }
    });

    document.addEventListener('click', function(e) {
        if (popupVisible && !popup.contains(e.target) && e.target !== pctText) {
            popupVisible = false;
            popup.style.opacity = '0';
            popup.style.pointerEvents = 'none';
            setTimeout(function() { popup.style.display = 'none'; }, 250);
        }
    });

    function updateScroll() {
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var viewportCenter = scrollTop + window.innerHeight / 2;

        var activeIdx = -1;
        sections.forEach(function(s, i) {
            var rect = s.el.getBoundingClientRect();
            var elTop = rect.top + window.pageYOffset;
            var elBottom = rect.bottom + window.pageYOffset;
            if (viewportCenter >= elTop && viewportCenter <= elBottom) {
                activeIdx = i;
            }
        });

        if (activeIdx === -1) {
            for (var i = sections.length - 1; i >= 0; i--) {
                var rect = sections[i].el.getBoundingClientRect();
                var elTop = rect.top + window.pageYOffset;
                if (viewportCenter >= elTop) {
                    activeIdx = i;
                    break;
                }
            }
        }

        if (activeIdx === -1) activeIdx = 0;
        currentSection = activeIdx;

        var passed = activeIdx + 1;
        var fillRatio = passed / total;
        var offset = circumference - (circumference * fillRatio);
        fgCircle.setAttribute('stroke-dashoffset', offset.toString());

        pctText.textContent = passed + '/' + total;

        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        var pageProgress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
        progressBar.style.width = Math.min(pageProgress, 100) + '%';

        var nearLast = activeIdx >= total - 2;
        if (nearLast !== isNearBottom) {
            isNearBottom = nearLast;
            if (nearLast) {
                dotNav.style.animation = 'pulse-dots 1.5s ease-in-out infinite';
            } else {
                dotNav.style.animation = 'none';
            }
        }

        dots.forEach(function(d, i) {
            if (i === activeIdx) {
                d.style.background = '#d4af37';
                d.style.boxShadow = '0 0 10px rgba(212,175,55,0.5)';
                d.style.transform = 'scale(1.4)';
            } else if (i < activeIdx) {
                d.style.background = '#d4af37';
                d.style.opacity = '0.4';
                d.style.boxShadow = 'none';
                d.style.transform = 'scale(1)';
            } else {
                d.style.background = '#333';
                d.style.opacity = '1';
                d.style.boxShadow = 'none';
                d.style.transform = 'scale(1)';
            }
        });

        ticking = false;
    }

    var styleTag = document.createElement('style');
    styleTag.textContent = '@keyframes pulse-dots { 0%,100% { opacity:1; } 50% { opacity:0.5; } }';
    document.head.appendChild(styleTag);

    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() { updateScroll(); });
            ticking = true;
        }
    });

    window.addEventListener('resize', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() { updateScroll(); });
            ticking = true;
        }
    });

    updateScroll();
})();
