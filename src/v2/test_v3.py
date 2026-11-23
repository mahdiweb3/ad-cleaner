"""Real-Chrome check for Page Cleaner v2.1.0.

Regression target (v2.0.0): the EasyList host rule for `google.com` turned a path
rule into a host-wide DNR redirect, so `accounts.google.com/ServiceLogin` and
`www.google.com/js/th/*.js` were answered with our stub. YouTube's sign-in frame
then never resolved and a video switch left <video> paused at t=0 with readyState 4
until a manual refresh.

Run: xvfb-run -a python3 test_v3.py
"""
import json, os, sys, tempfile

from playwright.sync_api import sync_playwright

EXT = os.environ.get("PC_EXT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "ext")
CHROME = "/opt/chromium/chrome-linux64/chrome"
AD_URL = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"
PLAYBACK = ("youtube.com", "googlevideo.com", "ytimg.com", "gstatic.com",
            "ggpht.com", "googleapis.com")
fails, passed = [], []


def check(name, ok, detail=""):
    (passed if ok else fails).append(name)
    print(("ok   " if ok else "FAIL ") + name + (f" :: {detail}" if detail else ""))


def main():
    css = open(os.path.join(EXT, "filters.css")).read()
    rules = json.load(open(os.path.join(EXT, "rules.json")))

    # 1. ruleset -------------------------------------------------------------
    check("rules.json loads", isinstance(rules, list), f"{len(rules)} rules")
    ids = [r["id"] for r in rules]
    check("rule ids unique", len(set(ids)) == len(ids))
    check("no main_frame redirect",
          not any("main_frame" in r["condition"].get("resourceTypes", []) for r in rules))
    blocked = [d for r in rules for d in r["condition"].get("requestDomains", [])
               if any(k in d for k in PLAYBACK)]
    check("playback hosts never host-blocked", not blocked, str(blocked[:3]))
    # the v2.0.0 regression: bare google.com / cse.google.com in requestDomains
    infra = [d for r in rules for d in r["condition"].get("requestDomains", [])
             if d in ("google.com", "www.google.com", "cse.google.com", "accounts.google.com")]
    check("google.com not host-blocked (auth frame stays alive)", not infra, str(infra[:3]))
    toks = {t.strip() for part in css.split(",") for t in [part.split("{")[0]]}
    baited = [s for s in (".ad", ".ads", "#ad", ".adsbygoogle", ".ad-banner",
                          ".adBanner", ".adsbox", ".textads", ".advert") if s in toks]
    check("classic bait selectors not hidden", not baited, str(baited[:3]))

    with sync_playwright() as p:
        def launch(ext):
            args = ["--no-first-run", "--no-default-browser-check", "--lang=en-US"]
            if ext:
                args = [f"--disable-extensions-except={ext}", f"--load-extension={ext}"] + args
            ctx = p.chromium.launch_persistent_context(
                tempfile.mkdtemp(prefix="pc-"), executable_path=CHROME, headless=False,
                args=args, viewport={"width": 1400, "height": 900})
            ctx.add_cookies([
                {"name": "CONSENT", "value": "YES+cb", "domain": ".youtube.com", "path": "/"},
                {"name": "SOCS", "value": "CAI", "domain": ".youtube.com", "path": "/"}])
            return ctx

        # 2. ad host redirected, bait fires onload ----------------------------
        ctx = launch(EXT)
        page = ctx.new_page()
        seen = []
        page.on("response", lambda r: seen.append(r.url)
                if r.request.redirected_from and "googlesyndication" in r.request.redirected_from.url
                else None)
        page.goto("https://example.com/", wait_until="domcontentloaded")
        bait = page.evaluate("""(u) => new Promise((res) => {
            const s = document.createElement('script');
            s.src = u; s.onload = () => res('load'); s.onerror = () => res('error');
            document.head.appendChild(s); setTimeout(() => res('timeout'), 8000);
        })""", AD_URL)
        check("ad host redirects to stub", any("chrome-extension://" in u for u in seen),
              str(seen)[:90])
        check("ad bait fires onload, not onerror", bait == "load", bait)
        page.close()

        # 3. YouTube: first video plays -------------------------------------
        yt = ctx.new_page()
        yt.goto("https://www.youtube.com/watch?v=aqz-KE-bpKQ",
                wait_until="domcontentloaded", timeout=60000)
        yt.wait_for_timeout(8000)
        check("window.fetch left native", yt.evaluate("window.fetch.toString().includes('[native code]')"))
        check("Response.prototype.json patched",
              yt.evaluate("!Response.prototype.json.toString().includes('[native code]')"))
        # v2.1.2 regression: a SPA video switch fetches /youtubei/v1/player with
        # XHR + responseType='json'. The browser parses that JSON itself, so
        # JSON.parse / Response.prototype.json never run and v2.1.0 cleaned nothing.
        check("XHR response getter hooked",
              yt.evaluate("!String(Object.getOwnPropertyDescriptor("
                          "XMLHttpRequest.prototype,'response').get)"
                          ".includes('[native code]')"))
        xhr = yt.evaluate("""async () => {
          const KEYS=['adPlacements','adSlots','playerAds','adBreakParams','adBreakHeartbeatParams'];
          const k = window.ytcfg.get('INNERTUBE_API_KEY');
          const ctx = window.ytcfg.get('INNERTUBE_CONTEXT');
          const get = (rt) => new Promise((res) => {
            const x = new XMLHttpRequest();
            x.open('POST','/youtubei/v1/player?key='+k+'&prettyPrint=false');
            x.setRequestHeader('content-type','application/json');
            x.setRequestHeader('x-youtube-client-name','1');
            x.setRequestHeader('x-youtube-client-version', window.ytcfg.get('INNERTUBE_CLIENT_VERSION'));
            if (rt) x.responseType = rt;
            x.onload = () => res({rt, status: x.status, body: x.response});
            x.onerror = () => res({rt, error: 'xhr failed'});
            x.send(JSON.stringify({videoId:'xOXolSQcEb4', context: ctx}));
          });
          const j = await get('json');
          const b = j.body || {};
          const adKeys = Object.keys(b).filter(k => KEYS.includes(k))
            .concat(Object.keys(b.playerResponse || {}).filter(k => KEYS.includes(k)));
          const t = await get('text');
          return {json: {status: j.status, adKeys},
                  textIsString: typeof t.body === 'string',
                  textHasKeys: typeof t.body === 'string' && KEYS.some(k => t.body.includes('"'+k+'"'))};
        }""")
        check("XHR json player payload clean", xhr["json"]["status"] == 200 and not xhr["json"]["adKeys"],
              str(xhr["json"]))
        check("XHR text responses untouched", xhr["textIsString"], str(xhr["textIsString"]))
        st = yt.evaluate("""() => { const v = document.querySelector('video');
            return v && {rs: v.readyState, paused: v.paused, src: !!v.currentSrc,
                         dur: Math.round(v.duration || 0)}; }""")
        check("first video has media", bool(st and st["src"]), str(st))
        plc = yt.evaluate("""() => { const r = window.ytInitialPlayerResponse;
            if (!r) return 'none';
            return ['adPlacements','adSlots','playerAds'].some(k => k in r) ? 'dirty' : 'clean'; }""")
        check("player payload clean", plc in ("clean", "none"), str(plc))

        # 4. soft switch: new video must actually play, no refresh -----------
        t0 = yt.evaluate("performance.timeOrigin")
        href0 = yt.url
        yt.locator('ytd-watch-next-secondary-results-renderer a[href*="/watch?v="]').first.click(timeout=25000)
        yt.wait_for_url(lambda u: "/watch?v=" in u and u != href0, timeout=30000)
        played = None
        for _ in range(30):
            yt.wait_for_timeout(500)
            played = yt.evaluate("""() => { const v = document.querySelector('video');
                return v && {t: v.currentTime, rs: v.readyState, paused: v.paused,
                             src: !!v.currentSrc}; }""")
            if played and played["src"] and played["t"] > 1 and not played["paused"]:
                break
        check("soft switch keeps document alive",
              yt.evaluate("performance.timeOrigin") == t0, f"{href0} -> {yt.url}")
        check("new video actually plays after switch",
              bool(played and played["src"] and played["t"] > 1 and not played["paused"]),
              str(played))
        ctx.close()

    print(f"\n{len(passed)} passed, {len(fails)} failed")
    if fails:
        print("failed:", fails)
        sys.exit(1)


if __name__ == "__main__":
    main()
