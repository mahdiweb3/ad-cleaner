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

# ponytail: blocking a host the video player itself needs (YouTube serves content
# + auth from these) breaks playback outright. EasyList legitimately contains path
# rules on some of them (e.g. ||youtube.com/pagead/), so drop the whole host.
# Add here if playback dies on another site.
NEVER = (".googlevideo.com", ".ytimg.com", ".youtube.com", ".youtube-nocookie.com",
         ".youtu.be", ".gstatic.com", ".googleapis.com", ".ggpht.com")
# ponytail: single-label/known-infra hosts EasyList only ever targets by path
# (google.com/adsense/..., cse.google.com/cse_v2/ads). Host-wide blocking of these
# kills sign-in, reCAPTCHA and site search. Path rule or nothing.
PATH_ONLY = {"google.com", "www.google.com", "cse.google.com", "mail-ads.google.com",
             "googleadapis.l.google.com", "blogger.googleusercontent.com"}

hosts, path_filters, cosmetics = set(), set(), set()
HOST_ONLY = re.compile(r"^\|\|([a-z0-9][a-z0-9._-]*\.[a-z]{2,})\^?$", re.I)
HOST_PATH = re.compile(r"^\|\|([a-z0-9][a-z0-9._-]*\.[a-z]{2,})([/?][^\s]*)?$", re.I)
VALID = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?:\.[a-z0-9-]{1,63})+$", re.I)

for name in ("easylist.txt", "easylist_adservers.txt"):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        continue
    for line in open(p, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line[0] in "![" or line.startswith("@@"):
            continue
        if line.startswith("#"):
            m = re.search(r"##([^{}:]+)$", line)
            if m:
                for part in m.group(1).split(","):
                    sel = part.strip()
                    if sel and re.fullmatch(r"[.#][A-Za-z0-9_-]+", sel) and sel not in BAIT:
                        cosmetics.add(sel)
            continue
        body = line.split("$", 1)[0]          # drop $options: we don't honour them
        # ponytail: '^' is EasyList's separator anchor; dropping it keeps host-only
        # rules as host-only and path rules as path rules. ~48k rules depend on this.
        body = body.replace("^", "")
        if body.endswith("|"):
            body = body[:-1]
        m = HOST_PATH.match(body)
        if not m:
            continue
        h = m.group(1).lower()
        rest = m.group(2) or ""
        if "*" in h or ".." in h or not VALID.match(h):
            continue
        protected = h in [n.lstrip(".") for n in NEVER] or h.endswith(NEVER)
        if protected:
            continue
        if not rest:
            if h not in PATH_ONLY:
                hosts.add(h)
        else:
            # ponytail: path rules become urlFilter, not requestDomains. A path rule on
            # google.com means "block google.com/adsense/ads.js", NOT all of google.com.
            uf = "||" + h + rest
            if len(uf) <= 250 and not uf.endswith("|"):
                path_filters.add(uf)

CHUNK = 500
hosts = sorted(hosts)
rules, rid = [], 1
TYPES_H = ["script", "xmlhttprequest", "sub_frame", "image", "media", "ping", "other", "object",
           "font", "websocket"]
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

# path rules: one DNR rule per filter (DNR needs a distinct urlFilter per rule).
# ponytail: main_frame deliberately absent -- a document-level redirect would
# break navigation. Add "main_frame" only for rules you have audited.
for uf in sorted(path_filters):
    if rid > 24000:      # static ruleset cap guard
        break
    rules.append({"id": rid, "priority": 1,
                  "action": {"type": "redirect", "redirect": {"extensionPath": "/stub.js"}},
                  "condition": {"urlFilter": uf, "resourceTypes":
                                ["script", "xmlhttprequest", "sub_frame", "image", "media",
                                 "ping", "other", "object"]}})
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

print(f"hosts={len(hosts)} path={len(path_filters)} rules={len(rules)} cosmetic={len(cosmetics)}")


def _selfcheck():
    """Smallest thing that fails if the conversion logic breaks."""
    for r in rules:
        c = r["condition"]
        for d in c.get("requestDomains", []):
            assert VALID.match(d), d
            assert d not in [n.lstrip(".") for n in NEVER], d
            assert d not in PATH_ONLY, d
        if "urlFilter" in c:
            assert c["urlFilter"].startswith("||"), c
            assert "main_frame" not in c["resourceTypes"], c
    assert ".adsbygoogle" not in cosmetics
    assert len({r["id"] for r in rules}) == len(rules), "duplicate rule ids"


if __name__ == "__main__":
    _selfcheck()
    print("selfcheck: ok")
