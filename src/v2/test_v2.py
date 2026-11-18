# ponytail: one runnable check. Proves (1) ruleset loads, (2) filtered requests look
# like empty 200s not ERR_BLOCKED_BY_CLIENT (what anti-adblock scripts fingerprint),
# (3) YouTube ad payload stripped + video still plays, (4) cosmetic CSS applied.
import json, sys
from playwright.sync_api import sync_playwright

EXT = "/root/adblocker-v2/ext"
CHROME = "/opt/chromium/chrome-linux64/chrome"


def main():
    out = {"checks": {}}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir="/tmp/pw-v2b",
            executable_path=CHROME,
            headless=True,
            args=[
                f"--disable-extensions-except={EXT}",
                f"--load-extension={EXT}",
                "--no-first-run", "--mute-audio", "--no-sandbox",
                "--disable-dev-shm-usage", "--autoplay-policy=no-user-gesture-required",
            ],
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        page.set_default_timeout(30000)

        # A: filtered request resolves instead of throwing
        page.goto("https://example.com/", wait_until="domcontentloaded", timeout=60000)
        # Image bait is the real detection vector: adblockers make it fire onerror.
        r = page.evaluate(
            """async () => {
              const t = (u) => new Promise((res) => {
                const i = new Image();
                const done = (e) => res({onload: e === 'load', onerror: e === 'error'});
                i.onload = () => done('load');
                i.onerror = () => done('error');
                i.src = u;
                setTimeout(() => done('timeout'), 8000);
              });
              return {
                control: await t('https://www.youtube.com/favicon.ico?x=' + Math.random()),
                ad: await t('https://securepubads.g.doubleclick.net/pagead/1.gif?x=' + Math.random()),
                ad2: await t('https://static.criteo.net/empty.gif?x=' + Math.random()),
              };
            }"""
        )
        out["net"] = r
        # redirect -> resolves (no throw). This is the "undetectable" property.
        out["checks"]["filtered_img_fires_onload"] = r["ad"]["onload"] and r["ad2"]["onload"]
        out["checks"]["control_img_fires_onload"] = r["control"]["onload"]

        # B: YouTube
        page.goto("https://www.youtube.com/watch?v=aqz-KE-bpKQ",
                  wait_until="domcontentloaded", timeout=60000)
        # ponytail: player attach is racy on a cold profile; poll, don't sleep-and-hope.
        for _ in range(20):
            if page.evaluate("() => !!document.querySelector('#movie_player video')"):
                break
            page.wait_for_timeout(1000)
        yt = page.evaluate(
            """() => {
              const pr = window.ytInitialPlayerResponse || {};
              const v = document.querySelector('#movie_player video');
              return {
                hasPR: !!window.ytInitialPlayerResponse,
                adPlacements: 'adPlacements' in pr,
                adSlots: 'adSlots' in pr,
                playerAds: 'playerAds' in pr,
                adShowing: !!document.querySelector('.ad-showing'),
                t: v ? v.currentTime : null,
                d: v ? v.duration : null,
              };
            }"""
        )
        page.evaluate("() => { const v=document.querySelector('#movie_player video'); if(v){v.muted=true;v.play().catch(()=>{});} }")
        page.wait_for_timeout(3500)
        prog = page.evaluate("() => { const v=document.querySelector('#movie_player video'); return v?v.currentTime:-1; }")
        yt["progress"] = prog
        out["yt"] = yt
        out["checks"]["yt_ad_keys_gone"] = not (yt["adPlacements"] or yt["adSlots"] or yt["playerAds"])
        out["checks"]["yt_no_ad_wall"] = not yt["adShowing"]
        out["checks"]["yt_video_plays"] = (prog or 0) > 1.5

        # C: cosmetic CSS
        page.goto("https://example.com/", wait_until="domcontentloaded", timeout=30000)
        cen = page.evaluate(
            """() => {
              const d = document.createElement('div');
              d.className = 'zone-advertisement';  // present in EasyList cosmetic list
              document.body.appendChild(d);
              const bait = document.createElement('div');
              bait.className = 'ad-banner';  // must stay visible (detector bait)
              document.body.appendChild(bait);
              return {ad: getComputedStyle(d).display,
                      bait: getComputedStyle(bait).display};
            }"""
        )
        out["css"] = cen
        out["checks"]["cosmetic_css_applied"] = cen["ad"] == "none"
        out["checks"]["bait_not_hidden"] = cen["bait"] != "none"

        ctx.close()

    ok = all(v is True for v in out["checks"].values())
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        print("RESULT: FAIL (exception)")
        sys.exit(1)
