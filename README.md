# Zion

> Can an AI agent leave its runtime without losing who it is?

Zion is an experimental open-source project investigating **AI Agent State
Portability** — the ability to capture, serialize, and restore an agent's
meaningful state independently of the runtime executing it.

## What Zion is

- A portable state model (`ZionState`) for AI agents.
- JSON serialization with round-trip fidelity.
- Runtime adapters for investigating state extraction.
- A research tool for understanding what makes an agent *itself*.

## What Zion is not

- Not a chatbot, LLM framework, or agent framework.
- Not a vector database or memory product.
- Not a cloud service or API.
- Not a replacement for any runtime — it complements them.

## Why it matters

Today's AI agents are born inside a runtime and die with it. When you stop a
Cheshire Cat agent, its memories, decisions, and task progress are trapped
inside that process. Zion asks whether we can extract the essential state and
move it — to a file, to another instance, or eventually to a completely
different runtime.

## Architecture

```
             ZION STATE
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
     DS4      Cheshire Cat  Other
       │          │          │
       └──────────┼──────────┘
                  ↓
          Portable State
```

The core `zion` package has no dependencies on any runtime. Runtime-specific
code lives in adapters.

## Current status

**Research / Experimental** — v0.1

This is the first bootstrap phase. The state model is defined, JSON
serialization works, and adapter boundaries are drawn. No live runtime
integration has been verified yet.

## Roadmap

- [x] Initialize repository
- [ ] Define Zion State v0.1
- [ ] Implement JSON serialization
- [ ] Implement round-trip tests
- [ ] Investigate Cheshire Cat
- [ ] Investigate DS4
- [ ] Measure state recovery
- [ ] Investigate cross-runtime portability

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT
