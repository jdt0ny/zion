# Zion State v0.2

> Experimental specification for runtime-independent AI agent state.
> Supersedes `zion-state-v0.1.md`, which stays in the repository as the
> historical snapshot of the v0.1 schema.

## 1. What changed from v0.1

v0.2 is an **additive** schema change: every v0.1 document remains a valid
v0.2 document. The change replaces a flat memory record with structured
episodic memory, and types a dimension that was previously untyped.

| Dimension  | v0.1                          | v0.2                                        |
|------------|-------------------------------|---------------------------------------------|
| `memory`   | `MemoryEntry` (5 fields)      | episodic: `occurred_at`, `salience`, `context`, `links` |
| `knowledge`| `list[dict]` (untyped bag)    | `list[KnowledgeEntry]` (typed, extra fields kept) |
| `version`  | `"0.1"`                       | `"0.2"` for new states                      |

Non-changes, on purpose: the portability taxonomy, the JSON format, the
`schema` identifier, and every other dimension.

## 2. Motivation

A list of strings answers "what was said". It does not answer _when the
event happened_, _how much it mattered_, or _what it connects to_. Without
those, recall, conflict detection and consolidation have nothing to work
on. This is the boundary between a list of utterances and a subconscious.

## 3. Scope

- Structured episodic memory (`memory`) and declarative knowledge (`knowledge`).
- Round-trip fidelity of 1.0 over the new structure.
- Loading v0.1 documents without loss.

Out of scope for v0.2: schema migrations between versions (they arrive with
the identity milestone), write-during-execution tools, and any semantic
search over memory.

## 4. State model

```
ZionState
├── schema          # schema identifier
├── version         # schema version ("0.2" for new states)
├── identity        # agent identity
├── project         # project metadata
├── conversation    # message history
├── memory          # episodic memory entries (this document)
├── decisions       # decision log
├── tasks           # task tracking
├── tools           # tool definitions
├── knowledge       # declarative knowledge entries (this document)
├── configuration   # agent configuration
└── runtime         # runtime metadata
```

## 5. Memory model

`memory` is a list of `MemoryEntry`. An entry is one episode: something
that happened, remembered with a time and a weight.

| Field         | Type                         | Required | Meaning                                             |
|---------------|------------------------------|----------|-----------------------------------------------------|
| `id`          | string                       | yes      | Join key; the target of other entries' `links`      |
| `content`     | string                       | yes      | The remembered text                                 |
| `created_at`  | datetime                     | yes      | When the memory was written                         |
| `occurred_at` | datetime                     | yes      | When the event happened (backfilled, see §7)        |
| `salience`    | float 0.0–1.0                | no       | How much the memory matters; default `0.5`          |
| `context`     | string \| null               | no       | Situation in which the memory was formed            |
| `links`       | list of `MemoryLink`         | no       | Structural links to other memories; default `[]`    |
| `updated_at`  | datetime \| null             | no       | Last edit                                           |
| `portability` | `portable`/`reconstructable`/`runtime_bound` | no | Default `portable`             |

Constraints:

- `salience` outside `0.0–1.0` is rejected, not clamped.
- `occurred_at > created_at` is rejected: a memory cannot be written
  before the event it records.
- `context` is a string, not an object. An object would be the same
  untyped bag that `knowledge` used to be.

### 5.1 MemoryLink

| Field      | Type     | Meaning                                             |
|------------|----------|-----------------------------------------------------|
| `target`   | string   | `id` of the memory this link points to              |
| `relation` | enum     | `caused_by`, `follows`, `same_topic`, `contradicts` |

`target` may point to a memory that is not in the current document. That
is legal (partial export), and `inspect_state` reports the count as
`dangling_memory_links` so an export never claims completeness it does
not have.

## 6. Knowledge model

`knowledge` is a list of `KnowledgeEntry`: facts, not episodes.

| Field         | Type           | Required | Meaning                                |
|---------------|----------------|----------|----------------------------------------|
| `content`     | string         | yes      | The proposition                        |
| `id`          | string \| null | no       | Identifier when known                  |
| `source`      | string \| null | no       | Where the fact came from               |
| `confidence`  | float 0.0–1.0  | no       | How firmly the fact is held            |
| `created_at`  | datetime \| null | no     | When the fact was recorded             |
| `portability` | portability    | no       | Default `portable`                     |

Rules:

- `KnowledgeEntry` has **no** `occurred_at` and **no** `salience`: a fact
  is not bound to a moment and is not weighted like an episode. The test
  suite asserts their absence, not just their non-use.
- Unknown fields are **preserved**. v0.1 documents contain free-form
  knowledge dictionaries; dropping their keys would be a fidelity loss.

Memory vs knowledge: a memory is _"I decided X during the session of
29/09"_; a knowledge entry is _"decisions in this project are recorded in
DECISIONS.md"_. One is dated and weighted; the other is not.

## 7. Backward compatibility

- A v0.1 document validates as v0.2 without modification.
- Missing `occurred_at` is backfilled from `created_at` on load.
- Loading **never rewrites `version`**: a document written as `"0.1"`
  stays `"0.1"`. Version upgrades are the job of schema migrations, which
  do not exist yet (see §10).
- Round-trip fidelity of a loaded v0.1 document must be 1.0.

## 8. JSON representation

```json
{
  "schema": "zion-state",
  "version": "0.2",
  "identity": {},
  "project": {},
  "conversation": [],
  "memory": [
    {
      "id": "m1",
      "content": "Adopted uv for the build",
      "created_at": "2026-09-29T15:26:00",
      "occurred_at": "2026-09-29T14:34:00",
      "salience": 0.9,
      "context": "packaging session",
      "links": [{"target": "m0", "relation": "caused_by"}],
      "updated_at": null,
      "portability": "portable"
    }
  ],
  "decisions": [],
  "tasks": [],
  "tools": [],
  "knowledge": [{"content": "Zion targets Python 3.11+"}],
  "configuration": {},
  "runtime": {}
}
```

## 9. Serialization and fidelity

- `export_state(state, path)` / `import_state(path)` are unchanged.
- Round-trip over the new structure must report `overall_fidelity == 1.0`.
- Order inside `links` and `memory` is significant and preserved.
- The portability taxonomy of v0.1 §6 still applies without change.

## 10. Version history

| Version | Focus                                             | Status   |
|---------|---------------------------------------------------|----------|
| 0.1     | State definition, JSON round-trip                 | shipped  |
| 0.2     | Episodic memory, typed knowledge (this document)  | shipped  |
| 0.3     | Identity continuity metric, schema migrations     | planned  |
| 0.4     | Bridges to existing checkpoint/memory formats     | planned  |
| 1.0     | Stabilised specification                          | planned  |

Schema migrations (`migrate_schema(from, to)`) are deliberately **not**
part of v0.2: the change is additive, so no migration is needed yet.
They are required before the first non-additive change.

## 11. Known limitations

- `salience` has no writer: until live capture exists, every memory
  carries the default `0.5` unless a producer sets it explicitly.
- `links` are not validated for cycles, and a dangling `target` is
  reported but not repaired.
- Knowledge is typed but not counted in `portability_summary`; the
  summary covers memory, decisions, tasks and runtime as before.
- Adapters populate `occurred_at` with an epoch placeholder: neither
  Cheshire Cat nor DS4 exposes real event timestamps.
- Everything here is still exercised against stub runtimes, not live ones.

## 12. Open questions

- Does `salience` need a decay function, or is a static weight enough?
- Should `contradicts` links trigger conflict detection automatically?
- When two memories link to each other, is that a cycle bug or a fact?
- Is `context` free text enough, or does it need controlled vocabulary?

---

**Zion v0.2 is experimental and does not claim universal AI agent
portability.**
