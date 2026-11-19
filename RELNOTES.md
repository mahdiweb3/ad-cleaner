## v2.1.0 — YouTube video switching fixed

### The bug
Switching to another YouTube video left the player stuck (paused at `t=0`, black frame) until a manual page refresh.

Two causes, both fixed:

1. **`main.js` replaced `window.fetch`.** The wrapper built a new `Response` from the body, which drops `response.url` and `response.type`. YouTube's SPA router reads `url` off its own navigation responses, so the route change never completed. `main.js` now patches only `JSON.parse` and `Response.prototype.json`, and is injected on `youtube.com` only (was `<all_urls>`).
2. **`google.com` was host-blocked.** The EasyList `^` anchor was not stripped in the converter, so `||google.com/path^`-style rules became host-wide `requestDomains` entries. `accounts.google.com/ServiceLogin` and `www.google.com/js/th/*.js` returned the stub, and the sign-in iframe never resolved. Path rules now emit `urlFilter`; host rules stay `requestDomains`.

### Also
- Protected playback hosts (`googlevideo.com`, `ytimg.com`, `gstatic.com`, `googleapis.com`, `ggpht.com`) are never host-blocked.
- Classic detector bait selectors (`.ad`, `.ads`, `.adsbygoogle`, `.ad-banner`, …) are never hidden — detection still passes.
- `build_rules.py` self-checks its own output and fails loudly instead of shipping a bad ruleset.

### Verified
`test_v3.py` — 14 checks in real Chrome (`xvfb-run -a python3 test_v3.py`):

```
ok   google.com not host-blocked (auth frame stays alive)
ok   classic bait selectors not hidden
ok   ad host redirects to stub
ok   ad bait fires onload, not onerror
ok   window.fetch left native
ok   Response.prototype.json patched
ok   first video has media
ok   player payload clean
ok   soft switch keeps document alive
ok   new video actually plays after switch
14 passed, 0 failed
```

The same suite against the v2.0.0 build reproduces the failure (`new video actually plays after switch :: t=0, paused=True`), so this is a measured fix, not a guess.

`smoke_hosts.py` — 8/10 ad hosts redirected, 4/4 legit scripts (reCAPTCHA, Google Sign-In, jsDelivr, jQuery) load untouched. The 2 survivors (`criteo.net`, `branch.io`) are path-only rules in EasyList (`||criteo.net/banners/`), so their root JS is legitimately not blocked.

### Install
Download `ad-cleaner-v2.1.0.zip` below, extract, `chrome://extensions` → Developer mode → Load unpacked.
