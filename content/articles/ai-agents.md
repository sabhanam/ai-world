---
title: AI agents
slug: ai-agents
kind: concept
status: complete
summary: An AI agent is a language model that works in a loop, choosing tools and taking steps on its own until a task is done.
tags: [agents, basics]
related: [model-context-protocol, claude-code, rag-pipelines]
sponsored: false
updated: 2026-10-15
sources:
  - https://www.anthropic.com/engineering/building-effective-agents [official]
  - https://modelcontextprotocol.io/ [official]
---

## In plain words
A chat assistant answers one message at a time. An agent is given a goal instead, like "fix this bug" or "find me three flights under $400", and works towards it on its own. It decides what to do next, uses tools such as search or a code editor, looks at the result and repeats until it's finished or stuck.

## Key takeaways
- An agent is an LLM plus tools plus a loop: think, act, check, repeat.
- The tools are what make it useful; MCP is a common way to plug them in.
- Simple, well-defined tasks work best. Long open-ended ones still go wrong.

## What it is
Anthropic separates two designs. **Workflows** follow steps a developer wrote in advance, with the model filling in each step. **Agents** let the model decide the steps itself, based on what it sees as it goes. Many products called "agents" are really workflows, and that's often the more reliable choice.

## How it works
1. **Goal:** you give the agent a task and a set of tools, for example web search, a file editor or a calendar API.
2. **Plan a step:** the model reads the goal and everything so far, then picks one action, such as "search for X".
3. **Act:** the app runs that tool and hands the result back to the model.
4. **Check:** the model looks at the result. Did it work? What's next?
5. **Repeat** until the task is done, a step limit is reached, or it asks a human for help.

It's like an intern with a checklist who reports back after each step, except the intern writes their own checklist as they go.

## Why it matters
Agents turn AI from something that answers into something that does work: coding tools that change files and run tests, research tools that read dozens of pages, support bots that can actually issue a refund.

## Things to watch
- **Errors compound:** a wrong step early can send the whole run off course.
- **Cost and time:** every loop is another model call.
- **Safety:** an agent with real tools can do real damage, so good systems ask before risky actions.
