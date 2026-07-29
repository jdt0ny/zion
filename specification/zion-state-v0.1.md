# Zion State v0.1

> Experimental specification for runtime-independent AI agent state.

## 1. Motivation

AI agents today are tightly coupled to their runtime environment. When an agent
is moved between systems — or when the runtime itself changes — the agent loses
its identity, memory, decisions, and task state. Zion investigates whether a
sufficiently expressive state model can capture what makes an agent useful
_independently_ of the runtime executing it.

## 2. Research question

> Can an AI agent leave its runtime without losing the essential state that
> makes it useful?

## 3. Scope

Zion v0.1 focuses on:

- Defining a portable state model for AI agents.
- JSON serialization and deserialization.
- Round-trip fidelity for portable state.
- Establishing adapter boundaries for Cheshire Cat AI and DS4.
- Explicit classification of state into portability categories.

## 4. Non-goals

- Building a chatbot, LLM framework, agent framework, or memory product.
- Cross-runtime migration (v0.1 is single-runtime discovery only).
- Cloud infrastructure, databases, authentication, or GUIs.
- Support for any runtime beyond Cheshire Cat and DS4 (for now).
- Real-time or live agent interaction.

## 5. State model

```
ZionState
├── schema          # schema identifier
├── version         # schema version
├── identity        # agent identity
├── project         # project metadata
├── conversation    # message history
├── memory          # memory entries
├── decisions       # decision log
├── tasks           # task tracking
├── tools           # tool definitions
├── knowledge       # knowledge entries
├── configuration   # agent configuration
└── runtime         # runtime metadata
```

## 6. Portability classifications

Every state element carries a portability classification:

| Classification    | Meaning                                                       |
|-------------------|---------------------------------------------------------------|
| `portable`        | Can be serialized and transferred independently of runtime.   |
| `reconstructable` | Another runtime can recreate it, but may not copy directly.   |
| `runtime_bound`   | Depends on inference engine, model, process, or runtime.      |

Never mark runtime-specific information as portable without evidence.

## 7. JSON representation

JSON is the canonical serialization format. It must be:

- Human-readable.
- Deterministic where practical.
- Independent of Python-specific serialization.
- Suitable for Git versioning.

```json
{
  "schema": "zion-state",
  "version": "0.1",
  "identity": {},
  "project": {},
  "conversation": [],
  "memory": [],
  "decisions": [],
  "tasks": [],
  "tools": [],
  "knowledge": [],
  "configuration": {},
  "runtime": {}
}
```

## 8. Serialization

- `export_state(state, path)` writes JSON to disk.
- `import_state(path)` reads JSON and reconstructs `ZionState`.
- Round-trips must preserve all portable data without loss.

## 9. Runtime-bound state

Runtime-bound state must never be silently classified as portable. The
distinction is fundamental. Examples:

- DS4 KV cache → `runtime_bound`
- Active inference state → `runtime_bound`
- Running process state → `runtime_bound`

## 10. Adapter architecture

```
                    ZION CORE
                       │
             ┌─────────┴─────────┐
             │                   │
        ZionState            State Tools
             │                   │
             └─────────┬─────────┘
                       │
              Runtime Adapters
                 /           \
                /             \
      Cheshire Cat             DS4
```

Core Zion must not depend on any runtime library.

## 11. Cheshire Cat research

**Status:** UNKNOWN — requires runtime inspection.

| Dimension      | Status    | Notes                         |
|----------------|-----------|-------------------------------|
| identity       | UNKNOWN   | Requires runtime inspection   |
| conversation   | UNKNOWN   | Requires runtime inspection   |
| memory         | UNKNOWN   | Requires runtime inspection   |
| decisions      | UNKNOWN   | Requires runtime inspection   |
| tasks          | UNKNOWN   | Requires runtime inspection   |
| tools          | UNKNOWN   | Requires runtime inspection   |
| knowledge      | UNKNOWN   | Requires runtime inspection   |
| configuration  | UNKNOWN   | Requires runtime inspection   |
| runtime        | UNKNOWN   | Requires runtime inspection   |

## 12. DS4 research

**Status:** UNKNOWN — requires runtime inspection.

| Dimension      | Status    | Notes                         |
|----------------|-----------|-------------------------------|
| session        | UNKNOWN   | Requires runtime inspection   |
| conversation   | UNKNOWN   | Requires runtime inspection   |
| model          | UNKNOWN   | Requires runtime inspection   |
| tool metadata  | UNKNOWN   | Requires runtime inspection   |
| KV/session     | UNKNOWN   | Requires runtime inspection   |
| runtime        | UNKNOWN   | Requires runtime inspection   |

## 13. Known limitations

- No cross-runtime migration implemented.
- No live runtime integration verified.
- Adapters are research boundaries, not production connectors.
- Real-time state synchronization is out of scope.
- DSL or query language for state inspection is not yet explored.

## 14. Open questions

- How does ZionState map to runtime-specific memory formats?
- Can decisions from one runtime be meaningfully interpreted by another?
- What constitutes "identity" when an agent moves between runtimes?
- Is there a minimal viable set of state that makes an agent useful?
- How do we handle state conflicts during migration?

## 15. Future versions

| Version | Focus                                |
|---------|--------------------------------------|
| 0.1     | State definition, JSON round-trip    |
| 0.2     | Cheshire Cat integration             |
| 0.3     | DS4 integration                      |
| 0.4     | Cross-runtime migration experiment   |
| 0.5     | State reconciliation and conflict    |
| 1.0     | Stabilised specification             |

---

**Zion v0.1 is experimental and does not claim universal AI agent portability.**
