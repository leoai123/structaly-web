/* =============================================================================
   訂單秘書 — 產業頁共用腳本（/trades/*/index.html）

   做三件事：
     1. 把 [data-oa-link] 的 href 換成 LINE 官方帳號連結（要換連結時改這裡一行）；
     2. 捲動後給 sticky header 一層厚度；
     3. 捲動進場動畫（只有 <html> 上有 .js-anim 時才跑）。

   .js-anim 是每頁 <head> 裡那段極短的 inline script 加上去的——放在 head 是為了在
   第一次繪製前就決定，避免內容先閃一下再被藏起來。這裡只負責「已經決定要動」之後的事。
   ============================================================================= */

(function () {
  /* 「訂單秘書」LINE 官方帳號（@659okblk）。要換短連結時改這一行就好。 */
  var ORDER_OA_URL = "https://line.me/R/ti/p/@659okblk";
  var links = document.querySelectorAll("[data-oa-link]");
  for (var i = 0; i < links.length; i++) links[i].setAttribute("href", ORDER_OA_URL);

  /* 捲動後給 sticky header 一點層次。這是狀態變化不是動畫，不受動效開關影響。 */
  var hdr = document.querySelector("header");
  if (hdr) {
    var queued = false;
    var sync = function () { queued = false; hdr.classList.toggle("is-stuck", window.scrollY > 8); };
    window.addEventListener("scroll", function () {
      if (!queued) { queued = true; window.requestAnimationFrame(sync); }
    }, { passive: true });
    sync();
  }

  if (!document.documentElement.classList.contains("js-anim")) return;

  /* ---- 保險絲 ----
     進場動畫是靠 JS 把內容從 opacity:0 打開的，萬一 IntersectionObserver 沒有動
     （瀏覽器怪癖、擴充套件擋掉、分頁在背景被凍結…），整頁內容就會看不見。
     沒收到第一次回呼就直接把所有內容顯示出來——寧可沒有動畫，也不能讓人看到空白的頁。 */
  var ioAlive = false;
  function revealAll() {
    var all = document.querySelectorAll("[data-rv]");
    for (var i = 0; i < all.length; i++) all[i].classList.add("rv-in");
  }
  function failsafe() {
    if (ioAlive) return;
    if (document.hidden) return;
    revealAll();
  }
  window.setTimeout(failsafe, 1600);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) window.setTimeout(failsafe, 1600);
  });

  var io = new IntersectionObserver(function (entries) {
    ioAlive = true;
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (!e.isIntersecting) continue;
      io.unobserve(e.target);
      if (e.target.hasAttribute("data-rv-cascade")) {
        var kids = e.target.querySelectorAll("[data-rv]");
        for (var k = 0; k < kids.length; k++) kids[k].classList.add("rv-in");
      } else {
        e.target.classList.add("rv-in");
      }
    }
  }, { rootMargin: "0px 0px -60px 0px", threshold: 0 });

  var groups = document.querySelectorAll("[data-rv-cascade]");
  for (var g = 0; g < groups.length; g++) io.observe(groups[g]);

  var items = document.querySelectorAll("[data-rv]");
  for (var n = 0; n < items.length; n++) {
    var el = items[n];
    if (el.closest && el.closest("[data-rv-cascade]")) continue;
    io.observe(el);
  }
})();
