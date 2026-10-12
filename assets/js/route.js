/* Récit au fil de la route : la carte, le profil d'altitude et la barre du haut suivent la lecture */
(function () {
  "use strict";
  var dataEl = document.getElementById("rt-data");
  var article = document.querySelector("article.prose");
  var panel = document.querySelector(".rt");
  if (!dataEl || !article || !panel) return;
  var D = JSON.parse(dataEl.textContent), acts = D.acts, color = D.color, T = D.t;
  if (!acts.length) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var top = document.querySelector(".rt-top"), btn = document.querySelector(".rt-btn");
  var last = acts[acts.length - 1], total = last.start + last.km;
  var hasAlt = acts.some(function (a) { return a.alt && a.alt.length > 1; });
  document.body.style.setProperty("--trip", color);
  if (!hasAlt) panel.classList.add("no-alt");

  // ---------- géométrie ----------
  function hav(a, b) {
    var r = Math.PI / 180, dLa = (b[0] - a[0]) * r, dLo = (b[1] - a[1]) * r;
    var s = Math.sin(dLa / 2) * Math.sin(dLa / 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLo / 2) * Math.sin(dLo / 2);
    return 12742 * Math.asin(Math.sqrt(s));
  }
  acts.forEach(function (d) {
    var c = [0];
    for (var i = 1; i < d.line.length; i++) c.push(c[i - 1] + hav(d.line[i - 1], d.line[i]));
    var f = d.km / (c[c.length - 1] || 1);
    d.cum = c.map(function (x) { return x * f; });
  });
  function actAt(km) { for (var i = acts.length - 1; i >= 0; i--) if (km >= acts[i].start - 1e-6) return i; return 0; }
  function posAt(km) {
    var k = actAt(km), d = acts[k], x = Math.max(0, Math.min(d.km, km - d.start)), c = d.cum, i = 1;
    if (d.line.length < 2) return { act: k, i: 1, ll: d.line[0] };
    while (i < c.length - 1 && c[i] < x) i++;
    var f = (x - c[i - 1]) / ((c[i] - c[i - 1]) || 1), a = d.line[i - 1], b = d.line[i];
    return { act: k, i: i, ll: [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f] };
  }
  function altAt(km) {
    var d = acts[actAt(km)];
    if (!d.alt) return null;
    var f = Math.max(0, Math.min(1, (km - d.start) / (d.km || 1))) * (d.alt.length - 1), i = Math.floor(f);
    return d.alt[i] + (d.alt[Math.min(i + 1, d.alt.length - 1)] - d.alt[i]) * (f - i);
  }

  // ---------- profil d'altitude ----------
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  var amin = Infinity, amax = -Infinity;
  acts.forEach(function (d) { (d.alt || []).forEach(function (a) { amin = Math.min(amin, a); amax = Math.max(amax, a); }); });
  if (hasAlt) { var span = Math.max(120, amax - amin); amin = amin - span * 0.12; amax = amin + span * 1.15; }
  function profile(Wd, Hd, pad) {
    var line = "", area = "";
    acts.forEach(function (d) {
      var x0 = d.start / total * Wd, x1 = (d.start + d.km) / total * Wd;
      if (!d.alt || d.alt.length < 2) { area += "M" + x0.toFixed(1) + " " + Hd + " L" + x1.toFixed(1) + " " + Hd + " "; return; }
      var pts = d.alt.map(function (a, i) {
        return [(x0 + (x1 - x0) * i / (d.alt.length - 1)).toFixed(1), (pad + (1 - (a - amin) / (amax - amin)) * (Hd - pad)).toFixed(1)];
      });
      var l = "M" + pts.map(function (p) { return p[0] + " " + p[1]; }).join(" L");
      line += l + " ";
      area += l + " L" + x1.toFixed(1) + " " + Hd + " L" + x0.toFixed(1) + " " + Hd + " Z ";
    });
    return { line: line, area: area };
  }
  var prof = panel.querySelector(".rt-prof"), clipRect = null, cursor = null;
  if (prof && hasAlt) {
    var pp = profile(600, 110, 16);
    var uid = "rt" + Math.random().toString(36).slice(2, 7);
    var clip = el("clipPath", { id: uid }, el("defs", {}, prof));
    clipRect = el("rect", { x: 0, y: 0, width: 0, height: 110 }, clip);
    el("path", { d: pp.area, class: "area" }, prof);
    el("path", { d: pp.area, class: "done", "clip-path": "url(#" + uid + ")" }, prof);
    el("path", { d: pp.line, class: "line" }, prof);
    acts.forEach(function (d, i) { if (i) { var x = d.start / total * 600; el("line", { x1: x, x2: x, y1: 0, y2: 110, class: "sep" }, prof); } });
    cursor = el("line", { x1: 0, x2: 0, y1: 0, y2: 110, class: "cur" }, prof);
  }
  // barre du haut : la silhouette de tout le récit
  var tRect = null, tbike = null;
  if (top) {
    var tsvg = top.querySelector(".rt-top-svg");
    tsvg.setAttribute("viewBox", "0 0 1000 30");
    var tid = "rtt" + Math.random().toString(36).slice(2, 7);
    var tclip = el("clipPath", { id: tid }, el("defs", {}, tsvg));
    tRect = el("rect", { x: 0, y: 0, width: 0, height: 30 }, tclip);
    var tp = hasAlt ? profile(1000, 30, 5).area : "M0 18 H1000 V30 H0 Z";
    el("path", { d: tp, class: "bg" }, tsvg);
    el("path", { d: tp, class: "done", "clip-path": "url(#" + tid + ")" }, tsvg);
    acts.forEach(function (d, i) { if (i) { var x = d.start / total * 1000; el("line", { x1: x, x2: x, y1: 0, y2: 30, class: "tick" }, tsvg); } });
    tbike = top.querySelector(".rt-top-bike");
  }

  // ---------- carte ----------
  var map = null, done = [], marker = null, shownAct = -1, flying = false;
  function loadLeaflet(cb) {
    if (window.L) return cb();
    if (!document.querySelector('link[href*="leaflet.css"]')) {
      var css = document.createElement("link");
      css.rel = "stylesheet"; css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(css);
    }
    var s = document.querySelector('script[src*="leaflet.js"]');
    if (s) { s.addEventListener("load", cb); return; }
    s = document.createElement("script");
    s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    s.onload = cb;
    document.head.appendChild(s);
  }
  function bounds(d) { return L.latLngBounds(d.line.length ? d.line : [[0, 0]]); }
  loadLeaflet(function () {
    map = L.map(panel.querySelector(".rt-map"), { scrollWheelZoom: false, zoomControl: true, attributionControl: true, zoomSnap: 0.25 });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
    acts.forEach(function (d) {
      L.polyline(d.line, { color: color, weight: 3.5, opacity: 0.32, interactive: false }).addTo(map);
      done.push(L.polyline([], { color: color, weight: 5, opacity: 1, interactive: false }).addTo(map));
    });
    map.fitBounds(L.latLngBounds(acts.reduce(function (a, d) { return a.concat(d.line); }, [])), { padding: [24, 24] });
    var icon = top ? top.querySelector(".rt-top-bike").innerHTML : "";
    marker = L.marker(acts[0].line[0], {
      icon: L.divIcon({ className: "", iconSize: [34, 34], iconAnchor: [17, 17], html: '<span class="rt-bike">' + icon + "</span>" }),
      keyboard: false, interactive: false
    }).addTo(map);
    update();
  });

  // ---------- défilement → kilomètre ----------
  var marks = Array.prototype.map.call(article.querySelectorAll("h4[data-acts]"), function (h) {
    var r = h.getAttribute("data-acts").split(",");
    return { el: h, a0: +r[0], a1: +r[1] };
  });
  var endEl = article.querySelector(".tracks, .post-nav2");
  function bottomOf() { return endEl ? endEl.getBoundingClientRect().top : article.getBoundingClientRect().bottom; }
  var target = 0, cur = 0, reading = false;
  function measure() {
    var Y = window.innerHeight * 0.45, km = 0;
    var ar = article.getBoundingClientRect(), bot = bottomOf();
    reading = ar.top < window.innerHeight * 0.5 && bot > window.innerHeight * 0.2;
    if (marks.length) {
      var k = -1;
      for (var i = 0; i < marks.length; i++) if (marks[i].el.getBoundingClientRect().top <= Y) k = i;
      if (k < 0) km = acts[marks[0].a0].start;
      else {
        var m = marks[k], t0 = m.el.getBoundingClientRect().top, t1 = k + 1 < marks.length ? marks[k + 1].el.getBoundingClientRect().top : bot;
        var f = Math.max(0, Math.min(1, (Y - t0) / ((t1 - t0) || 1)));
        var k0 = acts[m.a0].start, k1 = acts[m.a1].start + acts[m.a1].km;
        km = k0 + (k1 - k0) * f;
      }
    } else {
      var f2 = Math.max(0, Math.min(1, (Y - ar.top) / ((bot - ar.top) || 1)));
      km = total * f2;
    }
    target = Math.max(0, Math.min(total, km));
    if (top) top.classList.toggle("on", reading);
    if (btn) btn.classList.toggle("on", reading || panel.classList.contains("sheet"));
  }
  var dayEl = panel.querySelector(".rt-day"), kmEl = panel.querySelector(".rt-km"), altEl = panel.querySelector(".rt-alt");
  function update() {
    var p = posAt(cur), x = cur / total, d = acts[p.act];
    if (map && marker) {
      marker.setLatLng(p.ll);
      acts.forEach(function (a, i) {
        if (i < p.act) done[i].setLatLngs(a.line);
        else if (i > p.act) done[i].setLatLngs([]);
        else done[i].setLatLngs(a.line.slice(0, p.i).concat([p.ll]));
      });
      var visible = panel.offsetParent !== null && panel.getBoundingClientRect().height > 0;
      if (p.act !== shownAct && visible) {
        shownAct = p.act;
        flying = true;
        map.once("moveend", function () { flying = false; });
        if (reduce) map.fitBounds(bounds(d), { padding: [28, 28] });
        else map.flyToBounds(bounds(d), { padding: [28, 28], duration: 1 });
      } else if (!flying && visible && !map.getBounds().pad(-0.12).contains(p.ll)) {
        map.panTo(p.ll, { animate: !reduce, duration: 0.5 });
      }
    }
    if (clipRect) { clipRect.setAttribute("width", (x * 600).toFixed(1)); cursor.setAttribute("x1", (x * 600).toFixed(1)); cursor.setAttribute("x2", (x * 600).toFixed(1)); }
    if (tRect) tRect.setAttribute("width", (x * 1000).toFixed(1));
    if (tbike) tbike.style.left = (x * 100).toFixed(2) + "%";
    dayEl.textContent = d.day;
    kmEl.textContent = T.km.replace("{a}", Math.round(cur - d.start)).replace("{b}", Math.round(d.km));
    var al = altAt(cur);
    altEl.textContent = al == null ? "" : T.alt.replace("{a}", Math.round(al));
  }
  var lastKm = -1, ticking = false;
  function loop() {
    var dlt = target - cur;
    cur = Math.abs(dlt) < 0.02 || reduce ? target : cur + dlt * 0.14;
    if (Math.abs(cur - lastKm) > 0.005) { lastKm = cur; update(); }
    if (Math.abs(target - cur) > 0.01) requestAnimationFrame(loop); else ticking = false;
  }
  function onScroll() {
    measure();
    if (!ticking) { ticking = true; requestAnimationFrame(loop); }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", function () { onScroll(); if (map) map.invalidateSize(); });
  measure();
  cur = target;
  update();

  // ---------- mobile : la carte en tiroir ----------
  if (btn) btn.addEventListener("click", function () {
    var open = panel.classList.toggle("sheet");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.querySelector("span").textContent = open ? T.close : T.map;
    shownAct = -1;
    if (map) setTimeout(function () { map.invalidateSize(); update(); }, 380);
  });
})();
