---
description: Run the AI World pipeline — collect YouTube + web sources, write WIP pages, research them, build the site, commit and push.
argument-hint: "[--no-push] [--max-research N]"
---

Run the AI World pipeline from the repo root. Arguments: $ARGUMENTS (defaults: push at the end, `--max-research 5`).

1. **Collect YouTube.** Run `.venv/bin/python scripts/collect_youtube.py`. Its stdout lists the new raw files, one per line. Its stderr lists skipped channels and videos, so keep a note of them for the summary.
2. **Collect web.** Launch the `web-collector` agent. Take the paths under `NEW FILES` in its report.
3. If steps 1–2 found no new files, still continue. The writer will look for raw files that no article cites yet.
4. **Write.** Launch the `writer` agent with the full list of new raw file paths. Take the slugs under `WIP SLUGS` in its report.
5. **Research.** Launch one `researcher` agent per WIP slug, **in parallel** (one message, several Agent calls), up to the `--max-research` cap. If there are more slugs than the cap, leave the rest as WIP for the next run and say so.
6. **Build.** Run `.venv/bin/python scripts/build.py`. If it fails on a bad article file, fix that file's frontmatter (only the frontmatter) and rerun.
7. **Commit and push.** Stage `raw/`, `content/` and `articles/`, plus `data/articles.json`, and commit with the message `AI World run <YYYY-MM-DD>: <n> new sources, <n> pages updated`. Push to `origin main` unless `--no-push` was given.
8. **Summarize** in a few lines:
   - new sources by channel or site
   - pages created, updated and completed
   - what is still WIP
   - anything that failed
