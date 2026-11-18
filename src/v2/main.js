// ponytail: MAIN world, document_start. Strips ad payloads before the player reads
// them, so no ad request is ever made -> nothing for the site to detect as blocked.
// If YouTube renames these keys, ads come back: check adPlacements/adSlots/playerAds.
(() => {
  const KEYS = ['adPlacements', 'adSlots', 'playerAds', 'adBreakParams', 'adBreakHeartbeatParams'];
  const dirty = (o) => KEYS.some((k) => k in o);
  const clean = (o) => {
    try {
      for (const k of KEYS) delete o[k];
      if (o.playerResponse) clean(o.playerResponse);
      if (o.response && o.response.playerResponse) clean(o.response.playerResponse);
    } catch (e) {}
    return o;
  };

  let ipr;
  try {
    Object.defineProperty(window, 'ytInitialPlayerResponse', {
      configurable: true,
      get: () => ipr,
      set: (v) => { ipr = v && typeof v === 'object' ? clean(v) : v; },
    });
  } catch (e) {}

  try {
    const parse = JSON.parse;
    JSON.parse = function (...a) {
      const r = parse.apply(this, a);
      return r && typeof r === 'object' && dirty(r) ? clean(r) : r;
    };
  } catch (e) {}

  try {
    const of = window.fetch;
    if (of) {
      window.fetch = async function (...a) {
        const res = await of.apply(this, a);
        try {
          const u = String((a[0] && a[0].url) || a[0]);
          const ct = res.headers.get('content-type') || '';
          if (u.includes('/youtubei/') && ct.includes('json')) {
            const j = await res.clone().json();
            if (j && typeof j === 'object' && (dirty(j) || j.playerResponse)) {
              return new Response(JSON.stringify(clean(j)), {
                status: res.status,
                statusText: res.statusText,
                headers: res.headers,
              });
            }
          }
        } catch (e) {}
        return res;
      };
    }
  } catch (e) {}

  try {
    const open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (...a) {
      this.addEventListener('load', () => {
        try {
          if (!String(a[1] || '').includes('/youtubei/')) return;
          const j = JSON.parse(this.responseText);
          if (j && typeof j === 'object' && (dirty(j) || j.playerResponse)) clean(j);
        } catch (e) {}
      });
      return open.apply(this, a);
    };
  } catch (e) {}
})();
