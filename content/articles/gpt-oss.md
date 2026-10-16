---
title: OpenAI releases gpt-oss, its first open-weight models since GPT-2
slug: gpt-oss
kind: news
status: complete
summary: In August 2025 OpenAI published two open-weight reasoning models, gpt-oss-120b and gpt-oss-20b, free to download and run under Apache 2.0.
tags: [open-models, openai]
related: [ai-agents]
verdict: watch
take: "A strong option for private or offline use. Compare it with other open models on your own tasks before switching."
take_approved: false
sponsored: false
updated: 2026-10-13
sources:
  - https://openai.com/index/introducing-gpt-oss/ [official]
  - https://github.com/openai/gpt-oss
---

## In plain words
OpenAI, the company behind ChatGPT, usually keeps its models private and rents access to them. With gpt-oss it published two models anyone can download and run on their own hardware, the first time it had done so since GPT-2 in 2019. That gives companies a capable model they can run privately, without sending data to OpenAI.

## Key takeaways
- Two sizes: gpt-oss-120b for a single large GPU and gpt-oss-20b for a high-end laptop or desktop.
- Released under Apache 2.0, so commercial use is allowed.
- Built for reasoning and tool use, the skills agents need.

## What happened
On 2025-08-05 OpenAI released gpt-oss-120b and gpt-oss-20b as open-weight models. OpenAI says the larger one performs close to its o4-mini model on reasoning benchmarks and fits on a single 80 GB GPU, while the smaller one runs on devices with 16 GB of memory.

## Why it matters
Open-weight models from Meta, Mistral, DeepSeek and Qwen had been closing the gap with closed models. OpenAI joining in gives developers another strong option they can run offline, fine-tune and inspect, which matters for privacy-sensitive work and for cost.

## Things to watch
- Benchmark comparisons are OpenAI's own; independent tests vary by task.
- Running the larger model still needs expensive hardware.
