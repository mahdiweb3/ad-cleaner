# Page Cleaner — Ad Blocker Extension

A Chromium extension that blocks ads **everywhere** (all sites, not just YouTube) and is **designed not to be detected as an ad blocker**.

- **English:** [README.md](README.md)
- **فارسی:** [README.fa.md](README.fa.md)

## Install

1. Download the latest release zip and extract it somewhere permanent.
2. Open `chrome://extensions`, enable **Developer mode**.
3. Click **Load unpacked** and select the extracted folder.
4. Refresh YouTube.

## What's inside

| File | Purpose |
|---|---|
| `ext/manifest.json` | MV3 manifest: `declarative_net_request` ruleset + content scripts on `<all_urls>` |
| `ext/rules.json` | ~48,000 ad hostnames converted from EasyList into 194 DNR redirect rules |
| `ext/filters.css` | ~13,000 cosmetic selectors (hide ad boxes) |
| `ext/main.js` | Strips `adPlacements` / `adSlots` / `playerAds` from the YouTube player response |
| `build_rules.py` | Rebuilds `rules.json` + `filters.css` from EasyList sources |
| `test_v2.py` | Real Chrome (Playwright) end-to-end test — 7 checks |

## Why it isn't detected

Normal blockers **block** filtered requests, so ad-detection scripts see `onerror` on their bait `<img>`/`<script>` and flag you.

This extension **redirects** filtered requests to a tiny local stub instead. The bait fires `onload` exactly like a normal page, so detection passes. It also never hides the classic detector bait selectors (`.ad-banner`, `.adsbygoogle`, `.ad`, …).

## YouTube note

YouTube ad hostnames (`youtube.com`, `googlevideo.com`, `ytimg.com`, …) are deliberately **not** network-blocked — blocking them breaks playback. YouTube ads are removed by cleaning the player payload in `ext/main.js`. If YouTube renames its payload keys, update `main.js`.

## Rebuild / test

```bash
python3 build_rules.py   # EasyList -> ext/rules.json + ext/filters.css
python3 test_v2.py       # 7-check E2E run in Chrome
```

## Releases

- **v1.0.0** — first version (YouTube + general ad hosts, 142 rules)
- **v2.0.0** — redirect-based anti-detection, EasyList host expansion (48k hosts), cosmetic CSS, YouTube payload cleaning
