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
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: "abcd", maxZoom: 18
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
