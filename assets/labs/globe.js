/* Prototype d'accueil : dix ans de voyages dessinés sur un globe, dans l'ordre */
(function () {
  "use strict";
  var BASE = window.TQA_BASE || "";
  var wrap = document.querySelector(".gl");
  if (!wrap || !window.d3 || !window.topojson) return;
  var canvas = wrap.querySelector(".gl-canvas"), ctx = canvas.getContext("2d");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s) { return wrap.querySelector(s); };
  var yearEl = $(".gl-year"), nameEl = $(".gl-name"), periodEl = $(".gl-period"), flagsEl = $(".gl-flags"), lineEl = $(".gl-line");
  var counters = {};
  wrap.querySelectorAll(".gl-count dd").forEach(function (d) { counters[d.dataset.k] = { el: d, v: 0, from: 0, to: 0 }; });

  var proj = d3.geoOrthographic().clipAngle(90).precision(0.4);
  var path = d3.geoPath(proj, ctx);
  var grat = d3.geoGraticule10();
  var land110, land50, borders, trips = [], W = 0, dpr = 1, R = 0;
  var view = { lon: -20, lat: 20, k: 1 };
  var col = {};

  function readColors() {
    var cs = getComputedStyle(document.documentElement);
    var dark = document.documentElement.dataset.theme === "dark";
    col = {
      ocean: cs.getPropertyValue("--paper-deep").trim() || "#E9DFCC",
      land: dark ? "#3A352D" : "#FBF6EC",
      coast: dark ? "rgba(237,228,211,.38)" : "rgba(42,37,33,.55)",
      grat: dark ? "rgba(237,228,211,.07)" : "rgba(42,37,33,.08)",
      border: dark ? "rgba(237,228,211,.16)" : "rgba(42,37,33,.16)",
      ink: cs.getPropertyValue("--ink").trim() || "#2A2521",
      paper: cs.getPropertyValue("--paper").trim() || "#F3ECDF",
      shade: dark ? "rgba(0,0,0,.45)" : "rgba(60,45,30,.22)"
    };
  }
  readColors();
  document.addEventListener("tqa-theme", function () { readColors(); draw(); });

  function resize() {
    var r = canvas.getBoundingClientRect();
    dpr = Math.min(2, window.devicePixelRatio || 1);
    W = Math.round(r.width);
    canvas.width = W * dpr;
    canvas.height = W * dpr;
    R = W / 2 * 0.9;
    draw();
  }

  // ---------- dessin ----------
  var state = { cur: -1, prog: 0, done: -1 };   // done : dernier voyage entièrement dessiné
  // longueur « animée » d'un tronçon : les avions passent vite, le reste au rythme de la route
  var MODE_W = { avion: 0.12 };
  function segLen(sg) {
    if (sg._len == null) sg._len = Math.max(1e-4, d3.geoLength({ type: "LineString", coordinates: sg.c })) * (MODE_W[sg.m] || 1);
    return sg._len;
  }
  // les tronçons visibles quand une fraction p du voyage est dessinée
  function partialSegs(segs, p) {
    if (p >= 1) return segs;
    var total = 0;
    segs.forEach(function (sg) { total += segLen(sg); });
    var budget = p * total, out = [];
    for (var i = 0; i < segs.length && budget > 0; i++) {
      var sg = segs[i], L = segLen(sg);
      if (budget >= L) { out.push(sg); budget -= L; continue; }
      var f = budget / L, c = sg.c, n = c.length - 1, pos = f * n, whole = Math.floor(pos), r = pos - whole;
      var part = c.slice(0, whole + 1), A = c[whole], Bp = c[Math.min(whole + 1, n)];
      part.push([A[0] + (Bp[0] - A[0]) * r, A[1] + (Bp[1] - A[1]) * r]);
      out.push({ m: sg.m, c: part, head: true });
      budget = 0;
    }
    return out;
  }
  // un style par moyen de transport : trait plein pour nos traces, rails, tirets, pointillés…
  function strokeSeg(sg, color, on, sc) {
    var w = (on ? 2.8 : 1.8) * Math.min(sc, 1.6), k = Math.min(sc, 2);
    ctx.beginPath(); path({ type: "LineString", coordinates: sg.c });
    ctx.lineJoin = "round";
    var halo = function (extra) { ctx.setLineDash([]); ctx.lineCap = "round"; ctx.strokeStyle = col.paper; ctx.globalAlpha = 0.8; ctx.lineWidth = w + extra; ctx.stroke(); ctx.globalAlpha = 1; };
    ctx.strokeStyle = color;
    switch (sg.m) {
      case "train":
        halo(2.6);
        ctx.strokeStyle = color; ctx.lineCap = "butt"; ctx.lineWidth = w * 1.25; ctx.stroke();
        ctx.setLineDash([3.2 * k, 3.2 * k]); ctx.strokeStyle = col.paper; ctx.lineWidth = w * 0.5; ctx.stroke();
        break;
      case "bus":
        halo(2.2);
        ctx.strokeStyle = color; ctx.lineCap = "butt"; ctx.setLineDash([7 * k, 4 * k]); ctx.lineWidth = w; ctx.stroke();
        break;
      case "voiture":
        halo(2.2);
        ctx.strokeStyle = color; ctx.lineCap = "butt"; ctx.setLineDash([3 * k, 3 * k]); ctx.lineWidth = w * 0.95; ctx.stroke();
        break;
      case "bateau":
        ctx.strokeStyle = color; ctx.lineCap = "round"; ctx.setLineDash([0.1, 5 * k]); ctx.lineWidth = w * 1.5; ctx.stroke();
        break;
      case "avion":
        ctx.strokeStyle = color; ctx.lineCap = "round"; ctx.setLineDash([0.1, 6 * k]); ctx.lineWidth = w * 0.9; ctx.globalAlpha = 0.6; ctx.stroke(); ctx.globalAlpha = 1;
        break;
      default: // vélo, à pied
        halo(2.6);
        ctx.strokeStyle = color; ctx.lineCap = "round"; ctx.lineWidth = sg.m === "pied" ? w * 0.8 : w; ctx.stroke();
    }
    ctx.setLineDash([]);
  }
  function visible(pt) { return d3.geoDistance(pt, [view.lon, view.lat]) < Math.PI / 2 - 0.02; }

  function draw() {
    if (!W || !land110) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, W);
    proj.translate([W / 2, W / 2]).scale(R * view.k).rotate([-view.lon, -view.lat]);
    var sc = Math.sqrt(view.k);
    // ombre portée
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(W / 2, W / 2 + R * 0.98, R * 0.7, R * 0.07, 0, 0, Math.PI * 2);
    ctx.fillStyle = col.shade;
    ctx.filter = "blur(10px)";
    if (view.k < 1.6) ctx.fill();
    ctx.restore();
    // tout ce qui suit reste dans le disque du globe, même zoomé (effet de loupe)
    ctx.save();
    ctx.beginPath(); ctx.arc(W / 2, W / 2, R, 0, Math.PI * 2); ctx.clip();
    // océan
    ctx.beginPath(); path({ type: "Sphere" }); ctx.fillStyle = col.ocean; ctx.fill();
    ctx.beginPath(); path(grat); ctx.strokeStyle = col.grat; ctx.lineWidth = 1; ctx.stroke();
    // terres
    var land = view.k > 2.5 && land50 ? land50 : land110;
    ctx.beginPath(); path(land); ctx.fillStyle = col.land; ctx.fill();
    ctx.strokeStyle = col.coast; ctx.lineWidth = 0.7; ctx.stroke();
    if (borders) { ctx.beginPath(); path(borders); ctx.setLineDash([2, 3]); ctx.strokeStyle = col.border; ctx.lineWidth = 0.7; ctx.stroke(); ctx.setLineDash([]); }
    // traces
    trips.forEach(function (t, i) {
      var p = i <= state.done ? 1 : i === state.cur ? state.prog : 0;
      if (p <= 0) return;
      var on = i === state.cur;
      var ls = partialSegs(t.segs, p);
      ls.forEach(function (sg) { strokeSeg(sg, t.color, on, sc); });
      if (on) {
        var npins = Math.floor(t.pins.length * p);
        for (var k = 0; k < npins; k++) {
          if (!visible(t.pins[k])) continue;
          var xy = proj(t.pins[k]);
          ctx.beginPath(); ctx.arc(xy[0], xy[1], 3.2, 0, Math.PI * 2);
          ctx.fillStyle = col.paper; ctx.fill(); ctx.lineWidth = 1.6; ctx.strokeStyle = t.color; ctx.stroke();
        }
        var last = ls[ls.length - 1];
        if (last && last.c.length && p < 1) {
          var head = last.c[last.c.length - 1];
          if (visible(head)) {
            var h = proj(head);
            ctx.beginPath(); ctx.arc(h[0], h[1], 6, 0, Math.PI * 2); ctx.fillStyle = t.color; ctx.fill();
            ctx.lineWidth = 2.5; ctx.strokeStyle = col.paper; ctx.stroke();
          }
        }
      }
    });
    ctx.restore();
    // liseré du globe
    ctx.beginPath(); ctx.arc(W / 2, W / 2, Math.min(R, R * view.k), 0, Math.PI * 2);
    var g = ctx.createRadialGradient(W / 2 - R * 0.3, W / 2 - R * 0.35, R * 0.1, W / 2, W / 2, R);
    g.addColorStop(0, "rgba(255,255,255,.10)"); g.addColorStop(0.7, "rgba(255,255,255,0)"); g.addColorStop(1, "rgba(0,0,0,.10)");
    ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = 1.5; ctx.strokeStyle = col.coast; ctx.stroke();
  }

  // ---------- cadrage d'un voyage ----------
  function frame(t) {
    var ground = t.segs.filter(function (sg) { return sg.m !== "avion"; }).map(function (sg) { return sg.c; });
    var all = { type: "MultiLineString", coordinates: ground.concat(t.pins.length ? [t.pins] : []) };
    var b = d3.geoBounds(all), c = d3.geoCentroid(all);
    var d = d3.geoDistance(b[0], b[1]);
    var k = Math.max(1, Math.min(5.5, 0.95 / Math.max(d, 0.07)));
    return { lon: c[0], lat: Math.max(-60, Math.min(60, c[1])), k: k };
  }
  var ease = function (x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };

  // ---------- séquence ----------
  var playing = !reduce, anim = null, timer = null;
  function setCounters(t, dur) {
    ["km", "countries", "stories"].forEach(function (k) {
      var c = counters[k];
      c.from = c.v; c.to = t ? t[k] : 0;
    });
    var t0 = performance.now();
    (function step(now) {
      var f = Math.min(1, (now - t0) / dur);
      Object.keys(counters).forEach(function (k) {
        var c = counters[k];
        c.v = Math.round(c.from + (c.to - c.from) * ease(f));
        c.el.textContent = c.v.toLocaleString("fr-FR");
      });
      if (f < 1) requestAnimationFrame(step);
    })(t0);
  }
  // légende : les moyens de transport du voyage, avec leurs kilomètres
  var LEG = [
    ["velo", "à vélo", '<path d="M2 6h30" stroke="C" stroke-width="3" stroke-linecap="round"/>'],
    ["pied", "à pied", '<path d="M2 6h30" stroke="C" stroke-width="2.2" stroke-linecap="round"/>'],
    ["train", "en train", '<path d="M2 6h30" stroke="C" stroke-width="3.6"/><path d="M2 6h30" stroke="P" stroke-width="1.4" stroke-dasharray="3 3"/>'],
    ["bus", "en car et en bus", '<path d="M2 6h30" stroke="C" stroke-width="2.6" stroke-dasharray="7 4"/>'],
    ["voiture", "en voiture", '<path d="M2 6h30" stroke="C" stroke-width="2.5" stroke-dasharray="3 3"/>'],
    ["bateau", "en bateau", '<path d="M3 6h28" stroke="C" stroke-width="3.4" stroke-linecap="round" stroke-dasharray="0.1 5"/>'],
    ["avion", "en avion", '<path d="M3 6h28" stroke="C" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="0.1 5.5" opacity=".7"/>']
  ];
  var legendEl = $(".gl-legend");
  function legend(modes, color) {
    if (!legendEl) return;
    legendEl.innerHTML = LEG.filter(function (l) { return modes && modes[l[0]]; }).map(function (l) {
      var sw = l[2].replace(/C/g, color || "currentColor").replace(/P/g, col.paper);
      return '<li><svg viewBox="0 0 34 12" width="34" height="12" aria-hidden="true">' + sw + "</svg><span>" + l[1] +
        "</span><b>" + modes[l[0]].toLocaleString("fr-FR") + " km</b></li>";
    }).join("");
  }
  function caption(t) {
    legend(t.modes, t.color);
    yearEl.textContent = t.year;
    nameEl.textContent = t.title;
    nameEl.href = BASE + t.url;
    nameEl.style.setProperty("--trip", t.color);
    periodEl.textContent = t.period;
    flagsEl.innerHTML = t.flags.replace(/ loading="lazy"/g, "");
    lineEl.querySelectorAll("li").forEach(function (li, i) {
      li.classList.toggle("on", i === state.cur);
      li.classList.toggle("done", i <= state.done);
    });
  }
  function fly(to, dur, cb) {
    cancelAnimationFrame(anim);
    var from = { lon: view.lon, lat: view.lat, k: view.k };
    var gi = d3.geoInterpolate([from.lon, from.lat], [to.lon, to.lat]);
    var dist = d3.geoDistance([from.lon, from.lat], [to.lon, to.lat]);
    var dip = Math.min(from.k, to.k, Math.max(1, 1.6 / (dist + 0.4)));
    var t0 = performance.now();
    (function step(now) {
      var f = Math.min(1, (now - t0) / dur), e = ease(f), c = gi(e);
      view.lon = c[0]; view.lat = c[1];
      var kk = f < 0.5 ? from.k + (dip - from.k) * ease(f * 2) : dip + (to.k - dip) * ease(f * 2 - 1);
      view.k = dist > 0.15 ? kk : from.k + (to.k - from.k) * e;
      draw();
      if (f < 1) anim = requestAnimationFrame(step); else if (cb) cb();
    })(t0);
  }
  function drawTrip(i, dur, cb) {
    var t0 = performance.now();
    cancelAnimationFrame(anim);
    (function step(now) {
      state.prog = Math.min(1, (now - t0) / dur);
      draw();
      if (state.prog < 1) anim = requestAnimationFrame(step); else cb();
    })(t0);
  }
  function play(i) {
    clearTimeout(timer);
    if (i >= trips.length) { return finish(); }
    var t = trips[i];
    state.cur = i; state.prog = 0; state.done = i - 1;
    caption(t);
    var f = frame(t);
    fly(f, 1500, function () {
      setCounters(t, 1900);
      drawTrip(i, 2200 + Math.min(3200, t.segs.length * 140), function () {
        state.done = i;
        caption(t);
        if (playing) timer = setTimeout(function () { play(i + 1); }, 800);
      });
    });
  }
  function finish() {
    state.cur = -1; state.done = trips.length - 1;
    var t = trips[trips.length - 1];
    yearEl.textContent = "2015 – " + t.year;
    nameEl.textContent = "Tous les voyages";
    nameEl.href = BASE + "/voyages/";
    periodEl.textContent = trips.length + " carnets, du Sri Lanka au Piémont";
    flagsEl.innerHTML = "";
    var tot = {};
    trips.forEach(function (x) { Object.keys(x.modes).forEach(function (m) { tot[m] = (tot[m] || 0) + x.modes[m]; }); });
    caption({ year: yearEl.textContent, title: nameEl.textContent, url: "/voyages/", color: "", period: periodEl.textContent, flags: "", modes: tot });
    setCounters(t, 600);
    wrap.classList.add("done");
    fly({ lon: 40, lat: 25, k: 1 }, 2000, spin);
    playBtn.textContent = "Lecture";
    playBtn.setAttribute("aria-pressed", "false");
    playing = false;
  }
  var spinning = false;
  function spin() {
    if (reduce) return;
    spinning = true;
    var last = performance.now();
    (function step(now) {
      if (!spinning) return;
      view.lon += (now - last) * 0.004;
      last = now;
      draw();
      anim = requestAnimationFrame(step);
    })(last);
  }

  // ---------- contrôles ----------
  var playBtn = $(".gl-play");
  playBtn.addEventListener("click", function () {
    playing = !playing;
    playBtn.textContent = playing ? "Pause" : "Lecture";
    playBtn.setAttribute("aria-pressed", playing ? "true" : "false");
    if (playing) { spinning = false; wrap.classList.remove("done"); play(state.cur >= 0 && state.cur > state.done ? state.cur : state.done + 1); }
    else clearTimeout(timer);
  });
  $(".gl-replay").addEventListener("click", function () {
    spinning = false; playing = true; wrap.classList.remove("done");
    playBtn.textContent = "Pause"; playBtn.setAttribute("aria-pressed", "true");
    Object.keys(counters).forEach(function (k) { counters[k].v = 0; });
    play(0);
  });
  // glisser pour faire tourner
  var drag = null;
  canvas.addEventListener("pointerdown", function (e) {
    drag = { x: e.clientX, y: e.clientY, lon: view.lon, lat: view.lat };
    spinning = false;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", function (e) {
    if (!drag) return;
    var s = 160 / (R * view.k);
    view.lon = drag.lon - (e.clientX - drag.x) * s;
    view.lat = Math.max(-75, Math.min(75, drag.lat + (e.clientY - drag.y) * s));
    if (!anim || state.prog >= 1 || !playing) draw();
  });
  canvas.addEventListener("pointerup", function () { drag = null; });

  // ---------- données ----------
  Promise.all([
    fetch(BASE + "/assets/labs/vendor/countries-110m.json").then(function (r) { return r.json(); }),
    fetch(BASE + "/labs/data/globe.json").then(function (r) { return r.json(); })
  ]).then(function (res) {
    var topo = res[0];
    land110 = topojson.merge(topo, topo.objects.countries.geometries);
    borders = topojson.mesh(topo, topo.objects.countries, function (a, b) { return a !== b; });
    trips = res[1];
    var lastLabel = -9;
    trips.forEach(function (t, i) {
      var li = document.createElement("li");
      li.style.setProperty("--c", t.color);
      var showYear = (i === 0 || trips[i - 1].year !== t.year) && i - lastLabel >= 3;
      if (showYear) lastLabel = i;
      li.innerHTML = '<button type="button" aria-label="' + t.title + ", " + t.period + '"></button>' + (showYear ? '<span class="y">' + t.year + "</span>" : "");
      li.querySelector("button").addEventListener("click", function () {
        spinning = false; wrap.classList.remove("done"); playing = true;
        playBtn.textContent = "Pause"; playBtn.setAttribute("aria-pressed", "true");
        play(i);
      });
      lineEl.appendChild(li);
    });
    resize();
    window.addEventListener("resize", resize);
    fetch(BASE + "/assets/labs/vendor/land-50m.json").then(function (r) { return r.json(); }).then(function (t50) {
      land50 = topojson.feature(t50, t50.objects.land);
      draw();
    });
    if (reduce) finish(); else setTimeout(function () { play(0); }, 500);
  });
})();
