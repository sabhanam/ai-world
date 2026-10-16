"""Build articles/<slug>.html and data/articles.json from content/articles/*.md."""
import html
import json
import math
import random
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "articles"
OUT = ROOT / "articles"
INDEX = ROOT / "data" / "articles.json"
SITE_URL = "https://sabhanam.github.io/ai-world"
KINDS = {"product", "concept", "news"}
STATUSES = {"wip", "complete"}


def parse(text):
    """Split '---' frontmatter from the body. Supports `k: v`, `k: [a, b]` and block `- item` lists."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("missing --- frontmatter")
    meta, key = {}, None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key:
            meta.setdefault(key, []).append(unquote(item.group(1)))
            continue
        k, _, v = line.partition(":")
        key, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[key] = [unquote(x) for x in v[1:-1].split(",") if x.strip()]
        elif v:
            meta[key] = unquote(v)
    return meta, m.group(2)


def unquote(v):
    v = re.sub(r"\s+#.*$", "", v).strip()  # drop trailing `# comment`
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def load(path):
    meta, body = parse(path.read_text(encoding="utf-8"))
    for f in ("title", "summary", "kind", "status", "updated"):
        if not meta.get(f):
            raise ValueError(f"{path.name}: missing {f}")
    if meta["kind"] not in KINDS or meta["status"] not in STATUSES:
        raise ValueError(f"{path.name}: bad kind/status")
    meta["slug"] = meta.get("slug") or path.stem
    meta["tags"] = meta.get("tags") or []
    meta["sources"] = meta.get("sources") or []
    meta["sponsored"] = str(meta.get("sponsored", "")).lower() == "true"
    return meta, body



# Kind -> (gradient start, gradient end, glow). Covers are the one bold element of the design.
PALETTE = {
    "concept": ("#1b2f8f", "#3b5bf0", "#8fa6ff"),
    "product": ("#9a3412", "#f97316", "#ffd2ad"),
    "news": ("#4c1d95", "#8b5cf6", "#d6c4ff"),
}


def cover(slug, kind):
    """A 'signal' cover: light lines flowing over the kind's colour, shaped by the slug so each topic keeps its look."""
    start, end, glow = PALETTE[kind]
    rnd = random.Random(slug)
    w, h = 1200, 630
    paths = []
    n = 11
    hero = rnd.randrange(3, n - 3)  # the one line that stands out: the signal in the noise
    for i in range(n):
        base = h * (0.12 + 0.76 * i / (n - 1))
        amp = rnd.uniform(30, 120)
        freq = rnd.uniform(0.5, 1.5)
        phase = rnd.uniform(0, math.tau)
        pts = [(x, base + amp * math.sin(freq * x / w * math.tau + phase) + rnd.uniform(-12, 12))
               for x in range(-100, w + 201, 150)]
        d = f"M{pts[0][0]},{pts[0][1]:.0f} Q{pts[1][0]},{pts[1][1]:.0f} {pts[2][0]},{pts[2][1]:.0f}"
        d += "".join(f" T{x},{y:.0f}" for x, y in pts[3:])
        if i == hero:
            paths.append(f'<path d="{d}" stroke="#ffffff" stroke-width="5" opacity="0.95"/>')
        else:
            paths.append(f'<path d="{d}" stroke="{glow}" stroke-width="1.5" opacity="{round(0.18 + 0.42 * rnd.random(), 2)}"/>')
    cx, cy = rnd.randint(200, 1000), rnd.randint(120, 500)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{start}"/><stop offset="1" stop-color="{end}"/></linearGradient>'
        f'<radialGradient id="r" cx="{cx}" cy="{cy}" r="520" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{glow}" stop-opacity="0.45"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{w}" height="{h}" fill="url(#g)"/><rect width="{w}" height="{h}" fill="url(#r)"/>'
        f'<g fill="none" stroke-linecap="round">{"".join(paths)}</g></svg>\n'
    )


def read_minutes(body):
    return max(1, round(len(re.findall(r"\w+", body)) / 220))


def page(meta, body):
    e = lambda s: html.escape(str(s), quote=True)
    url = f"{SITE_URL}/articles/{meta['slug']}.html"
    content = markdown.markdown(body, extensions=["fenced_code", "tables"])
    # The plain-words summary is the page's most important part, so it gets its own box.
    content = re.sub(r"<h2>In plain words</h2>(.*?)(?=<h2>|$)",
                     r'<aside class="plain"><h2>In plain words</h2>\1</aside>', content, count=1, flags=re.S)
    notes = ""
    if meta["status"] == "wip":
        notes += ('<p class="note wip">This page is still being researched. '
                  "What's here comes from the first source; more detail and references are on the way.</p>")
    if meta["sponsored"]:
        notes += ('<p class="note sponsored">At least one source was sponsored. '
                  "Claims that only the sponsor makes are marked as such.</p>")
    sources = "".join(f'<li><a href="{e(s)}" rel="noopener">{e(s)}</a></li>' for s in meta["sources"])
    tags = "".join(f"<li>{e(t)}</li>" for t in meta["tags"])
    status = "Still researching" if meta["status"] == "wip" else "Researched"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(meta['title'])} | AI World</title>
<meta name="description" content="{e(meta['summary'])}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="AI World">
<meta property="og:title" content="{e(meta['title'])}">
<meta property="og:description" content="{e(meta['summary'])}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="{url}">
<link rel="icon" href="data:,">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../styles.css">
</head>
<body class="post-page">
<div class="progress" aria-hidden="true"></div>
<header class="site-nav"><a class="brand" href="../"><span class="mark" aria-hidden="true"></span>AI World</a><nav><a href="../#topics">All topics</a><a href="https://sabhanam.github.io/me/">About me</a></nav></header>
<main>
<article class="post">
  <header class="post-head">
    <p class="post-meta"><a class="kind k-{e(meta['kind'])}" href="../?kind={e(meta['kind'])}#topics">{e(meta['kind'])}</a><span class="status {e(meta['status'])}">{status}</span><time datetime="{e(meta['updated'])}">Updated {e(meta['updated'])}</time><span>{meta['read']} min read</span></p>
    <h1>{e(meta['title'])}</h1>
    <p class="lede">{e(meta['summary'])}</p>
  </header>
  <figure class="post-cover"><img src="covers/{e(meta['slug'])}.svg" alt="" width="1200" height="630"></figure>
  <div class="post-body">
    {notes}
    <div class="prose">{content}</div>
    <section class="post-sources" aria-labelledby="src">
      <h2 id="src">Sources</h2>
      <ol>{sources}</ol>
    </section>
    <footer class="post-foot">
      <ul class="tags">{tags}</ul>
      <button class="btn ghost" type="button" data-copy="{url}">Copy link</button>
    </footer>
  </div>
</article>
</main>
<footer class="site-foot"><p>AI World is collected, researched and written by AI agents, then curated by <a href="https://sabhanam.github.io/me/">Sabhanam Sree Sai Ram</a>.</p></footer>
<script>
document.querySelector("[data-copy]").addEventListener("click", async (ev) => {{
  const b = ev.currentTarget;
  try {{ await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "Link copied"; }}
  catch {{ b.textContent = b.dataset.copy; }}
}});
</script>
</body>
</html>
"""


def build():
    covers = OUT / "covers"
    covers.mkdir(parents=True, exist_ok=True)
    INDEX.parent.mkdir(exist_ok=True)
    items = []
    for path in sorted(SRC.glob("*.md")):
        meta, body = load(path)
        meta["read"] = read_minutes(body)
        (OUT / f"{meta['slug']}.html").write_text(page(meta, body), encoding="utf-8")
        (covers / f"{meta['slug']}.svg").write_text(cover(meta["slug"], meta["kind"]), encoding="utf-8")
        item = {k: meta[k] for k in ("slug", "title", "kind", "status", "summary", "tags", "updated", "sponsored", "read")}
        item["sources"] = len(meta["sources"])
        items.append(item)
    # Drop pages and covers whose markdown was removed.
    live = {i["slug"] for i in items}
    for old in [*OUT.glob("*.html"), *covers.glob("*.svg")]:
        if old.stem not in live:
            old.unlink()
    items.sort(key=lambda i: i["updated"], reverse=True)
    INDEX.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {len(items)} articles")
    return items


if __name__ == "__main__":
    build()
