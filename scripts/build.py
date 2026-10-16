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
    OUT.mkdir(exist_ok=True)
    INDEX.parent.mkdir(exist_ok=True)
    items = []
    for path in sorted(SRC.glob("*.md")):
        meta, body = load(path)
        meta["read"] = read_minutes(body)
        (OUT / f"{meta['slug']}.html").write_text(page(meta, body), encoding="utf-8")
        item = {k: meta[k] for k in ("slug", "title", "kind", "status", "summary", "tags", "updated", "sponsored", "read")}
        item["sources"] = len(meta["sources"])
        items.append(item)
    # Drop pages whose markdown was removed.
    live = {i["slug"] for i in items}
    for old in OUT.glob("*.html"):
        if old.stem not in live:
            old.unlink()
    items.sort(key=lambda i: i["updated"], reverse=True)
    INDEX.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {len(items)} articles")
    return items


if __name__ == "__main__":
    build()
