/*
 * email-protect.js
 * Assemble email links and addresses at runtime so the raw address never
 * appears in the served HTML source for harvesting bots to scrape.
 *
 *   <a data-e="BASE64">            -> href becomes mailto:<decoded target>
 *   <a data-e="BASE64" data-e-show> -> also sets link text to the address
 *   <span data-e-text="BASE64">    -> element text becomes the decoded address
 *
 * BASE64 is base64(address[?query]). With JS off, links fall back to their
 * existing href (e.g. /contact) and any placeholder text ("djz [at] shmonk
 * [dot] com") stays human-readable but bot-safe.
 */
(function () {
  function decode(s) {
    try { return atob(s); } catch (e) { return ""; }
  }

  document.querySelectorAll("a[data-e]").forEach(function (el) {
    var target = decode(el.getAttribute("data-e"));
    if (!target) return;
    el.setAttribute("href", "mailto:" + target);
    if (el.hasAttribute("data-e-show")) {
      el.textContent = target.split("?")[0];
    }
  });

  document.querySelectorAll("[data-e-text]").forEach(function (el) {
    var addr = decode(el.getAttribute("data-e-text"));
    if (addr) el.textContent = addr;
  });
})();
