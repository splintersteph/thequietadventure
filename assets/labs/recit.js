/* Prototype de récit : la carte et le profil d'altitude suivent la lecture */
(function () {
  "use strict";
  var data = JSON.parse(document.getElementById("lr-data").textContent);
  var days = data.days, color = data.color;
  document.body.style.setProperty("--trip", color);
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var total = days[days.length - 1].start + days[days.length - 1].km;
  var panel = document.querySelector(".lr-panel"), top = document.querySelector(".lr-top"), btn = document.querySelector(".lr-mapbtn");
  var dayNames = Array.prototype.map.call(document.querySelectorAll(".lr-open .lr-day"), function (e) { return e.textContent.trim(); });

  // ---------- géométrie ----------
  function hav(a, b) {
    var r = Math.PI / 180, dLa = (b[0] - a[0]) * r, dLo = (b[1] - a[1]) * r;
    var s = Math.sin(dLa / 2) * Math.sin(dLa / 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLo / 2) * Math.sin(dLo / 2);
    return 12742 * Math.asin(Math.sqrt(s));
  }
  days.forEach(function (d) {
    var c = [0];
    for (var i = 1; i < d.line.length; i++) c.push(c[i - 1] + hav(d.line[i - 1], d.line[i]));
    var f = d.km / (c[c.length - 1] || 1);
    d.cum = c.map(function (x) { return x * f; });
  });
  function dayAt(km) { for (var i = days.length - 1; i >= 0; i--) if (km >= days[i].start - 1e-6) return i; return 0; }
  function posAt(km) {
    var d = days[dayAt(km)], x = Math.max(0, Math.min(d.km, km - d.start)), c = d.cum, i = 1;
    while (i < c.length - 1 && c[i] < x) i++;
    var f = (x - c[i - 1]) / ((c[i] - c[i - 1]) || 1), a = d.line[i - 1], b = d.line[i];
    return { day: days.indexOf(d), i: i, ll: [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f] };
  }
  function altAt(km) {
    var d = days[dayAt(km)], f = Math.max(0, Math.min(1, (km - d.start) / d.km)) * (d.alt.length - 1), i = Math.floor(f);
    return d.alt[i] + (d.alt[Math.min(i + 1, d.alt.length - 1)] - d.alt[i]) * (f - i);
  }

  // ---------- profil d'altitude ----------
  var amin = Infinity, amax = -Infinity;
  days.forEach(function (d) { d.alt.forEach(function (a) { amin = Math.min(amin, a); amax = Math.max(amax, a); }); });
  amin = Math.floor(amin / 100) * 100 - 50;
  function profilePath(Wd, Hd, pad) {
    var pts = [];
    days.forEach(function (d) {
      d.alt.forEach(function (a, i) {
        var km = d.start + d.km * i / (d.alt.length - 1);
        pts.push([km / total * Wd, pad + (1 - (a - amin) / (amax - amin)) * (Hd - pad)]);
      });
    });
    var line = "M" + pts.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L");
    return { line: line, area: line + " L" + Wd + " " + Hd + " L0 " + Hd + " Z" };
  }
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  var prof = document.querySelector(".lr-prof"), pp = profilePath(600, 120, 26);
  var defs = el("defs", {}, prof), clip = el("clipPath", { id: "lr-clip" }, defs), clipRect = el("rect", { x: 0, y: 0, width: 0, height: 120 }, clip);
  el("path", { d: pp.area, class: "area" }, prof);
  el("path", { d: pp.area, class: "done", "clip-path": "url(#lr-clip)" }, prof);
  el("path", { d: pp.line, class: "line" }, prof);
  days.forEach(function (d, i) {
    var x = d.start / total * 600;
    if (i) el("line", { x1: x, x2: x, y1: 0, y2: 120, class: "sep" }, prof);
  });
  var cursor = el("line", { x1: 0, x2: 0, y1: 0, y2: 120, stroke: color, "stroke-width": 2, "vector-effect": "non-scaling-stroke" }, prof);
  // barre du haut : la silhouette de toute l'étape
  var tsvg = document.querySelector(".lr-top-svg");
  tsvg.setAttribute("viewBox", "0 0 1000 30");
  var tp = profilePath(1000, 30, 4);
  var tdefs = el("defs", {}, tsvg), tclip = el("clipPath", { id: "lr-tclip" }, tdefs), tRect = el("rect", { x: 0, y: 0, width: 0, height: 30 }, tclip);
  el("path", { d: tp.area, class: "bg" }, tsvg);
  el("path", { d: tp.area, class: "done", "clip-path": "url(#lr-tclip)" }, tsvg);
  days.forEach(function (d, i) { if (i) { var x = d.start / total * 1000; el("line", { x1: x, x2: x, y1: 0, y2: 30, class: "tick" }, tsvg); } });
  var tbike = document.querySelector(".lr-top-bike");

  // ---------- carte ----------
  var map = null, base = [], done = [], marker = null, shownDay = -1, flying = false;
  function loadLeaflet(cb) {
    if (window.L) return cb();
    var css = document.createElement("link");
    css.rel = "stylesheet"; css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);
    var s = document.createElement("script");
    s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    s.onload = cb;
    document.head.appendChild(s);
  }
  loadLeaflet(function () {
    map = L.map("lr-map", { scrollWheelZoom: false, zoomControl: true, attributionControl: true, zoomSnap: 0.25 });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
    days.forEach(function (d) {
      base.push(L.polyline(d.line, { color: color, weight: 4, opacity: 0.35 }).addTo(map));
      done.push(L.polyline([], { color: color, weight: 5.5, opacity: 1 }).addTo(map));
    });
    var all = L.latLngBounds(days.reduce(function (a, d) { return a.concat(d.line); }, []));
    map.fitBounds(all, { padding: [30, 30] });
    marker = L.marker(days[0].line[0], {
      icon: L.divIcon({ className: "", iconSize: [40, 40], iconAnchor: [20, 20], html: '<span class="lr-bike">' + document.querySelector(".lr-top-bike").innerHTML + "</span>" }),
      keyboard: false, interactive: false
    }).addTo(map);
    update(true);
  });

  // ---------- défilement → kilomètre ----------
  var blocks = [];
  document.querySelectorAll(".lr-body").forEach(function (b) {
    var d = +b.dataset.day, list = b.querySelectorAll(".lr-block");
    list.forEach(function (e, i) { blocks.push({ el: e, day: d, i: i, n: list.length, body: b }); });
  });
  var bodies = document.querySelectorAll(".lr-body"), openers = document.querySelectorAll(".lr-open");
  var target = 0, cur = 0, inBody = false;
  function measure() {
    var Y = window.innerHeight * 0.45, km = 0, found = false;
    inBody = false;
    bodies.forEach(function (b) { var r = b.getBoundingClientRect(); if (r.top < window.innerHeight * 0.6 && r.bottom > window.innerHeight * 0.35) inBody = true; });
    for (var k = 0; k < blocks.length; k++) {
      var bl = blocks[k], r = bl.el.getBoundingClientRect(), next = blocks[k + 1];
      var bottom = next && next.day === bl.day ? next.el.getBoundingClientRect().top : r.bottom;
      var d = days[bl.day];
      if (Y < r.top) { if (!found) { km = d.start; found = true; } break; }
      var f = Math.max(0, Math.min(1, (Y - r.top) / ((bottom - r.top) || 1)));
      km = d.start + d.km * (bl.i + f) / bl.n;
      found = true;
    }
    target = Math.max(0, Math.min(total, km));
    // parallaxe des grandes photos
    if (!reduce) openers.forEach(function (o) {
      var r = o.getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) return;
      o.querySelector(".lr-open-img").style.transform = "translate3d(0," + (r.top * 0.18).toFixed(1) + "px,0)";
    });
    var heroGone = document.querySelector(".lr-hero").getBoundingClientRect().bottom < 60;
    top.classList.toggle("on", heroGone);
    panel.classList.toggle("on", inBody);
    btn.classList.toggle("on", inBody || panel.classList.contains("sheet"));
  }
  var lastKm = -1;
  function update(force) {
    var p = posAt(cur), x = cur / total;
    if (map && marker) {
      marker.setLatLng(p.ll);
      days.forEach(function (d, i) {
        if (i < p.day) done[i].setLatLngs(d.line);
        else if (i > p.day) done[i].setLatLngs([]);
        else done[i].setLatLngs(d.line.slice(0, p.i).concat([p.ll]));
      });
      if (p.day !== shownDay) {
        shownDay = p.day;
        flying = true;
        map.once("moveend", function () { flying = false; });
        if (reduce) map.fitBounds(L.latLngBounds(days[p.day].line), { padding: [40, 40] });
        else map.flyToBounds(L.latLngBounds(days[p.day].line), { padding: [40, 40], duration: 1.1 });
      } else if (!flying && !map.getBounds().pad(-0.15).contains(p.ll)) {
        map.panTo(p.ll, { animate: !reduce, duration: 0.6 });
      }
    }
    clipRect.setAttribute("width", (x * 600).toFixed(1));
    cursor.setAttribute("x1", (x * 600).toFixed(1)); cursor.setAttribute("x2", (x * 600).toFixed(1));
    tRect.setAttribute("width", (x * 1000).toFixed(1));
    tbike.style.left = (x * 100).toFixed(2) + "%";
    document.querySelector(".lr-now-day").textContent = dayNames[p.day] || "";
    document.querySelector(".lr-now-km").textContent = "km " + Math.round(cur - days[p.day].start) + " sur " + Math.round(days[p.day].km);
    document.querySelector(".lr-now-alt").textContent = Math.round(altAt(cur)) + " m d'altitude";
  }
  function loop() {
    measure();
    var d = target - cur;
    cur = Math.abs(d) < 0.02 || reduce ? target : cur + d * 0.12;
    if (Math.abs(cur - lastKm) > 0.005) { lastKm = cur; update(); }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // ---------- mobile : la carte en tiroir ----------
  btn.addEventListener("click", function () {
    var open = panel.classList.toggle("sheet");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.querySelector("span").textContent = open ? "Fermer" : "La carte";
    if (map) setTimeout(function () { map.invalidateSize(); }, 380);
  });
  window.addEventListener("resize", function () { if (map) map.invalidateSize(); });
})();
