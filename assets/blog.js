(function () {
  var bar = document.querySelector(".reading-progress");
  var article = document.querySelector(".article-body");
  if (bar && article) {
    var queued = false;
    var update = function () {
      queued = false;
      var start = article.offsetTop;
      var distance = Math.max(1, article.offsetHeight - window.innerHeight);
      var value = Math.max(0, Math.min(1, (window.scrollY - start) / distance));
      bar.style.width = (value * 100).toFixed(2) + "%";
    };
    window.addEventListener("scroll", function () {
      if (!queued) { queued = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  }
  var mobileCta = document.querySelector(".mobile-cta");
  var close = document.querySelector(".mobile-cta-close");
  if (mobileCta && close) close.addEventListener("click", function () { mobileCta.hidden = true; });
})();
