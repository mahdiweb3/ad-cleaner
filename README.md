# Page Cleaner — Ad Blocker Extension

A Chromium extension that blocks ads **everywhere** (all sites, not just YouTube) and is **designed not to be detected as an ad blocker**.

- **English:** [README.md](README.md)
- **فارسی:** [README.fa.md](README.fa.md)

## Install

1. Download a release zip and extract it somewhere permanent:
   - [v2.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/download/v2.0.0/ad-cleaner-v2.0.0.zip) — all sites (recommended)
   - [v1.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/download/v1.0.0/ad-cleaner-v1.0.0.zip) — YouTube only
2. Open `chrome://extensions`, enable **Developer mode**.
3. Click **Load unpacked** and select the extracted folder.
4. Browse any site.

## What's inside

| File | Purpose |
|---|---|
| `src/v2/manifest.json` | MV3 manifest: `declarative_net_request` ruleset + content scripts on `<all_urls>` |
| `src/v2/rules.json` | 48,097 ad hostnames converted from EasyList into 194 DNR redirect rules |
| `src/v2/filters.css` | 13,076 cosmetic selectors (hide ad boxes) |
| `src/v2/main.js` | Strips `adPlacements` / `adSlots` / `playerAds` from the YouTube player response |
| `src/v2/stub.js`, `src/v2/stub.gif` | Tiny local stand-ins that filtered requests redirect to |
| `src/v2/build_rules.py` | Rebuilds `rules.json` + `filters.css` from EasyList sources |
| `src/v2/test_v2.py` | Real Chrome (Playwright) end-to-end test — 7 checks |
| `src/v1/` | v1.0.0 source (YouTube-only, 142 rules) |

## Why it isn't detected

Normal blockers **block** filtered requests, so ad-detection scripts see `onerror` on their bait `<img>`/`<script>` and flag you.

This extension **redirects** filtered requests to a tiny local stub instead. The bait fires `onload` exactly like a normal page, so detection passes. It also never hides the classic detector bait selectors (`.ad-banner`, `.adsbygoogle`, `.ad`, …).

## YouTube note

YouTube ad hostnames (`youtube.com`, `googlevideo.com`, `ytimg.com`, …) are deliberately **not** network-blocked — blocking them breaks playback. YouTube ads are removed by cleaning the player payload in `src/v2/main.js`. If YouTube renames its payload keys, update `main.js`.

## Rebuild / test

```bash
cd src/v2
python3 build_rules.py   # EasyList -> rules.json + filters.css
python3 test_v2.py       # 7-check E2E run in Chrome
```

## Releases

- **[v2.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v2.0.0)** — redirect-based anti-detection, EasyList host expansion (48,097 hosts), cosmetic CSS, YouTube payload cleaning
- **[v1.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v1.0.0)** — first version (YouTube + general ad hosts, 142 rules)

Both zips are also committed at the repo root (`ad-cleaner-v1.0.0.zip`, `ad-cleaner-v2.0.0.zip`).

## License

MIT
