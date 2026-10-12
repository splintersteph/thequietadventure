/* The Quiet Adventure — prototypes : réglages communs (mode nuit, recherche, photos, visionneuse) */
(function () {
  "use strict";
  var BASE = window.TQA_BASE || "";
  var root = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- Mode nuit ----------
  var nav = document.getElementById("nav");
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>';
  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';
  if (!root.dataset.theme && window.matchMedia("(prefers-color-scheme: dark)").matches) root.dataset.theme = "dark";
  function isDark() { return root.dataset.theme === "dark"; }
  function setTheme(dark) {
    var apply = function () {
      root.dataset.theme = dark ? "dark" : "light";
      try { localStorage.setItem("tqa-theme", root.dataset.theme); } catch (e) {}
      document.querySelectorAll(".theme-btn").forEach(function (b) {
        b.innerHTML = dark ? SUN : MOON;
        b.setAttribute("aria-label", dark ? "Passer en mode jour" : "Passer en mode nuit");
      });
      document.dispatchEvent(new CustomEvent("tqa-theme"));
    };
    if (document.startViewTransition && !reduce) document.startViewTransition(apply); else apply();
  }
  if (nav) {
    var sb = document.createElement("button");
    sb.type = "button";
    sb.className = "search-btn";
    sb.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Chercher <kbd>/</kbd>';
    nav.appendChild(sb);
    var tb = document.createElement("button");
    tb.type = "button";
    tb.className = "theme-btn";
    nav.appendChild(tb);
    tb.innerHTML = isDark() ? SUN : MOON;
    tb.setAttribute("aria-label", isDark() ? "Passer en mode jour" : "Passer en mode nuit");
    tb.addEventListener("click", function () { setTheme(!isDark()); });
    sb.addEventListener("click", function () { openSearch(); });
  }
  document.querySelectorAll(".lx-theme").forEach(function (b) { b.addEventListener("click", function () { setTheme(!isDark()); }); });

  // ---------- Photos : flou puis net ----------
  function lqInit(scope) {
    (scope || document).querySelectorAll(".lq:not(.ready)").forEach(function (w) {
      w.classList.add("ready");
      var im = w.querySelector("img");
      var done = function () { w.classList.add("in"); };
      if (im.complete && im.naturalWidth) done(); else { im.addEventListener("load", done); im.addEventListener("error", done); }
    });
  }
  lqInit();

  // ---------- Recherche ----------
  var idx = {};
  function norm(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function load(lang) {
    if (!idx[lang]) idx[lang] = fetch(BASE + "/labs/data/search-" + lang + ".json").then(function (r) { return r.json(); }).then(function (rows) {
      rows.forEach(function (r) { r.nt = norm(r.t); r.nj = norm(r.j); r.nx = norm(r.x); });
      return rows;
    });
    return idx[lang];
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function snippet(r, terms) {
    var pos = -1;
    for (var i = 0; i < terms.length && pos < 0; i++) pos = r.nx.indexOf(terms[i]);
    if (pos < 0) return esc(r.x.slice(0, 150)) + "…";
    var a = Math.max(0, r.x.lastIndexOf(" ", Math.max(0, pos - 70)));
    var b = r.x.indexOf(" ", Math.min(r.x.length, pos + 110));
    if (b < 0) b = r.x.length;
    return (a > 0 ? "…" : "") + mark(r.x.slice(a, b), terms) + (b < r.x.length ? "…" : "");
  }
  function mark(text, terms) {
    var n = norm(text), out = "", i = 0;
    while (i < text.length) {
      var hit = 0;
      for (var k = 0; k < terms.length; k++) {
        if (terms[k] && n.substr(i, terms[k].length) === terms[k] && (i === 0 || /[^a-z0-9]/.test(n[i - 1]))) { hit = Math.max(hit, terms[k].length); }
      }
      if (hit) { out += "<mark>" + esc(text.substr(i, hit)) + "</mark>"; i += hit; } else { out += esc(text[i]); i++; }
    }
    return out;
  }
  function search(rows, q) {
    var terms = norm(q).split(/[^a-z0-9]+/).filter(function (t) { return t.length > 1; });
    if (!terms.length) return { terms: terms, hits: [] };
    var hits = [];
    rows.forEach(function (r) {
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var t = terms[i], re = new RegExp("(^|[^a-z0-9])" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g");
        var s = 0;
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
  function wire(box, lang) {
    var input = box.querySelector("input"), list = box.querySelector(".sr-results"), cur = -1, timer;
    function render() {
      var q = input.value.trim();
      if (q.length < 2) { list.innerHTML = ""; return; }
      load(lang).then(function (rows) {
        var res = search(rows, q);
        if (!res.hits.length) { list.innerHTML = '<li class="none">Aucun récit ne contient « ' + esc(q) + ' ». Essayez un lieu ou un mot plus court.</li>'; return; }
        list.innerHTML = res.hits.map(function (h) {
          var r = h.r;
          return '<li><a href="' + BASE + r.u + '">' + (r.c ? '<img class="c" src="' + r.c + '" alt="" loading="lazy">' : '<span></span>') +
            '<span><b>' + mark(r.t, res.terms) + '</b><span class="m">' + r.f + esc(r.j ? r.j + ", " : "") + esc(r.d) + '</span><span class="s">' + snippet(r, res.terms) + "</span></span></a></li>";
        }).join("");
        cur = -1;
      });
    }
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
    box.querySelectorAll(".sr-tags button").forEach(function (b) {
      b.addEventListener("click", function () { input.value = b.textContent; render(); input.focus(); });
    });
    return { input: input, render: render };
  }
  var inline = document.querySelector(".sr-box[data-inline]");
  if (inline) { var w = wire(inline, "fr"); load("fr"); setTimeout(function () { w.input.focus(); }, 100); }
  var ov = null, ovw = null, lastFocus = null;
  function openSearch() {
    if (inline) { inline.querySelector("input").focus(); return; }
    if (!ov) {
      ov = document.createElement("div");
      ov.className = "sr-ov";
      ov.setAttribute("role", "dialog");
      ov.setAttribute("aria-modal", "true");
      ov.setAttribute("aria-label", "Rechercher un récit");
      ov.innerHTML = '<div class="sr-box"><label class="sr-field"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input type="search" placeholder="Un lieu, un mot, un souvenir…" aria-label="Rechercher un récit" autocomplete="off"></label>' +
        '<div class="sr-tags"><button type="button">baleines</button><button type="button">crevaison</button><button type="button">aire de jeux</button><button type="button">tunnel</button></div><ol class="sr-results" aria-live="polite"></ol></div>';
      document.body.appendChild(ov);
      ovw = wire(ov, "fr");
      ov.addEventListener("click", function (e) { if (e.target === ov) closeSearch(); });
    }
    lastFocus = document.activeElement;
    load("fr");
    ov.classList.add("on");
    ovw.input.focus();
    ovw.input.select();
  }
  function closeSearch() { if (ov) { ov.classList.remove("on"); if (lastFocus) lastFocus.focus(); } }
  document.addEventListener("keydown", function (e) {
    var t = e.target.tagName;
    if (e.key === "/" && t !== "INPUT" && t !== "TEXTAREA") { e.preventDefault(); openSearch(); }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openSearch(); }
    if (e.key === "Escape" && ov && ov.classList.contains("on")) closeSearch();
  });

  // ---------- Visionneuse : glisser au doigt, double-tap pour zoomer ----------
  var pics = Array.prototype.slice.call(document.querySelectorAll("img[data-lb]")).filter(function (im) { return !im.closest(".lr-hero, .lr-open, .lx-card"); });
  if (!pics.length) return;
  var vw = document.createElement("div");
  vw.className = "vw";
  vw.setAttribute("role", "dialog");
  vw.setAttribute("aria-modal", "true");
  vw.setAttribute("aria-label", "Photos du récit");
  vw.innerHTML = '<div class="vw-top"><span class="vw-count"></span><button type="button" class="vw-close" aria-label="Fermer">×</button></div>' +
    '<div class="vw-stage"><div class="vw-track"></div><button type="button" class="vw-nav vw-prev" aria-label="Photo précédente">‹</button><button type="button" class="vw-nav vw-next" aria-label="Photo suivante">›</button></div>' +
    '<p class="vw-cap"></p><div class="vw-thumbs"></div>';
  document.body.appendChild(vw);
  var track = vw.querySelector(".vw-track"), thumbs = vw.querySelector(".vw-thumbs"), count = vw.querySelector(".vw-count"), cap = vw.querySelector(".vw-cap");
  pics.forEach(function (im, i) {
    var s = document.createElement("div");
    s.className = "vw-slide";
    s.innerHTML = '<img alt="" draggable="false">';
    track.appendChild(s);
    var t = document.createElement("img");
    t.src = im.currentSrc || im.src;
    t.alt = "";
    t.loading = "lazy";
    t.addEventListener("click", function () { go(i); });
    thumbs.appendChild(t);
    im.addEventListener("click", function () { open(i, im); });
  });
  var slides = track.children, at = 0, opened = false;
  function fill(i) {
    if (i < 0 || i >= pics.length) return;
    var img = slides[i].querySelector("img");
    if (!img.getAttribute("src")) img.src = pics[i].dataset.full || pics[i].currentSrc || pics[i].src;
  }
  function go(i, instant) {
    at = Math.max(0, Math.min(pics.length - 1, i));
    fill(at); fill(at - 1); fill(at + 1);
    track.style.transition = instant || reduce ? "none" : "transform .35s cubic-bezier(.2,.8,.2,1)";
    track.style.transform = "translateX(" + (-at * 100) + "%)";
    count.textContent = (at + 1) + " / " + pics.length;
    cap.textContent = pics[at].dataset.caption || "";
    Array.prototype.forEach.call(thumbs.children, function (t, k) { t.classList.toggle("on", k === at); });
    if (thumbs.children[at]) thumbs.children[at].scrollIntoView({ block: "nearest", inline: "center" });
    Array.prototype.forEach.call(slides, function (s) { s.querySelector("img").classList.remove("zoom"); });
  }
  function open(i, from) {
    var show = function () { vw.classList.add("on"); opened = true; go(i, true); document.body.style.overflow = "hidden"; vw.querySelector(".vw-close").focus(); };
    if (document.startViewTransition && !reduce && from) {
      from.style.viewTransitionName = "vw-photo";
      var t = document.startViewTransition(function () {
        from.style.viewTransitionName = "";
        show();
        slides[i].querySelector("img").style.viewTransitionName = "vw-photo";
      });
      t.finished.then(function () { slides[i].querySelector("img").style.viewTransitionName = ""; });
    } else show();
  }
  function close() { vw.classList.remove("on"); opened = false; document.body.style.overflow = ""; if (pics[at]) pics[at].focus && pics[at].scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" }); }
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
    if (now - lastTap < 300) { var im = slides[at].querySelector("img"); im.classList.toggle("zoom"); lastTap = 0; return; }
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
