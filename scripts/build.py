"""Build articles/<slug>.html and data/articles.json from content/articles/*.md."""
import html
import json
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


def page(meta, body):
    e = lambda s: html.escape(str(s), quote=True)
    url = f"{SITE_URL}/articles/{meta['slug']}.html"
    content = markdown.markdown(body, extensions=["fenced_code", "tables"])
    wip = (
        '<p class="banner">Work in progress: the AI is still researching this one. '
        "Facts may be incomplete.</p>"
        if meta["status"] == "wip" else ""
    )
    sponsored = (
        '<p class="banner warm">Some sources for this page were sponsored. Claims from them are flagged.</p>'
        if meta["sponsored"] else ""
    )
    sources = "".join(f'<li><a href="{e(s)}" rel="noopener">{e(s)}</a></li>' for s in meta["sources"])
    tags = "".join(f"<li>{e(t)}</li>" for t in meta["tags"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(meta['title'])} · AI World</title>
<meta name="description" content="{e(meta['summary'])}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(meta['title'])}">
<meta property="og:description" content="{e(meta['summary'])}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="data:,">
<link rel="stylesheet" href="../styles.css">
</head>
<body>
<header class="site-nav"><a class="brand" href="../">AI World</a><nav><a href="../">All topics</a></nav></header>
<main class="article">
  <p class="meta"><span class="kind">{e(meta['kind'])}</span><span class="status {e(meta['status'])}">{'WIP' if meta['status'] == 'wip' else 'Complete'}</span><span>Updated {e(meta['updated'])}</span></p>
  <h1>{e(meta['title'])}</h1>
  <p class="lede">{e(meta['summary'])}</p>
  {wip}{sponsored}
  <ul class="tags">{tags}</ul>
  <div class="prose">{content}</div>
  <section class="sources"><h2>Sources</h2><ol>{sources}</ol></section>
  <p><button class="btn ghost" type="button" data-copy="{url}">Copy link</button></p>
</main>
<script>
document.querySelector("[data-copy]").addEventListener("click", async (ev) => {{
  try {{ await navigator.clipboard.writeText(ev.target.dataset.copy); ev.target.textContent = "Link copied"; }}
  catch {{ prompt("Copy this link", ev.target.dataset.copy); }}
}});
</script>
</body>
</html>
"""


def build():
    OUT.mkdir(exist_ok=True)
    INDEX.parent.mkdir(exist_ok=True)
    items = []
    for path in sorted(SRC.glob("*.md")):
        meta, body = load(path)
        (OUT / f"{meta['slug']}.html").write_text(page(meta, body), encoding="utf-8")
        items.append({k: meta[k] for k in ("slug", "title", "kind", "status", "summary", "tags", "updated", "sponsored")})
    # Drop pages whose markdown was removed.
    live = {f"{i['slug']}.html" for i in items}
    for old in OUT.glob("*.html"):
        if old.name not in live:
            old.unlink()
    items.sort(key=lambda i: i["updated"], reverse=True)
    INDEX.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {len(items)} articles")
    return items


if __name__ == "__main__":
    build()
