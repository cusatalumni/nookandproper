/* Rewrite Amazon links to the visitor's local Amazon store and affiliate tag.
   Country comes from /api/geo (Vercel edge header). Degrades silently to the
   default US store when the endpoint is unavailable — e.g. local preview. */
(function () {
  var REGIONS = window.NP_REGIONS || {};
  var DEFAULT = window.NP_DEFAULT_REGION || "US";

  function apply(code) {
    var r = REGIONS[code];
    if (!r) return null;
    document.querySelectorAll("a[data-amazon-path]").forEach(function (a) {
      var path = a.getAttribute("data-amazon-path");
      a.href = "https://" + r.domain + path + (path.indexOf("?") > -1 ? "&" : "?") + "tag=" + r.tag;
      a.setAttribute("data-region", code);
    });
    document.querySelectorAll("[data-region-label]").forEach(function (el) {
      el.textContent = r.label;
      el.parentElement.hidden = false;
    });
    return r;
  }

  apply(DEFAULT);
  if (!Object.keys(REGIONS).length) return;
  try {
    fetch("/api/geo", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && d.country) apply(d.country); })
      .catch(function () {});
  } catch (e) {}
})();
