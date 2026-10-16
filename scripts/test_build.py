"""Run: .venv/bin/python scripts/test_build.py"""
import json
from build import parse, build, INDEX

meta, body = parse("""---
title: "Quoted: title"
kind: concept   # product | concept | news
tags: [a, b]
sources:
  - https://x.dev/a#frag
  - 'https://y.dev'
---
## Body
""")
assert meta == {"title": "Quoted: title", "kind": "concept", "tags": ["a", "b"],
                "sources": ["https://x.dev/a#frag", "https://y.dev"]}, meta
assert body.startswith("## Body")

items = build()
assert items == json.loads(INDEX.read_text())
assert all({"slug", "title", "kind", "status", "summary", "tags", "updated", "read", "sources"} <= i.keys() for i in items)
assert [i["updated"] for i in items] == sorted((i["updated"] for i in items), reverse=True)
print("ok")

from build import source, add_terms
assert source("https://openai.com/x [official]") == ("https://openai.com/x", "official")
assert source("https://www.youtube.com/watch?v=1") == ("https://www.youtube.com/watch?v=1", "video")
assert source("https://github.com/a/b")[1] == "code"
assert source("https://en.wikipedia.org/wiki/X")[1] == "press"
out = add_terms("<p>An LLM is an LLM.</p><pre><code>LLM</code></pre>", {"LLM": "a model"}, "Agents")
assert out.count('class="term"') == 1 and "<code>LLM</code>" in out, out
assert add_terms("<p>LLM</p>", {"LLM": "a model"}, "What is an LLM") == "<p>LLM</p>"  # page about the term itself
print("ok: sources and glossary")
