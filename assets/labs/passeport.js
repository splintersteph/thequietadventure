/* Prototype passeport : le carnet s'ouvre, les visas se posent un par un */
(function () {
  "use strict";
  var book = document.querySelector(".ps-book");
  if (!book) return;
  var cover = book.querySelector(".ps-cover");
  function open() { book.dataset.open = "true"; cover.setAttribute("aria-expanded", "true"); }
  cover.addEventListener("click", open);
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.intersectionRatio > 0.6) { setTimeout(open, 900); io.disconnect(); } });
    }, { threshold: [0.6] });
    io.observe(cover);
  }
})();
