---
title: RAG (retrieval-augmented generation)
slug: rag-pipelines
kind: concept
status: wip
summary: A way to make an AI answer from your own documents by looking up the relevant bits first and handing them to the model.
tags: [rag, search, llm-basics]
sponsored: false
updated: 2026-10-16
sources:
  - https://en.wikipedia.org/wiki/Retrieval-augmented_generation
---

## In plain words
An AI model can't read all your company's documents at once, and it can't know what it was never trained on. RAG fixes this by searching your documents for the few passages that matter to a question, then giving those passages to the model along with the question. The model answers using them, so its answer is grounded in your material.
