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
