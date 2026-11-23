// ponytail: MAIN world, document_start. Deletes ad payload keys in place so the
// player never sees them (no ad request is made, so nothing to detect).
// v2.1.2: adds an XMLHttpRequest.response hook. This is the real fix for "ads when
// switching videos": first page load ships the payload inline in HTML (setter path),
// but a SPA video switch is fetched with XHR + responseType='json', where the
// browser parses the JSON itself -- JSON.parse and Response.prototype.json never
// run, so v2.1.0 cleaned nothing and the ad played. F5 reloaded the inline path,
// which is why a refresh appeared to fix it.
// v2.1.1: dirty() also looked one level into playerResponse.
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
  // Envelope used by some player fetches; first-load payloads are the player
  // response itself, which is why both shapes must be handled.
  const inner = (o) => {
    const p = o.playerResponse || (o.response && o.response.playerResponse);
    return p && typeof p === 'object' ? p : null;
  };
  const dirty = (o) => {
    for (const k of KEYS) if (k in o) return true;
    const p = inner(o);
    return p ? KEYS.some((k) => k in p) : false;
  };
  const clean = (o) => {
    try {
      for (const k of KEYS) delete o[k];
      const p = inner(o);
      if (p) clean(p);
    } catch (e) {}
    return o;
  };
  // ponytail: two levels only (root -> playerResponse -> playerResponse). Deeper
  // recursion would walk every parsed object and stall big responses.
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

  // The one v2.1.0 missed: XHR with responseType='json' is parsed by the browser,
  // so the object reaches the app without passing through JSON.parse. Patch the
  // getter and clean on read; same object is returned, nothing is copied.
  try {
    const d = Object.getOwnPropertyDescriptor(XMLHttpRequest.prototype, 'response');
    if (d && d.get) {
      Object.defineProperty(XMLHttpRequest.prototype, 'response', {
        configurable: true,
        enumerable: d.enumerable,
        get() {
          const v = d.get.call(this);
          // ponytail: only json responses -- text/blob/arraybuffer must stay untouched.
          return this.responseType === 'json' ? maybe(v) : v;
        },
      });
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
