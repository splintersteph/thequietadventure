(function () {
  "use strict";

  // Mobile menu
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Lightbox for article photos
  var imgs = Array.prototype.slice.call(document.querySelectorAll(".prose img"));
  if (imgs.length) {
    var lb = document.createElement("div");
    lb.className = "lb";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.innerHTML = '<img alt=""><button type="button" class="close" aria-label="Fermer">×</button>' +
      '<button type="button" class="prev" aria-label="Précédente">‹</button>' +
      '<button type="button" class="next" aria-label="Suivante">›</button>';
    document.body.appendChild(lb);
    var big = lb.querySelector("img");
    var idx = 0;
    var show = function (i) {
      idx = (i + imgs.length) % imgs.length;
      big.src = imgs[idx].currentSrc || imgs[idx].src;
      big.alt = imgs[idx].alt;
      lb.classList.add("on");
    };
    var hide = function () { lb.classList.remove("on"); };
    imgs.forEach(function (im, i) { im.addEventListener("click", function () { show(i); }); });
    lb.querySelector(".close").addEventListener("click", hide);
    lb.querySelector(".prev").addEventListener("click", function (e) { e.stopPropagation(); show(idx - 1); });
    lb.querySelector(".next").addEventListener("click", function (e) { e.stopPropagation(); show(idx + 1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) hide(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("on")) return;
      if (e.key === "Escape") hide();
      if (e.key === "ArrowLeft") show(idx - 1);
      if (e.key === "ArrowRight") show(idx + 1);
    });
  }

  // Maps (Leaflet, loaded only where a map exists)
  var maps = document.querySelectorAll("[data-map]");
  if (!maps.length) return;
  var css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  document.head.appendChild(css);
  var s = document.createElement("script");
  s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
  s.onload = function () { Array.prototype.forEach.call(maps, draw); };
  document.head.appendChild(s);

  function draw(el) {
    var data = JSON.parse(el.getAttribute("data-map"));
    var map = L.map(el, { scrollWheelZoom: false, attributionControl: true });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map);
    var bounds = [];
    (data.lines || []).forEach(function (ln) {
      L.polyline(ln.points, { color: ln.color || "#2F5D50", weight: ln.weight || 3, opacity: .9, dashArray: ln.dash || null }).addTo(map);
      ln.points.forEach(function (p) { bounds.push(p); });
    });
    (data.points || []).forEach(function (p) {
      var m = L.circleMarker([p.lat, p.lng], {
        radius: p.r || 7, color: "#FFFDF8", weight: 2.5, fillColor: p.color || "#A8641F", fillOpacity: 1
      }).addTo(map);
      if (p.title) {
        m.bindPopup((p.label ? '<div style="font-size:12px;letter-spacing:1px;text-transform:uppercase;color:#6B6157">' + p.label + "</div>" : "") +
          '<a href="' + p.url + '">' + p.title + "</a>");
      }
      bounds.push([p.lat, p.lng]);
    });
    if (bounds.length === 1) map.setView(bounds[0], 9);
    else if (bounds.length) map.fitBounds(bounds, { padding: [30, 30], maxZoom: 11 });
    else map.setView([30, 10], 2);
  }
})();

// Filtres de la page « Voyages »
(function () {
  var grid = document.getElementById("trip-grid");
  if (!grid) return;
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip[data-filter]"));
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var count = document.querySelector(".filter-count");
  var empty = document.querySelector(".filter-empty");
  function apply(key) {
    var n = 0;
    cards.forEach(function (c) {
      var ok = !key || (" " + c.getAttribute("data-cats") + " ").indexOf(" " + key + " ") > -1;
      c.hidden = !ok;
      if (ok) n++;
    });
    chips.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-filter") === key ? "true" : "false"); });
    if (count) count.textContent = n + " " + count.getAttribute("data-word");
    if (empty) empty.hidden = n > 0;
  }
  chips.forEach(function (b) {
    b.addEventListener("click", function () {
      var key = b.getAttribute("data-filter");
      history.replaceState(null, "", key ? "#" + key : location.pathname);
      apply(key);
    });
  });
  function fromHash() { apply(decodeURIComponent(location.hash.slice(1))); }
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();

// Particules d'ambiance dans l'en-tête des voyages (pétales, feuilles, papillons…)
(function () {
  var box = document.querySelector(".hero-particles");
  if (!box || (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  var path = box.getAttribute("data-path");
  var colors = box.getAttribute("data-colors").split(",");
  var kind = box.getAttribute("data-kind");
  var n = kind === "butterflies" ? 5 : (window.innerWidth < 640 ? 9 : 16);
  for (var i = 0; i < n; i++) {
    var size = (kind === "snow" ? 6 : 12) + Math.random() * (kind === "snow" ? 6 : 12);
    var el = document.createElement("i");
    el.style.left = (Math.random() * 100) + "%";
    el.style.animationDuration = (kind === "butterflies" ? 14 : 9) + Math.random() * 9 + "s";
    el.style.animationDelay = (-Math.random() * 16) + "s";
    el.style.opacity = (kind === "snow" ? .8 : .9).toString();
    var c = colors[i % colors.length];
    var stroke = kind === "leaves" ? ' stroke="rgba(60,40,20,.35)" stroke-width="0.8"' : "";
    el.innerHTML = '<svg width="' + size + '" height="' + size + '" viewBox="0 0 20 20" style="animation-duration:' +
      (1.6 + Math.random() * 2) + 's"><path d="' + path + '" fill="' + c + '"' + stroke + '/></svg>';
    box.appendChild(el);
  }
})();

// Apparition des étapes au défilement
(function () {
  var legs = document.querySelectorAll(".leg");
  if (!legs.length || !("IntersectionObserver" in window)) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -8% 0px" });
  Array.prototype.forEach.call(legs, function (l) { l.classList.add("reveal"); io.observe(l); });
})();

// Récits : particules sur la photo de couverture, voyageur qui avance avec la lecture, apparition des photos
(function () {
  var article = document.querySelector("article.prose");
  if (!article) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var box = document.querySelector(".cover-frame .hero-particles");
  if (box && !reduce) {
    var path = box.getAttribute("data-path"), colors = box.getAttribute("data-colors").split(","), kind = box.getAttribute("data-kind");
    var n = kind === "butterflies" ? 4 : 12;
    for (var i = 0; i < n; i++) {
      var size = (kind === "snow" ? 6 : 12) + Math.random() * (kind === "snow" ? 6 : 12);
      var el = document.createElement("i");
      el.style.left = (Math.random() * 100) + "%";
      el.style.animationDuration = (kind === "butterflies" ? 14 : 9) + Math.random() * 9 + "s";
      el.style.animationDelay = (-Math.random() * 16) + "s";
      el.innerHTML = '<svg width="' + size + '" height="' + size + '" viewBox="0 0 20 20" style="animation-duration:' + (1.6 + Math.random() * 2) +
        's"><path d="' + path + '" fill="' + colors[i % colors.length] + '"/></svg>';
      box.appendChild(el);
    }
  }

  var bar = document.querySelector(".read-route");
  if (bar) {
    var done = bar.querySelector(".read-done"), rider = bar.querySelector(".rider"), idle;
    var update = function () {
      var r = article.getBoundingClientRect();
      var total = r.height - window.innerHeight * 0.6;
      var p = Math.min(1, Math.max(0, (-r.top + window.innerHeight * 0.3) / Math.max(1, total)));
      done.style.width = (p * 100) + "%";
      rider.style.left = "calc(" + (p * 100) + "% * 0.94 + 3%)";
      rider.style.opacity = p > 0.01 ? "1" : "0";
      bar.classList.remove("idle");
      clearTimeout(idle);
      idle = setTimeout(function () { bar.classList.add("idle"); }, 400);
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  if (reduce || !("IntersectionObserver" in window)) return;
  var targets = article.querySelectorAll(":scope > img, :scope > figure, :scope > .gallery, :scope > video, :scope > h3, :scope > h4, :scope > blockquote, :scope > .strava-card");
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -10% 0px" });
  Array.prototype.forEach.call(targets, function (t) { t.classList.add("rv"); io.observe(t); });
})();
