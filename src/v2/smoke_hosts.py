"""Broad smoke test: many ad hosts must redirect to the stub; a normal site must
stay intact. Guards against over-broad rules (the v2.0.0 google.com regression).
"""
import tempfile
from playwright.sync_api import sync_playwright

EXT = "/root/adblocker-v2/ext"
CHROME = "/opt/chromium/chrome-linux64/chrome"
AD_HOSTS = [
    "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js",
    "https://googleads.g.doubleclick.net/pagead/id",
    "https://static.doubleclick.net/instream/ad_status.js",
    "https://tpc.googlesyndication.com/sodar/56-y-0RG.js",
    "https://ads.pubmatic.com/AdServer/js/showad.js",
    "https://cdn.taboola.com/libtrc/loader.js",
    "https://s.adroll.com/j/roundtrip.js",
    "https://static.criteo.net/js/ld/publishertag.js",
    "https://c.amazon-adsystem.com/aax2/apstag.js",
    "https://cdn.branch.io/branch-latest.min.js",
]
MUST_WORK = [
    "https://www.google.com/recaptcha/api.js",
    "https://accounts.google.com/gsi/client",
    "https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js",
    "https://code.jquery.com/jquery-3.7.1.min.js",
]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        tempfile.mkdtemp(), executable_path=CHROME, headless=False,
        args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}",
              "--no-first-run", "--no-default-browser-check", "--lang=en-US"],
        viewport={"width": 1280, "height": 800})
    pg = ctx.new_page()
    redir = {}
    pg.on("response", lambda r: redir.setdefault(
        (r.request.redirected_from.url if r.request.redirected_from else r.url),
        r.url) if r.url.startswith("chrome-extension://") else None)
    pg.goto("https://example.com/", wait_until="domcontentloaded")

    def probe(url):
        return pg.evaluate("""(u) => new Promise((res) => {
            const s = document.createElement('script');
            const t = setTimeout(() => res('timeout'), 9000);
            s.onload = () => { clearTimeout(t); res('load'); };
            s.onerror = () => { clearTimeout(t); res('error'); };
            s.src = u; document.head.appendChild(s);
        })""", url)

    blocked = worked = 0
    for u in AD_HOSTS:
        r = probe(u)
        hit = any(u.split("?")[0].startswith(k.split("?")[0]) for k in redir)
        blocked += hit
        print(("BLOCK " if hit else "LEAK  ") + u[:72] + f"  ({r})")
    for u in MUST_WORK:
        r = probe(u)
        ok = r == "load" and not any(u[:40] in k for k in redir)
        worked += ok
        print(("KEEP  " if ok else "BROKE ") + u[:72] + f"  ({r})")
    # ponytail: criteo.net and branch.io are path-only rules in EasyList
    # (||criteo.net/banners/), so their root JS legitimately survives.
    # Not a converter bug -> do not widen to host-wide blocking.
    print(f"\nad hosts redirected {blocked}/{len(AD_HOSTS)}, legit scripts kept {worked}/{len(MUST_WORK)}")
    ctx.close()
