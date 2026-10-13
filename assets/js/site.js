// Mode nuit, recherche instantanée, visionneuse de photos, passeport
(function () {
  "use strict";
  var BASE = window.TQA_BASE || "";
  var root = document.documentElement;
  var EN = root.lang === "en";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var TX = EN ? {
    none: "No story mentions “{q}”. Try a place or a shorter word.", placeholder: "A place, a word, a memory…", search: "Search the stories",
    photos: "Photos from the story", close: "Close", prev: "Previous photo", next: "Next photo",
    tags: ["whales", "puncture", "playground", "kangaroo", "tunnel", "focaccia"]
  } : {
    none: "Aucun récit ne contient « {q} ». Essayez un lieu ou un mot plus court.", placeholder: "Un lieu, un mot, un souvenir…", search: "Rechercher dans les récits",
    photos: "Photos du récit", close: "Fermer", prev: "Photo précédente", next: "Photo suivante",
    tags: ["baleines", "crevaison", "aire de jeux", "kangourou", "tunnel", "focaccia"]
  };

  // ---------- Mode nuit ----------
  var meta = document.querySelector('meta[name="theme-color"]');
  function isDark() { return root.dataset.theme === "dark" || (!root.dataset.theme && window.matchMedia("(prefers-color-scheme: dark)").matches); }
  function paint() {
    var dark = isDark();
    if (!root.dataset.theme && dark) root.dataset.theme = "dark";
    document.querySelectorAll(".theme-btn").forEach(function (b) { b.setAttribute("aria-label", dark ? b.dataset.light : b.dataset.dark); b.setAttribute("aria-pressed", dark ? "true" : "false"); });
    if (meta) meta.setAttribute("content", dark ? "#1C1A16" : "#F3ECDF");
  }
  paint();
  function setTheme(dark) {
    var apply = function () {
      root.dataset.theme = dark ? "dark" : "light";
      try { localStorage.setItem("tqa-theme", root.dataset.theme); } catch (e) {}
      paint();
      document.dispatchEvent(new CustomEvent("tqa-theme"));
    };
    if (document.startViewTransition && !reduce) document.startViewTransition(apply); else apply();
  }
  document.querySelectorAll(".theme-btn").forEach(function (b) { b.addEventListener("click", function () { setTheme(!isDark()); }); });

  // ---------- Photos : aperçu flou, puis nettes ----------
  document.querySelectorAll("img[data-lq]").forEach(function (im) {
    var done = function () { im.classList.add("lq-in"); };
    if (im.complete && im.naturalWidth) done(); else { im.addEventListener("load", done); im.addEventListener("error", done); }
  });

  // ---------- Recherche ----------
  var idx = null;
  function norm(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function load() {
    if (!idx) idx = fetch(BASE + root.dataset.search).then(function (r) { return r.json(); }).then(function (rows) {
      rows.forEach(function (r) { r.nt = norm(r.t); r.nj = norm(r.j); r.nx = norm(r.x); });
      return rows;
    });
    return idx;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function mark(text, terms) {
    var n = norm(text), out = "", i = 0;
    if (n.length !== text.length) return esc(text);
    while (i < text.length) {
      var hit = 0;
      for (var k = 0; k < terms.length; k++) {
        if (terms[k] && n.substr(i, terms[k].length) === terms[k] && (i === 0 || /[^a-z0-9]/.test(n[i - 1]))) hit = Math.max(hit, terms[k].length);
      }
      if (hit) { out += "<mark>" + esc(text.substr(i, hit)) + "</mark>"; i += hit; } else { out += esc(text[i]); i++; }
    }
    return out;
  }
  function snippet(r, terms) {
    var pos = -1;
    for (var i = 0; i < terms.length && pos < 0; i++) pos = r.nx.indexOf(terms[i]);
    if (pos < 0) return esc(r.x.slice(0, 150)) + "…";
    var a = Math.max(0, r.x.lastIndexOf(" ", Math.max(0, pos - 70)));
    var b = r.x.indexOf(" ", Math.min(r.x.length, pos + 110));
    if (b < 0) b = r.x.length;
    return (a > 0 ? "…" : "") + mark(r.x.slice(a, b), terms) + (b < r.x.length ? "…" : "");
  }
  function search(rows, q) {
    var terms = norm(q).split(/[^a-z0-9]+/).filter(function (t) { return t.length > 1; });
    if (!terms.length) return { terms: terms, hits: [] };
    var hits = [];
    rows.forEach(function (r) {
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var re = new RegExp("(^|[^a-z0-9])" + terms[i].replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g"), s = 0;
        if (re.test(r.nt)) s += 12;
        re.lastIndex = 0;
        if (re.test(r.nj)) s += 6;
        re.lastIndex = 0;
        var m = r.nx.match(re);
        if (m) s += Math.min(8, m.length) + 2;
        if (!s) return;
        score += s;
      }
      hits.push({ r: r, s: score });
    });
    hits.sort(function (a, b) { return b.s - a.s; });
    return { terms: terms, hits: hits.slice(0, 30) };
  }
  var ov = null, input, list, cur = -1, lastFocus = null, timer;
  function render() {
    var q = input.value.trim();
    if (q.length < 2) { list.innerHTML = ""; return; }
    load().then(function (rows) {
      var res = search(rows, q);
      if (!res.hits.length) { list.innerHTML = '<li class="none">' + esc(TX.none.replace("{q}", q)) + "</li>"; return; }
      list.innerHTML = res.hits.map(function (h) {
        var r = h.r;
        return '<li><a href="' + BASE + r.u + '">' + (r.c ? '<img class="c" src="' + (r.c.charAt(0) === "/" ? BASE + r.c : r.c) + '" alt="" loading="lazy">' : "<span></span>") +
          "<span><b>" + mark(r.t, res.terms) + '</b><span class="m">' + r.f.replace(/src="\//g, 'src="' + BASE + "/") + esc(r.j ? r.j + ", " : "") + esc(r.d) + '</span><span class="s">' + snippet(r, res.terms) + "</span></span></a></li>";
      }).join("");
      cur = -1;
    });
  }
  function build() {
    ov = document.createElement("div");
    ov.className = "sr-ov";
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-modal", "true");
    ov.setAttribute("aria-label", TX.search);
    ov.innerHTML = '<div class="sr-box"><label class="sr-field"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>' +
      '<input type="search" placeholder="' + TX.placeholder + '" aria-label="' + TX.search + '" autocomplete="off"><button type="button" class="sr-x" aria-label="' + TX.close + '">×</button></label>' +
      '<div class="sr-tags">' + TX.tags.map(function (t) { return '<button type="button">' + t + "</button>"; }).join("") + '</div><ol class="sr-results" aria-live="polite"></ol></div>';
    document.body.appendChild(ov);
    input = ov.querySelector("input");
    list = ov.querySelector(".sr-results");
    input.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(render, 60); });
    input.addEventListener("keydown", function (e) {
      var links = list.querySelectorAll("a");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        cur = Math.max(0, Math.min(links.length - 1, cur + (e.key === "ArrowDown" ? 1 : -1)));
        links.forEach(function (a, i) { a.classList.toggle("on", i === cur); });
        if (links[cur]) links[cur].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && links[Math.max(cur, 0)]) { links[Math.max(cur, 0)].click(); }
    });
    ov.querySelectorAll(".sr-tags button").forEach(function (b) { b.addEventListener("click", function () { input.value = b.textContent; render(); input.focus(); }); });
    ov.querySelector(".sr-x").addEventListener("click", closeSearch);
    ov.addEventListener("click", function (e) { if (e.target === ov) closeSearch(); });
  }
  function openSearch() {
    if (!ov) build();
    lastFocus = document.activeElement;
    load();
    ov.classList.add("on");
    document.body.style.overflow = "hidden";
    input.focus();
    input.select();
  }
  function closeSearch() { if (ov) { ov.classList.remove("on"); document.body.style.overflow = ""; if (lastFocus && lastFocus.focus) lastFocus.focus(); } }
  document.querySelectorAll(".search-btn").forEach(function (b) { b.addEventListener("click", openSearch); });
  document.addEventListener("keydown", function (e) {
    var t = e.target.tagName;
    if (e.key === "/" && t !== "INPUT" && t !== "TEXTAREA" && !e.target.isContentEditable) { e.preventDefault(); openSearch(); }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openSearch(); }
    if (e.key === "Escape" && ov && ov.classList.contains("on")) closeSearch();
  });

  // ---------- Passeport : le carnet s'ouvre, les visas se posent un par un ----------
  var book = document.querySelector(".ps-book");
  if (book) {
    var cover = book.querySelector(".ps-cover");
    var openBook = function () { book.dataset.open = "true"; cover.setAttribute("aria-expanded", "true"); };
    cover.addEventListener("click", openBook);
    if (reduce) openBook();
    else if ("IntersectionObserver" in window) {
      var pio = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.intersectionRatio > 0.5) { setTimeout(openBook, 900); pio.disconnect(); } }); }, { threshold: [0.5] });
      pio.observe(cover);
    }
  }

  // ---------- Visionneuse : glisser au doigt, double-tap pour zoomer ----------
  var pics = Array.prototype.slice.call(document.querySelectorAll(".prose img")).filter(function (im) {
    return !im.closest(".post-nav2, .pv, .trk, .tracks, .strava-card, a[href]:not([href*='/media/']):not([href*='wp-content'])") && !im.classList.contains("flag");
  });
  if (!pics.length) return;
  var vw = document.createElement("div");
  vw.className = "vw";
  vw.setAttribute("role", "dialog");
  vw.setAttribute("aria-modal", "true");
  vw.setAttribute("aria-label", TX.photos);
  vw.innerHTML = '<div class="vw-top"><span class="vw-count"></span><button type="button" class="vw-close" aria-label="' + TX.close + '">×</button></div>' +
    '<div class="vw-stage"><div class="vw-track"></div><button type="button" class="vw-nav vw-prev" aria-label="' + TX.prev + '">‹</button><button type="button" class="vw-nav vw-next" aria-label="' + TX.next + '">›</button></div>' +
    '<p class="vw-cap"></p><div class="vw-thumbs"></div>';
  document.body.appendChild(vw);
  var track = vw.querySelector(".vw-track"), thumbs = vw.querySelector(".vw-thumbs"), count = vw.querySelector(".vw-count"), cap = vw.querySelector(".vw-cap");
  function caption(im) {
    var f = im.closest("figure");
    var c = f && f.querySelector("figcaption");
    return c ? c.textContent.trim() : (im.alt || "");
  }
  pics.forEach(function (im, i) {
    var s = document.createElement("div");
    s.className = "vw-slide";
    s.innerHTML = '<img alt="" draggable="false">';
    track.appendChild(s);
    var t = document.createElement("img");
    t.alt = "";
    t.loading = "lazy";
    t.dataset.src = im.currentSrc || im.src;
    t.addEventListener("click", function () { go(i); });
    thumbs.appendChild(t);
    im.style.cursor = "zoom-in";
    im.addEventListener("click", function (e) {
      var a = im.closest("a");
      if (a) e.preventDefault();
      open(i, im);
    });
  });
  var slides = track.children, at = 0, opened = false;
  function fill(i) {
    if (i < 0 || i >= pics.length) return;
    var img = slides[i].querySelector("img");
    if (!img.getAttribute("src")) {
      var a = pics[i].closest("a[href*='/media/'], a[href*='wp-content']");
      img.src = a ? a.href : (pics[i].currentSrc || pics[i].src);
    }
  }
  function go(i, instant) {
    at = Math.max(0, Math.min(pics.length - 1, i));
    fill(at); fill(at - 1); fill(at + 1);
    track.style.transition = instant || reduce ? "none" : "transform .35s cubic-bezier(.2,.8,.2,1)";
    track.style.transform = "translateX(" + (-at * 100) + "%)";
    count.textContent = (at + 1) + " / " + pics.length;
    cap.textContent = caption(pics[at]);
    Array.prototype.forEach.call(thumbs.children, function (t, k) {
      if (Math.abs(k - at) < 12 && !t.src) t.src = t.dataset.src;
      t.classList.toggle("on", k === at);
    });
    if (thumbs.children[at]) thumbs.children[at].scrollIntoView({ block: "nearest", inline: "center" });
    Array.prototype.forEach.call(slides, function (s) { s.querySelector("img").classList.remove("zoom"); });
  }
  function open(i, from) {
    var show = function () { vw.classList.add("on"); opened = true; go(i, true); document.body.style.overflow = "hidden"; vw.querySelector(".vw-close").focus(); };
    if (document.startViewTransition && !reduce && from) {
      var prev = from.style.viewTransitionName;
      from.style.viewTransitionName = "vw-photo";
      var t = document.startViewTransition(function () {
        from.style.viewTransitionName = prev || "";
        show();
        slides[i].querySelector("img").style.viewTransitionName = "vw-photo";
      });
      t.finished.then(function () { slides[i].querySelector("img").style.viewTransitionName = ""; });
    } else show();
  }
  function close() {
    vw.classList.remove("on"); opened = false; document.body.style.overflow = "";
    if (pics[at]) pics[at].scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
  }
  vw.querySelector(".vw-close").addEventListener("click", close);
  vw.querySelector(".vw-prev").addEventListener("click", function () { go(at - 1); });
  vw.querySelector(".vw-next").addEventListener("click", function () { go(at + 1); });
  document.addEventListener("keydown", function (e) {
    if (!opened) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") go(at - 1);
    if (e.key === "ArrowRight") go(at + 1);
  });
  var x0 = null, y0 = 0, dx = 0, lastTap = 0, w0 = 1;
  var stage = vw.querySelector(".vw-stage");
  stage.addEventListener("pointerdown", function (e) {
    if (e.target.closest("button")) return;
    var now = Date.now();
    if (now - lastTap < 300) { slides[at].querySelector("img").classList.toggle("zoom"); lastTap = 0; return; }
    lastTap = now;
    x0 = e.clientX; y0 = e.clientY; dx = 0; w0 = stage.clientWidth;
    track.style.transition = "none";
    stage.setPointerCapture(e.pointerId);
  });
  stage.addEventListener("pointermove", function (e) {
    if (x0 === null) return;
    dx = e.clientX - x0;
    var edge = (at === 0 && dx > 0) || (at === pics.length - 1 && dx < 0) ? 0.35 : 1;
    track.style.transform = "translateX(calc(" + (-at * 100) + "% + " + (dx * edge) + "px))";
  });
  function end(e) {
    if (x0 === null) return;
    var dy = e.clientY - y0;
    x0 = null;
    if (Math.abs(dy) > 120 && Math.abs(dy) > Math.abs(dx)) { close(); return; }
    if (dx < -w0 * 0.18) go(at + 1); else if (dx > w0 * 0.18) go(at - 1); else go(at);
  }
  stage.addEventListener("pointerup", end);
  stage.addEventListener("pointercancel", end);
})();

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

  function decode(str) {
    var pts = [], i = 0, lat = 0, lng = 0;
    while (i < str.length) {
      for (var k = 0; k < 2; k++) {
        var r = 0, sh = 0, b;
        do { b = str.charCodeAt(i++) - 63; r |= (b & 31) << sh; sh += 5; } while (b >= 32);
        var d = (r & 1) ? ~(r >> 1) : (r >> 1);
        if (k === 0) lat += d; else lng += d;
      }
      pts.push([lat / 1e5, lng / 1e5]);
    }
    return pts;
  }

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Trace qui se dessine quand la carte devient visible
  function animate(el, lines) {
    if (reduce || !lines.length || !("IntersectionObserver" in window)) return;
    lines.forEach(function (ln) {
      var p = ln.getElement && ln.getElement();
      if (!p || !p.getTotalLength) return;
      var len = p.getTotalLength();
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len;
    });
    var io = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return;
      io.disconnect();
      lines.forEach(function (ln, i) {
        var p = ln.getElement();
        if (!p) return;
        p.style.transition = "stroke-dashoffset 2.4s ease-in-out " + (i * 0.35) + "s";
        p.style.strokeDashoffset = 0;
        setTimeout(function () { p.style.strokeDasharray = ""; p.style.strokeDashoffset = ""; p.style.transition = ""; }, 2600 + i * 350);
      });
    }, { threshold: 0.35 });
    io.observe(el);
  }

  function draw(el) {
    var data = JSON.parse(el.getAttribute("data-map"));
    var map = L.map(el, { scrollWheelZoom: false, attributionControl: true, zoomSnap: 0.25 });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map);
    var bounds = [], pointBounds = [], hlBounds = [], hl = {};
    (data.hl || []).forEach(function (id) { hl[id] = true; });
    var hasHl = (data.hl || []).length > 0;
    function fit() {
      var b = data.fit === "hl" && hlBounds.length ? hlBounds : (data.fit === "points" && pointBounds.length ? pointBounds : bounds);
      if (b.length === 1) map.setView(b[0], 9);
      else if (b.length) map.fitBounds(b, { padding: [30, 30], maxZoom: data.fit === "hl" ? 13 : 11 });
      else map.setView([30, 10], 2);
    }
    (data.lines || []).forEach(function (ln) {
      L.polyline(ln.points, { color: ln.color || "#2F5D50", weight: ln.weight || 3, opacity: ln.mode ? .75 : .9, dashArray: ln.dash || null, lineCap: ln.mode ? "round" : "butt", interactive: false }).addTo(map);
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
      pointBounds.push([p.lat, p.lng]);
    });
    fit();
    var tracks = data.tracks || [];
    if (!tracks.length) return;
    var pending = tracks.length, drawn = [];
    tracks.forEach(function (tr) {
      fetch(tr.src).then(function (r) { return r.json(); }).then(function (list) {
        list.forEach(function (it) {
          var pts = decode(it[1]);
          var on = hl[it[0]];
          var line = L.polyline(pts, {
            color: tr.color, weight: on ? 5 : (hasHl ? 2.5 : 3.2), opacity: on ? 1 : (hasHl ? .45 : .9), lineCap: "round", lineJoin: "round"
          }).addTo(map);
          if (/^\d+$/.test(String(it[0]))) {  // traces redessinées : pas de lien Strava
            line.bindTooltip("Strava ↗", { sticky: true, direction: "top" });
            line.on("click", function () { window.open("https://www.strava.com/activities/" + it[0], "_blank", "noopener"); });
          }
          if (on) { line.bringToFront(); drawn.push(line); pts.forEach(function (p) { hlBounds.push(p); }); }
          pts.forEach(function (p) { bounds.push(p); });
        });
      }).catch(function () {}).then(function () {
        if (--pending === 0) {
          fit();
          drawn.forEach(function (l) { l.bringToFront(); });
          animate(el, drawn.length ? drawn : []);
        }
      });
    });
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

// Fin de voyage : le voyageur file vers le voyage suivant quand on arrive au bout de la route
(function () {
  var el = document.querySelector(".route-next");
  if (!el || !("IntersectionObserver" in window)) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  el.classList.add("armed");
  var io = new IntersectionObserver(function (es) {
    if (!es[0].isIntersecting) return;
    io.disconnect();
    el.classList.add("in");
    setTimeout(function () { el.classList.add("done"); }, 2400);
  }, { threshold: 0.25 });
  io.observe(el);
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
  var targets = article.querySelectorAll(":scope > img, :scope > figure, :scope > .gallery, :scope > .mosaic > .mz, :scope > video, :scope > h3, :scope > h4, :scope > blockquote, :scope > .strava-card, :scope > .trk, .trk-list > .trk, :scope > .tracks");
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -10% 0px" });
  Array.prototype.forEach.call(targets, function (t) { t.classList.add("rv"); io.observe(t); });
})();


/* « Ce jour-là » : un récit écrit à la même date, une autre année */
(function () {
  var el = document.getElementById("otd-data");
  if (!el) return;
  var D;
  try { D = JSON.parse(el.textContent); } catch (e) { return; }
  var now = new Date(), y = now.getFullYear();
  function doy(m, d) { return Math.round((Date.UTC(2001, m - 1, d) - Date.UTC(2001, 0, 1)) / 864e5); }
  var today = doy(now.getMonth() + 1, now.getDate());
  var best = [], bestGap = 99;
  D.rows.forEach(function (r) {
    var ry = +r.d.slice(0, 4);
    if (ry >= y) return;
    var g = Math.abs(doy(+r.d.slice(5, 7), +r.d.slice(8, 10)) - today);
    g = Math.min(g, 365 - g);
    if (g > 4) return;
    if (g < bestGap) { bestGap = g; best = [r]; } else if (g === bestGap) best.push(r);
  });
  if (!best.length) return;
  var r = best[(now.getDate() + now.getMonth() * 31) % best.length];
  var n = y - +r.d.slice(0, 4);
  var when = bestGap === 0 ? (n === 1 ? D.t.years[0] : D.t.years[1].replace("{n}", n)) : D.t.near.replace("{n}", n);
  var dt = new Date(r.d + "T12:00:00");
  var nice = dt.toLocaleDateString(D.lang === "fr" ? "fr-FR" : "en-GB", { day: "numeric", month: "long", year: "numeric" });
  var sec = el.parentNode, a = sec.querySelector(".otd-card");
  a.href = r.u;
  a.style.setProperty("--k", r.k);
  if (r.c) sec.querySelector(".otd-img").style.backgroundImage = "url('" + r.c + "')";
  sec.querySelector(".otd-when").textContent = when + " · " + nice + (r.v ? " · " + r.v : "");
  sec.querySelector(".otd-title").textContent = r.t;
  sec.querySelector(".otd-ex").textContent = r.e;
  sec.querySelector(".otd-go").textContent = D.t.read;
  sec.hidden = false;
})();
