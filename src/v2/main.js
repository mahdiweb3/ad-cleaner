// ponytail: MAIN world, document_start. Deletes ad payload keys in place so the
// player never sees them (no ad request is made, so nothing to detect).
// v2.1.0: only JSON.parse + Response.prototype.json are patched. v2.0.0 replaced
// window.fetch with a NEW Response object, which dropped response.url/type and
// stalled YouTube's SPA router -> switching videos hung until a manual refresh.
(() => {
  if (window.__pcClean) return;
  window.__pcClean = 1;
  // ponytail: JSON.parse is patched globally (needed -- player payloads arrive via
  // several readers), but only youtube hosts carry these keys. Skip the patch
  // entirely elsewhere so no site pays for the 5 `in` checks per parse.
  if (!/(^|\.)(youtube\.com|youtube-nocookie\.com)$/.test(location.hostname)) return;

  const KEYS = ['adPlacements', 'adSlots', 'playerAds', 'adBreakParams', 'adBreakHeartbeatParams'];
  const dirty = (o) => {
    for (const k of KEYS) if (k in o) return true;
    return false;
  };
  const clean = (o) => {
    try {
      for (const k of KEYS) delete o[k];
      if (o.playerResponse) clean(o.playerResponse);
      if (o.response && o.response.playerResponse) clean(o.response.playerResponse);
    } catch (e) {}
    return o;
  };
  // ponytail: top-level check only; payloads always carry the keys at the root of
  // playerResponse. Recursing into every parsed object would stall big responses.
  const maybe = (r) => (r && typeof r === 'object' && dirty(r) ? clean(r) : r);

  try {
    const parse = JSON.parse;
    JSON.parse = function () {
      return maybe(parse.apply(this, arguments));
    };
  } catch (e) {}

  // Covers XHR/fetch paths that hand a Response straight to the app (YouTube uses
  // this for /youtubei/v1/player). No new Response is constructed, so the original
  // object keeps its url/type/stream and SPA navigation keeps working.
  try {
    const rj = Response.prototype.json;
    if (rj) {
      Response.prototype.json = function () {
        return rj.apply(this, arguments).then(maybe);
      };
    }
  } catch (e) {}

  // First page load: the player response arrives as an inline global.
  try {
    let v;
    Object.defineProperty(window, 'ytInitialPlayerResponse', {
      configurable: true,
      get: () => v,
      set: (x) => { v = x && typeof x === 'object' ? clean(x) : x; },
    });
  } catch (e) {}

  // /youtubei/v1/player responses can also arrive as raw text parsed by the app's
  // own reader; patch it the same way when present.
  try {
    if (window.ytcfg && typeof window.ytcfg.set === 'function') {
      const set = window.ytcfg.set;
      window.ytcfg.set = function () {
        const r = set.apply(this, arguments);
        try {
          if (window.ytInitialPlayerResponse) clean(window.ytInitialPlayerResponse);
        } catch (e) {}
        return r;
      };
    }
  } catch (e) {}
})();
