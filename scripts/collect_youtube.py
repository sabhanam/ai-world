"""Source 1: save transcripts of the latest videos from each channel in sources/channels.md.

Usage: .venv/bin/python scripts/collect_youtube.py [--per-channel 5]
Writes raw/youtube/<channel>/<date>-<videoId>.md and records ids in raw/seen.json.
Prints the paths of new files, one per line, so the next step knows what is new.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parent.parent
CHANNELS = ROOT / "sources" / "channels.md"
RAW = ROOT / "raw" / "youtube"
SEEN = ROOT / "raw" / "seen.json"


def channel_urls(text):
    """Lines like `- https://www.youtube.com/@handle  # note`. Everything else is ignored."""
    return re.findall(r"^\s*-\s+(https?://\S*youtube\.com/\S+)", text, re.M)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "channel"


def load_seen():
    return json.loads(SEEN.read_text()) if SEEN.exists() else {"youtube": [], "web": []}


def latest_videos(url, n):
    url = url.rstrip("/")
    if "/@" in url and not url.endswith("/videos"):
        url += "/videos"
    opts = {"extract_flat": True, "playlistend": n, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    channel = info.get("channel") or info.get("uploader") or info.get("title") or url
    return channel, [v for v in info.get("entries") or [] if v.get("id")]


def video_details(video_id):
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
        return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)


def transcript(video_id):
    fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en", "en-US", "en-GB"])
    return " ".join(s.text.replace("\n", " ") for s in fetched)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-channel", type=int, default=5)
    args = ap.parse_args()

    seen = load_seen()
    done = set(seen["youtube"])
    urls = channel_urls(CHANNELS.read_text(encoding="utf-8"))
    if not urls:
        print("no channels in sources/channels.md", file=sys.stderr)
        return
    for url in urls:
        try:
            channel, videos = latest_videos(url, args.per_channel)
        except Exception as ex:  # one bad channel must not stop the rest
            print(f"skip channel {url}: {ex}", file=sys.stderr)
            continue
        for v in videos:
            vid = v["id"]
            if vid in done:
                continue
            try:
                info = video_details(vid)
                text = transcript(vid)
            except Exception as ex:
                print(f"skip video {vid}: {type(ex).__name__}", file=sys.stderr)
                continue
            d = info.get("upload_date") or "00000000"
            date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            out = RAW / slugify(channel) / f"{date}-{vid}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            title = (info.get("title") or vid).replace('"', "'")
            out.write_text(
                f'---\ntitle: "{title}"\nurl: https://www.youtube.com/watch?v={vid}\n'
                f'channel: "{channel}"\npublished: {date}\nsource: youtube\n---\n\n'
                f"{info.get('description') or ''}\n\n## Transcript\n\n{text}\n",
                encoding="utf-8",
            )
            seen["youtube"].append(vid)
            done.add(vid)
            SEEN.write_text(json.dumps(seen, indent=2) + "\n")  # save as we go so a crash keeps progress
            print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
