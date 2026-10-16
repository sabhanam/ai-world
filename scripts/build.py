"""Build articles/<slug>.html and data/articles.json from content/articles/*.md and content/glossary.md."""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "articles"
GLOSSARY = ROOT / "content" / "glossary.md"
OUT = ROOT / "articles"
INDEX = ROOT / "data" / "articles.json"
SITE_URL = "https://sabhanam.github.io/ai-world"
KINDS = {"product", "concept", "news"}
STATUSES = {"wip", "complete"}
SOURCE_LABELS = {"official": "Official", "press": "Press", "video": "Video", "code": "Code", "web": "Web"}
PRESS = {"techcrunch.com", "theverge.com", "wired.com", "arstechnica.com", "reuters.com", "bloomberg.com",
         "nytimes.com", "ft.com", "venturebeat.com", "technologyreview.com", "cnbc.com", "theinformation.com",
         "wikipedia.org"}
STATUS_TEXT = {"wip": "Still researching", "complete": "Researched"}
VERDICTS = {"worth-trying": "Worth trying", "watch": "Watch this", "hype": "Mostly hype"}
# The sections a finished page of each kind has. Progress bars count these.
SECTIONS = {
    "concept": ["In plain words", "Key takeaways", "What it is", "How it works", "Why it matters", "Things to watch"],
    "product": ["In plain words", "Key takeaways", "What it is", "Why it matters", "Things to watch"],
    "news": ["In plain words", "Key takeaways", "What happened", "Why it matters", "Things to watch"],
}
FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,500..800"
         "&family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap")
e = lambda s: html.escape(str(s), quote=True)


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


def source(raw):
    """`https://x.dev [official]` -> (url, label). Without a label, guess from the domain."""
    m = re.match(r"^(\S+)(?:\s+\[(\w+)\])?$", raw.strip())
    url, label = m.group(1), (m.group(2) or "").lower()
    if label not in SOURCE_LABELS:
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host in ("youtube.com", "youtu.be", "m.youtube.com"):
            label = "video"
        elif host == "github.com":
            label = "code"
        elif any(host == p or host.endswith("." + p) for p in PRESS):
            label = "press"
        else:
            label = "web"
    return url, label


def load(path):
    meta, body = parse(path.read_text(encoding="utf-8"))
    for f in ("title", "summary", "kind", "status", "updated"):
        if not meta.get(f):
            raise ValueError(f"{path.name}: missing {f}")
    if meta["kind"] not in KINDS or meta["status"] not in STATUSES:
        raise ValueError(f"{path.name}: bad kind/status")
    meta["slug"] = meta.get("slug") or path.stem
    meta["tags"] = meta.get("tags") or []
    meta["related"] = meta.get("related") or []
    meta["sources"] = [source(s) for s in meta.get("sources") or []]
    meta["sponsored"] = str(meta.get("sponsored", "")).lower() == "true"
    meta["read"] = max(1, round(len(re.findall(r"\w+", body)) / 220))
    if meta.get("verdict") and meta["verdict"] not in VERDICTS:
        raise ValueError(f"{path.name}: verdict must be one of {', '.join(VERDICTS)}")
    meta["take_approved"] = str(meta.get("take_approved", "")).lower() == "true"
    have = {h.strip() for h in re.findall(r"^## (.+)$", body, re.M)}
    meta["missing"] = [h for h in SECTIONS[meta["kind"]] if h not in have]
    meta["progress"] = [len(SECTIONS[meta["kind"]]) - len(meta["missing"]), len(SECTIONS[meta["kind"]])]
    meta["found"] = provenance(meta)
    return meta, body


def provenance(meta):
    """Where this topic was first picked up: the raw file in `found_in`, else the first source's site."""
    raw = ROOT / meta["found_in"] if meta.get("found_in") else None
    if raw and raw.is_file():
        r, _ = parse(raw.read_text(encoding="utf-8"))
        if r.get("source") == "youtube":
            return {"text": f"First heard in {r.get('channel', 'a video')} on YouTube, {r.get('published', '')}", "url": r.get("url")}
        return {"text": f"First read on {r.get('site', 'the web')}, {r.get('published', '')}", "url": r.get("url")}
    if meta["sources"]:
        url = meta["sources"][0][0]
        return {"text": f"First found on {urlparse(url).netloc.removeprefix('www.')}", "url": url}
    return None


def progress_bar(done, total):
    cells = "".join(f'<i class="{"on" if n < done else ""}"></i>' for n in range(total))
    return f'<span class="meter" role="img" aria-label="{done} of {total} sections written">{cells}</span>'


def load_glossary():
    """Lines like `- **API**: a way for one program to ask another for something.`"""
    if not GLOSSARY.exists():
        return {}
    return dict(re.findall(r"^-\s+\*\*(.+?)\*\*:\s*(.+)$", GLOSSARY.read_text(encoding="utf-8"), re.M))


def add_terms(content, glossary, title):
    """Wrap the first use of each glossary term in a hover/focus definition. Skips code, links and headings."""
    remaining = {t: d for t, d in glossary.items() if t.lower() not in title.lower()}
    if not remaining:
        return content
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(remaining, key=len, reverse=True)) + r")\b")
    lookup = {t.lower(): (t, d) for t, d in remaining.items()}
    used, skip, out = set(), 0, []
    for part in re.split(r"(<[^>]+>)", content):
        if part.startswith("<"):
            tag = re.match(r"</?(\w+)", part)
            if tag and tag.group(1) in ("code", "pre", "a", "h1", "h2", "h3"):
                skip += -1 if part.startswith("</") else 1
            out.append(part)
            continue
        if skip:
            out.append(part)
            continue

        def wrap(m):
            key = m.group(1).lower()
            if key in used or key not in lookup:
                return m.group(0)
            used.add(key)
            return (f'<span class="term" tabindex="0">{m.group(0)}'
                    f'<span class="def" role="tooltip">{e(lookup[key][1])}</span></span>')
        out.append(pattern.sub(wrap, part))
    return "".join(out)


def page(meta, body, by_slug, glossary):
    url = f"{SITE_URL}/articles/{meta['slug']}.html"
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])
    content = md.convert(body)
    toc = [(t["id"], t["name"]) for t in md.toc_tokens]
    # The two summary sections get boxes: they're what a skimming reader stops at.
    for name, cls in (("In plain words", "plain"), ("Key takeaways", "takeaways")):
        content = re.sub(rf'<h2 id="([^"]+)">{name}</h2>(.*?)(?=<h2|$)',
                         rf'<aside class="{cls}" aria-labelledby="\1"><h2 id="\1">{name}</h2>\2</aside>',
                         content, count=1, flags=re.S)
    content = add_terms(content, glossary, meta["title"])
    # Sections the researcher hasn't written yet show as placeholders, so the page visibly grows.
    content += "".join(
        f'<section class="pending" aria-label="{e(h)}, not written yet"><h2>{e(h)}</h2>'
        f'<p>Being researched.</p><span class="ghost"></span><span class="ghost short"></span></section>'
        for h in meta["missing"])

    take = ""
    if meta.get("take") and meta.get("verdict"):
        label = "My take" if meta["take_approved"] else "Draft take, not reviewed yet"
        take = (f'<aside class="take v-{e(meta["verdict"])}{"" if meta["take_approved"] else " draft"}">'
                f'<p class="take-head"><span>{label}</span><strong>{VERDICTS[meta["verdict"]]}</strong></p>'
                f'<p>{e(meta["take"])}</p></aside>')
    found = meta["found"]
    found_html = (f'<p class="found"><a href="{e(found["url"])}" rel="noopener">{e(found["text"])}</a>. '
                  f'Researched from {len(meta["sources"])} source{"s" if len(meta["sources"]) != 1 else ""}.</p>') if found else ""

    notes = ""
    if meta["status"] == "wip":
        notes += ('<p class="note wip">This page is still being researched. '
                  "What's here comes from the first source; more detail and references are on the way.</p>")
    if meta["sponsored"]:
        notes += ('<p class="note sponsored">At least one source was sponsored. '
                  "Claims that only the sponsor makes are marked as such.</p>")
    toc_html = "".join(f'<li><a href="#{e(i)}">{e(n)}</a></li>' for i, n in toc)
    sources = "".join(
        f'<li><span class="src-label {lbl}">{SOURCE_LABELS[lbl]}</span>'
        f'<a href="{e(u)}" rel="noopener">{e(urlparse(u).netloc.removeprefix("www.") + urlparse(u).path.rstrip("/"))}</a></li>'
        for u, lbl in meta["sources"])
    related = "".join(
        f'<li class="k-{e(r["kind"])}"><a href="{e(r["slug"])}.html"><span class="kind">{e(r["kind"])}</span>'
        f'<span class="rel-title">{e(r["title"])}</span><span class="rel-sum">{e(r["summary"])}</span></a></li>'
        for r in (by_slug[s] for s in meta["related"]))
    related_html = (f'<section class="related" aria-labelledby="rel"><h2 id="rel">Related topics</h2>'
                    f'<ul>{related}</ul></section>') if related else ""
    tags = "".join(f'<li><a href="../?tag={e(t)}#topics">{e(t)}</a></li>' for t in meta["tags"])
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
<script>try{{const t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch{{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="../styles.css">
</head>
<body class="post-page">
<div class="progress" aria-hidden="true"></div>
<header class="site-nav">
  <a class="brand" href="../"><span class="mark" aria-hidden="true"><i></i><i></i><i></i></span><span>AI <b>World</b></span></a>
  <nav><a href="../#map">Map</a><a href="../#topics">All topics</a><button class="theme-toggle" type="button" aria-label="Switch colour theme"></button></nav>
</header>
<main>
<article class="post k-{e(meta['kind'])}">
  <header class="post-head">
    <p class="post-meta"><a class="kind" href="../?kind={e(meta['kind'])}#topics">{e(meta['kind'])}</a><span class="status {e(meta['status'])}">{STATUS_TEXT[meta['status']]}</span><time datetime="{e(meta['updated'])}">Updated {e(meta['updated'])}</time><span>{meta['read']} min read</span><span class="meter-wrap">{progress_bar(*meta['progress'])}{meta['progress'][0]} of {meta['progress'][1]} sections</span></p>
    <h1>{e(meta['title'])}</h1>
    <p class="lede">{e(meta['summary'])}</p>
    {found_html}
  </header>
  <div class="post-layout">
    <nav class="toc" aria-label="On this page"><p>On this page</p><ol>{toc_html}<li><a href="#src">Sources</a></li></ol></nav>
    <div class="post-body">
      {take}{notes}
      <div class="prose">{content}</div>
      <section class="post-sources" aria-labelledby="src">
        <h2 id="src">Sources</h2>
        <ol>{sources}</ol>
      </section>
      {related_html}
      <footer class="post-foot">
        <ul class="tags">{tags}</ul>
        <button class="btn ghost" type="button" data-copy="{url}">Copy link</button>
      </footer>
    </div>
  </div>
</article>
</main>
<footer class="site-foot"><p>AI World is collected, researched and written by AI agents, then curated by <a href="https://sabhanam.github.io/me/">Sabhanam Sree Sai Ram</a>.</p></footer>
<script src="../site.js"></script>
</body>
</html>
"""


def build():
    OUT.mkdir(exist_ok=True)
    INDEX.parent.mkdir(exist_ok=True)
    loaded = [load(p) for p in sorted(SRC.glob("*.md"))]
    by_slug = {m["slug"]: m for m, _ in loaded}
    for meta, _ in loaded:
        missing = [s for s in meta["related"] if s not in by_slug]
        if missing:
            print(f"warning: {meta['slug']}: unknown related {missing}")
        meta["related"] = [s for s in meta["related"] if s in by_slug and s != meta["slug"]]
    glossary = load_glossary()
    items = []
    for meta, body in loaded:
        (OUT / f"{meta['slug']}.html").write_text(page(meta, body, by_slug, glossary), encoding="utf-8")
        item = {k: meta[k] for k in ("slug", "title", "kind", "status", "summary", "tags", "updated",
                                     "sponsored", "read", "related", "progress", "found")}
        if meta.get("verdict"):
            item["verdict"] = meta["verdict"]
            item["take_approved"] = meta["take_approved"]
        item["sources"] = len(meta["sources"])
        items.append(item)
    # Drop pages whose markdown was removed.
    for old in OUT.glob("*.html"):
        if old.stem not in by_slug:
            old.unlink()
    items.sort(key=lambda i: i["updated"], reverse=True)
    INDEX.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {len(items)} articles, {len(glossary)} glossary terms")
    return items


if __name__ == "__main__":
    build()
