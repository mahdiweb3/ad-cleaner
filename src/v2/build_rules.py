# ponytail: EasyList -> MV3 DNR + cosmetic CSS. Redirect (not block) so filtered
# requests return a real 200 instead of ERR_BLOCKED_BY_CLIENT -- an <img>/<script>
# bait then fires onload, so classic blocker detection fails.
# Ceiling: a detector that reads document.currentScript.src sees chrome-extension://.
import json, re, os

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, "ext")

# ponytail: classic detector bait selectors are never hidden. Real ads don't use
# these names; hiding them IS the detection test. Ceiling: a site baiting with a
# real ad selector wins -- patch per-site if it ever happens.
BAIT = {
    ".ad", ".ads", "#ad", "#ads", ".ad-banner", ".adBanner", ".ad_banne",
    ".adsbox", ".adsbygoogle", ".ad-placement", ".ad-placeholder",
    ".ad-unit", ".ad-unit-label", ".banner_ad", ".textads", ".advert",
    ".advertisement", ".ad-slot", ".ad-container",
}

hosts, cosmetics = set(), set()
HOST_RE = re.compile(r"^\|\|([a-z0-9][a-z0-9._-]*\.[a-z]{2,})", re.I)

# ponytail: blocking a host the video player itself needs (YouTube serves content
# + auth from these) breaks playback outright. EasyList legitimately contains path
# rules on some of them (e.g. ||youtube.com/pagead/), so drop the whole host.
# Add here if playback dies on another site.
NEVER = (".googlevideo.com", ".ytimg.com", ".youtube.com", ".youtube-nocookie.com",
         ".youtu.be", ".gstatic.com", ".googleapis.com", ".ggpht.com")

for name in ("easylist.txt", "easylist_adservers.txt"):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        continue
    for line in open(p, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line[0] in "![":
            continue
        if line.startswith("#"):
            m = re.search(r"##([^{}:]+)$", line)
            if m:
                for part in m.group(1).split(","):
                    sel = part.strip()
                    if sel and re.fullmatch(r"[.#][A-Za-z0-9_-]+", sel) and sel not in BAIT:
                        cosmetics.add(sel)
            continue
        m = HOST_RE.match(line)   # ||host^, ||host/path, ||host$opts -> host
        if m:
            h = m.group(1).lower()
            protected = h in [n.lstrip(".") for n in NEVER] or h.endswith(NEVER)
            if not h.startswith("-") and ".." not in h and not protected:
                hosts.add(h)

CHUNK = 500
hosts = sorted(hosts)
rules, rid = [], 1
for i in range(0, len(hosts), CHUNK):
    ch = hosts[i:i + CHUNK]
    rules.append({"id": rid, "priority": 1,
                  "action": {"type": "redirect", "redirect": {"extensionPath": "/stub.js"}},
                  "condition": {"requestDomains": ch,
                                "resourceTypes": ["script", "xmlhttprequest", "sub_frame"]}})
    rid += 1
    rules.append({"id": rid, "priority": 1,
                  "action": {"type": "redirect", "redirect": {"extensionPath": "/stub.gif"}},
                  "condition": {"requestDomains": ch,
                                "resourceTypes": ["image", "media", "ping", "other", "object"]}})
    rid += 1

os.makedirs(OUT, exist_ok=True)
json.dump(rules, open(os.path.join(OUT, "rules.json"), "w"), separators=(",", ":"))

sels = sorted(cosmetics)
css = ["".join([",".join(sels[i:i + 400]), "{display:none!important}\n"])
       for i in range(0, len(sels), 400)]
open(os.path.join(OUT, "filters.css"), "w").write("".join(css))

open(os.path.join(OUT, "stub.js"), "w").write("/* noop */\n")
open(os.path.join(OUT, "stub.gif"), "wb").write(
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")

print(f"hosts={len(hosts)} rules={len(rules)} cosmetic={len(cosmetics)}")
