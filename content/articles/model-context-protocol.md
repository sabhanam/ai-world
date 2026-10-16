---
title: Model Context Protocol (MCP)
slug: model-context-protocol
kind: concept
status: complete
summary: An open standard that lets AI assistants plug into outside tools and data, so one connector works with many apps.
tags: [agents, tooling, anthropic]
related: [ai-agents, claude-code, rag-pipelines]
sponsored: false
updated: 2026-10-17
sources:
  - https://modelcontextprotocol.io/ [official]
  - https://www.anthropic.com/news/model-context-protocol [official]
  - https://github.com/modelcontextprotocol
---

## In plain words
An AI assistant on its own only knows what it was trained on and what you paste in. MCP is a common "plug shape" that lets it connect to other things, like your files, a database, GitHub or a calendar, so it can look things up and take actions. Anthropic introduced it in November 2024 as an open standard, and many other AI apps now support it.

## Key takeaways
- One connector, called an MCP server, works in every app that supports MCP.
- It's what lets an assistant act, not just chat: search docs, open tickets, query data.
- Only install servers you trust, because a server can do whatever its code allows.

## What it is
MCP (Model Context Protocol) is a set of rules for how an AI app and an outside tool talk to each other. A protocol is just an agreed way of exchanging messages, the way every website speaks HTTP.

Before MCP, every AI app needed its own custom connector for every tool. With MCP, a tool maker writes **one MCP server**, and any app that speaks MCP can use it.

## Why it matters
- **Less duplicated work.** Write a connector once and it works in Claude, IDEs and other agents.
- **Assistants can act, not just chat.** With the right servers, an assistant can search your docs, open a pull request or query a database.
- **You stay in control.** Apps usually ask before a tool runs, and you choose which servers to install.

## How it works
Think of a power strip: the AI app is the wall socket, and each MCP server is a device you plug in.

1. **Host:** the app you use, such as Claude Desktop or an IDE. It runs an **MCP client** for each server it connects to.
2. **Server:** a small program that wraps one tool or data source. It tells the client what it offers:
    - **Tools:** actions the AI can call, like `create_issue`.
    - **Resources:** data it can read, like a file.
    - **Prompts:** ready-made instructions.
3. **Conversation:** when you ask something, the model sees the list of available tools and decides to call one. The client sends the request to the server, which does the work and returns the result for the model to use in its answer.

```
You -> AI app (host) -> MCP client -> MCP server -> GitHub / files / database
                ^                          |
                +-------- result ----------+
```

Servers can run on your own machine, talking over standard input/output, or remotely over HTTP.

## Things to watch
- **Security:** a server can do whatever its code allows. Only install servers you trust, and watch for prompt injection.
- **Quality varies:** there are thousands of community servers, and not all are maintained.
