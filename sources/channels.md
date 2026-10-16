# Source 1: YouTube channels

One channel per line, as `- <channel URL>  # optional note`. Only lines starting with `- https://...youtube.com/...` are read.
`scripts/collect_youtube.py` pulls the latest videos from each channel and saves their transcripts to `raw/youtube/`.

- https://www.youtube.com/@anthropic-ai  # test channel; replace with your list
