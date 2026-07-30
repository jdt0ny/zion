# ZION EXPERIMENT #001 — Cheshire Cat State Discovery

## Objective

Understand exactly what constitutes the state of a Cheshire Cat AI agent, and
determine which parts can be represented by ZionState.

## Cheshire Cat Version

| Field              | Value                                         |
|--------------------|-----------------------------------------------|
| Repository         | https://github.com/cheshire-cat-ai/core       |
| Commit             | `1493ce3`                                     |
| Branch             | `main`                                        |
| Version            | `2.0.23`                                      |
| Date investigated  | 2026-07-30                                    |
| License            | GPL-3.0                                       |

## Architecture

```
                        CHESHIRE CAT v2.0.23
                               │
                 FastAPI Application (uvicorn)
                               │
                    RequestContextMiddleware
                     (per-request contextvars)
                               │
                    ┌──────────┴──────────┐
                    │                     │
             CheshireCat                 Routes
            (process singleton)      /status, /settings,
                    │                /agents, /plugins,
            ┌───────┴───────┐        /me, /docs
            │               │
        Registry        MadHatter
     (service DI)     (plugin manager)
            │               │
     ┌──────┴──────┐   ┌───┴────┐
     │             │   │        │
  Services     Plugins  Hooks  Tools  Endpoints
     │
  ┌──┴──────────────────────────────┐
  │ Agents  Directives  ModelProv  │
  │ Auths   CoreSettings           │
  └────────────────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
  Persistence        Runtime
     │                   │
  ┌──┴────────┐    ┌────┴────┐
  │ Piccolo   │    │ In-Mem  │
  │ (SQLite / │    │ Singletons│
  │  PG)      │    │ ContextVars│
  │           │    │ ModelCache│
  │ Tables:   │    └─────────┘
  │ - ccat_global_key_value  │
  │ - ccat_user_key_value    │
  │ - ccat_chats (scaffold)  │
  └────────────────┘
```

### Key Architectural Notes

- **No formal agent identity**: The `CheshireCat` class is a process singleton. No
  agent ID, name, or personality is persisted. The `Agent` service class has a
  `slug` but no persistent identity beyond that.
- **No built-in vector memory**: Version 2.0.23 does not include a vector store
  or embedding-based memory subsystem. Memory is limited to the key-value store.
- **Plugin-discoverable services**: The `MadHatter` plugin manager discovers
  plugins from the filesystem, and their `Service` subclasses are registered in
  the `Registry`. Plugins contribute hooks, endpoints, tools, and services.
- **Per-request context**: User authentication and request state live in
  `contextvars`, not in a database.
- **Agent instances are transient**: `Agent` has `singleton = False`. Each API
  call creates a fresh agent instance, runs the loop, and discards it.

---

## State Components

### 1. Identity

| Attribute        | Status    | Details                                                           |
|------------------|-----------|-------------------------------------------------------------------|
| agent_id         | NOT PRESENT | No agent ID concept exists.                                      |
| agent_name       | NOT PRESENT | No agent name is stored.                                         |
| personality      | NOT PRESENT | No personality definition.                                        |
| system_prompt    | DEFINED   | Hardcoded on `Agent.system_prompt` class attribute ("You are an Agent in the Cheshire Cat AI fleet..."). Overridable per Agent subclass. |
| directives       | DEFINED   | Declared as `Agent.directives` list. Resolved per-run via registry. |
| version          | NOT PRESENT | No version tracking for agents.                                   |

**Source**: `src/cat/services/agents/base.py` (lines 28-40)

**Zion classification**: MODEL GAP — Zion's `AgentIdentity` fields
(`agent_id`, `name`, `version`) do not map onto anything in Cheshire Cat.
Cheshire Cat has no identity abstraction at all.

---

### 2. Conversation

| Field            | Status    | Details                                                           |
|------------------|-----------|-------------------------------------------------------------------|
| Storage          | VERIFIED  | `ChatDB` (table `ccat_chats`) via scaffold chats plugin. JSON columns. |
| Message model    | VERIFIED  | `Message(role, content, tool_calls, tool_call_id, structuredContent)` in `cat/types/messages.py`. Roles: "user", "assistant", "tool". |
| Sessions         | NOT PRESENT | No formal session concept. Context is per-request.                |
| Users            | PRESENT   | `User(id, name, roles, custom)` in `cat/auth/user.py`. All chat data is user-scoped via `user_id`. |
| Persistent       | YES       | Saved via chats plugin CRUD endpoints.                           |
| Metadata         | PRESENT   | `ChatDB` has `name`, `updated_at`, `messages` (JSON), `context` (JSON). |
| Timestamps       | PRESENT   | `updated_at` auto-set via `Timestamptz` column.                  |
| Tool calls       | PRESENT   | `Message.tool_calls` list of `ToolCall(id, name, args)`.          |
| Reasoning        | NOT PRESENT | No explicit reasoning field.                                     |
| Attachments      | PRESENT   | `ContentBlock` includes `ImageContent`, `AudioContent`, `ResourceLink`, `EmbeddedResource`. |

**Source**:
- `src/cat/types/messages.py` — Message model
- `src/cat/scaffold/plugins/chats/db.py` — ChatDB table
- `src/cat/scaffold/plugins/chats/endpoints/crud.py` — CRUD API
- `src/cat/protocols/model_context/type_wrappers.py` — ContentBlock types

**Zion classification**: PORTABLE. Messages can be extracted as JSON arrays.

**Zion mapping gap**: Zion's `Message` model has `role`, `content`, `created_at`.
Cheshire Cat messages have `tool_calls`, `tool_call_id`, `structuredContent`, and
rich content blocks (images, audio, resources). Zion would need a richer message
model to represent Cheshire Cat conversations faithfully.

---

### 3. Memory

| Field              | Status          | Details                                                              |
|--------------------|-----------------|----------------------------------------------------------------------|
| Memory classes     | NOT PRESENT     | No memory classes exist. No vector memory, no episodic/semantic memory. |
| Global key-value   | VERIFIED        | `Store` class wraps `ccat_global_key_value` table. Keys: string, Values: JSON. Methods: save, load, delete, exists. |
| Per-user key-value | VERIFIED        | `UserStore` class wraps `ccat_user_key_value` table. Scoped by `user_id`. |
| Memory types       | NOT PRESENT     | No "working", "long-term", "short-term" distinction.                 |
| Embeddings         | NOT PRESENT     | No embedding storage in core.                                        |
| Vector store       | NOT PRESENT     | No vector database integration in core.                              |
| Retrieval          | NOT PRESENT     | No retrieval mechanism in core.                                      |

**Source**:
- `src/cat/db/helper.py` — Store and UserStore
- `src/cat/db/models.py` — KeyValueDB and UserKeyValueDB table definitions

**Zion classification**: PORTABLE. Key-value pairs are JSON-serializable.

**Important limitation**: Cheshire Cat v2.0.23 has NO semantic/episodic/vector
memory. Memory is purely arbitrary key-value data. Any memory-like behavior
must be provided by a plugin and is not part of the core state model.

---

### 4. Knowledge / Documents

| Field              | Status          | Details                                                              |
|--------------------|-----------------|----------------------------------------------------------------------|
| Document ingestion | NOT PRESENT     | No built-in document ingestion pipeline.                             |
| Document metadata  | NOT PRESENT     | No document metadata storage.                                        |
| Chunks             | NOT PRESENT     | No text chunking.                                                    |
| Embeddings         | NOT PRESENT     | No embedding pipeline.                                               |
| Vector collections | NOT PRESENT     | No vector collections.                                               |
| File storage       | PRESENT         | Uploads directory at `{DATA_PATH}/uploads/` (via scaffold `uploads` plugin). |

**Source**: Verified by absence — no document-related classes exist in core.

**Zion classification**: NOT PRESENT in core Cheshire Cat. Knowledge/Document
handling would be plugin-provided.

---

### 5. Tools

| Field              | Status          | Details                                                              |
|--------------------|-----------------|----------------------------------------------------------------------|
| Tool definition    | VERIFIED        | `Tool` class in `cat/mad_hatter/decorators/tool.py`. Fields: name, description, input_schema, output_schema, is_internal, meta, plugin_id. |
| Tool registration  | VERIFIED        | `@tool` decorator on Agent subclass methods. `instantiate_agent_tools()` picks them up via class MRO scan. |
| Tool parameters    | VERIFIED        | `input_schema: Dict` — JSON Schema for arguments. Generated from function signature via `ParsedFunction`. |
| Tool execution     | VERIFIED        | `Tool.execute(agent, tool_call)` — calls the bound function. Result wrapped in `Message(role="tool")`. |
| Plugin tools       | VERIFIED        | Module-level `@tool` detected and warned as unreachable. MCP tools added by directives. |
| Tool state         | NOT PRESENT     | Tools are stateless Python functions. No tool state is persisted.    |
| Tool configuration | VERIFIED        | MCP tool servers have `Settings` with server URLs and auth tokens.   |

**Source**:
- `src/cat/mad_hatter/decorators/tool.py` — Tool class and @tool decorator
- `src/cat/services/agents/base.py` — Agent.list_tools(), Agent.call_tool()
- `src/cat/scaffold/plugins/mcp_client/config.py` — MCP server settings

**Zion classification**:
- Tool *definition* (name, description, input_schema): **PORTABLE**
- Tool *implementation* (Python function body): **RUNTIME_BOUND** — the actual
  code cannot be meaningfully transferred to a different runtime without
  reimplementation.
- Tool *configuration* (MCP server URLs, auth): **PORTABLE** (extractable as JSON)
- Tool *execution state*: **RUNTIME_BOUND** (in-flight tool calls)

---

### 6. Plugins

| Field              | Status          | Details                                                              |
|--------------------|-----------------|----------------------------------------------------------------------|
| Plugin code        | VERIFIED        | Python files in `{PLUGINS_PATH}/{plugin_id}/`. Imported and executed. |
| Plugin manifest    | VERIFIED        | `plugin.json` → `PluginManifest(name, version, thumb, tags, description, author_name, author_url, plugin_url, min_cat_version, max_cat_version)`. |
| Plugin config      | VERIFIED        | Service `Settings` nested Pydantic models, persisted in global key-value store. |
| Plugin deps        | VERIFIED        | `requirements.txt` installed via `uv pip install` at activation.     |
| Plugin state       | NOT PRESENT     | No persistent runtime state for plugins.                             |
| Plugin activation  | VERIFIED        | `active_plugins` list in global key-value store tracks which plugins are on. |
| Plugin install     | VERIFIED        | From URL (registry or zip) via `PluginExtractor`.                    |

**Source**:
- `src/cat/mad_hatter/plugin.py` — Plugin class
- `src/cat/mad_hatter/plugin_manifest.py` — PluginManifest
- `src/cat/mad_hatter/plugin_extractor.py` — PluginExtractor
- `src/cat/mad_hatter/mad_hatter.py` — MadHatter (toggle, install, uninstall)

**Zion classification**:
- Plugin *code*: **RECONSTRUCTABLE** — Python source code could be copied, but
  the runtime must be Python-compatible to execute it. The code structure is
  transferable, but execution semantics are Python-specific.
- Plugin *manifest*: **PORTABLE** — JSON metadata.
- Plugin *configuration*: **PORTABLE** — JSON settings blobs.
- Plugin *dependencies*: **RECONSTRUCTABLE** — `requirements.txt` can be
  reinstalled in a compatible environment.
- Plugin *activation state*: **PORTABLE** — list of active plugin IDs.

---

### 7. Configuration

| Field                  | Status          | Details                                                              |
|------------------------|-----------------|----------------------------------------------------------------------|
| Python defaults        | VERIFIED        | `cat/config/defaults.py` — 15 UPPERCASE constants.                  |
| User overrides         | VERIFIED        | `config.py` in project folder — plain Python, imported dynamically. |
| DB-backed settings     | VERIFIED        | Service settings stored as JSON blobs in `ccat_global_key_value`. Key format: `settings_{plugin_id}_{type}_{slug}`. |
| Environment variables  | NOT PRESENT     | No direct `.env` loading in core. Users can read env in their `config.py`. |
| LLM provider config    | VERIFIED        | `CoreSettings.default_llm`, `CoreSettings.default_embedder`. Provider-specific settings (e.g., `OpenAICompatibleProvider.Settings` with `base_url` and `api_key`). |
| Model settings          | VERIFIED        | Model discovery via `list_llms()` / `list_embedders()` on each provider. Cached on singleton. |

**Source**:
- `src/cat/config/__init__.py` — Config class
- `src/cat/config/defaults.py` — Default values
- `src/cat/services/core_settings.py` — CoreSettings service
- `src/cat/services/service.py` — Service settings base

**Zion classification**:
- Portable configuration (service settings JSON): **PORTABLE**
- Python config.py: **PORTABLE** (Python file, can be copied)
- Secrets (API_KEY, JWT_SECRET, API keys): **RUNTIME_BOUND** — must never enter
  Zion state.
- DB connection string: **RUNTIME_BOUND** — environment-specific.
- LLM/embedder model slugs: **PORTABLE** (logical identifiers, not runtime-bound).

---

### 8. Runtime State

| Field                    | Status          | Details                                                              |
|--------------------------|-----------------|----------------------------------------------------------------------|
| CheshireCat singleton    | VERIFIED        | `_ccat` module global in `cat/ambient/runtime.py`. One per process. |
| Service singletons       | VERIFIED        | Cached on class via `ServiceMeta`. Lazy-constructed.                |
| Registry class map       | VERIFIED        | `Registry.classes` dict — type → slug → class. Rebuilt on plugin changes. |
| MadHatter caches         | VERIFIED        | `hooks`, `endpoints`, `service_classes` dicts. Rebuilt on refresh.  |
| ContextVars              | VERIFIED        | Per-request: `Ctx(user, request, stream)`. Per-plugin: `plugin_id`. |
| Model provider caches    | VERIFIED        | `_models` list on `OpenAICompatibleProvider`. Caches model list per provider. |
| OpenAPI schema           | VERIFIED        | Cached, reset on endpoint changes.                                  |
| Active agent run state   | VERIFIED        | `Agent.task`, `Agent.result`, `Agent.tools`, `Agent.directives` — per-run instance fields. Discarded after run. |

**Source**:
- `src/cat/ambient/runtime.py` — ccat() singleton accessor
- `src/cat/ambient/context_vars.py` — Ctx and contextvars management
- `src/cat/services/factory.py` — Registry
- `src/cat/mad_hatter/mad_hatter.py` — MadHatter caches

**Zion classification**: RUNTIME_BOUND. All of these are in-memory and
process-specific. None can be meaningfully serialized.

---

## Persistence Layer Summary

| Storage             | Technology   | Location                              | Data                                 |
|---------------------|-------------|---------------------------------------|--------------------------------------|
| Global key-value    | Piccolo ORM | `ccat_global_key_value` table         | Active plugins, service settings, installation info |
| User key-value      | Piccolo ORM | `ccat_user_key_value` table           | Per-user plugin data                 |
| Chat history        | Piccolo ORM | `ccat_chats` table                    | Messages JSON, context JSON          |
| Plugin code         | Filesystem  | `{PROJECT_PATH}/plugins/{id}/`        | Python source, plugin.json, requirements.txt |
| Uploads             | Filesystem  | `{DATA_PATH}/uploads/`               | Uploaded files                       |
| Configuration       | Python file | `{PROJECT_PATH}/config.py`           | UPPERCASE constants overrides        |

Default database path: `{PROJECT_PATH}/data/core/core.db` (SQLite).

---

## Extraction Feasibility

| Component           | Extractable | Method                                                              | Loss                                                              |
|---------------------|-------------|----------------------------------------------------------------------|-------------------------------------------------------------------|
| Key-value store     | YES         | Query all rows from `ccat_global_key_value` and `ccat_user_key_value` tables | None (JSON data)                     |
| Conversations       | YES         | Query all rows from `ccat_chats` table                               | None (JSON data)                     |
| Plugin manifest     | YES         | Read `plugin.json` from each plugin directory                        | None                                 |
| Plugin code         | YES         | Copy plugin directory                                                | Python-specific, needs compatible runtime |
| Plugin settings     | YES         | Load from key-value store by key pattern `settings_{pid}_{type}_{slug}` | None (JSON data)                     |
| Active plugins list | YES         | Load `active_plugins` key from global store                          | None                                 |
| Config defaults     | YES         | Read `cat/config/defaults.py`                                       | None                                 |
| User config         | YES         | Read `config.py` file                                                | Document secrets must be filtered    |
| Service settings    | YES         | Enumeration via `GET /settings` API or direct DB query               | Provider-specific secrets lost intentionally |
| Vector/embedding    | N/A         | Not present in core                                                  | N/A                                  |

---

## Portability Classification

| State                  | Exists | Persistent | Extractable | Portable | Reconstructable | Runtime-bound | Evidence                                       |
|------------------------|--------|------------|-------------|----------|-----------------|---------------|------------------------------------------------|
| Identity               | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No identity model exists in any source file    |
| Conversation/messages  | YES    | YES        | YES         | YES      | —               | —             | `ChatDB` JSON column, `Message` Pydantic model |
| Key-value memory       | YES    | YES        | YES         | YES      | —               | —             | `Store`/`UserStore` in `cat/db/helper.py`      |
| Vector/embedding mem   | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | Not present in core codebase                   |
| Knowledge/documents    | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | Not present in core codebase                   |
| Tool definitions       | YES    | PARTIAL    | PARTIAL     | YES      | YES             | —             | `Tool` class — name/schema portable, body is not |
| Tool implementation    | YES    | NO         | PARTIAL     | —        | —               | YES           | Python function body, runtime-specific         |
| Tool configuration     | YES    | YES        | YES         | YES      | —               | —             | MCP server settings in global store            |
| Plugin code            | YES    | YES        | YES         | —        | YES             | —             | Python source files on filesystem              |
| Plugin manifest        | YES    | YES        | YES         | YES      | —               | —             | `plugin.json` (JSON metadata)                  |
| Plugin configuration   | YES    | YES        | YES         | YES      | —               | —             | Service settings JSON blob in key-value store  |
| Plugin activation      | YES    | YES        | YES         | YES      | —               | —             | `active_plugins` list in global store           |
| Python config          | YES    | YES        | YES         | YES      | —               | —             | `config.py` file                               |
| DB-backed settings     | YES    | YES        | YES         | YES      | —               | —             | Service settings in key-value store            |
| Secrets (API_KEY etc)  | YES    | YES        | YES         | NO       | —               | —             | Must NOT be exported                           |
| CheshireCat singleton  | YES    | NO         | NO          | —        | —               | YES           | `_ccat` module global, in-memory only          |
| Service singletons     | YES    | NO         | NO          | —        | —               | YES           | Cached on class via `ServiceMeta`              |
| MadHatter caches       | YES    | NO         | PARTIAL     | —        | YES             | —             | Rebuildable from active plugins                |
| ContextVars            | YES    | NO         | NO          | —        | —               | YES           | Per-request, per-plugin context variables      |
| Model provider caches  | YES    | NO         | NO          | —        | —               | YES           | In-memory list of models per provider          |
| Agent run state        | YES    | NO         | NO          | —        | —               | YES           | Per-call instance, discarded after run         |

---

## Zion Mapping

| Cheshire Cat State        | Zion State         | Transformation                                    | Information Lost                                      | Portability    |
|---------------------------|--------------------|---------------------------------------------------|------------------------------------------------------|----------------|
| No identity exists        | `AgentIdentity`    | Must be constructed/supplied by user              | Nothing lost (no identity to lose)                   | reconstructable |
| `ChatDB.messages` (JSON)  | `conversation`     | Map `Message` fields → Zion `Message` fields      | Tool calls, content blocks, structuredContent, IDs   | portable       |
| `ccat_global_key_value`   | `memory`           | Each key-value pair → one `MemoryEntry`           | Key structure, per-user scoping, JSON type precision | portable       |
| `ccat_user_key_value`     | `memory`           | Each key-value pair → one `MemoryEntry`           | User ID association                                   | portable       |
| No knowledge exists       | `knowledge`        | N/A — field remains empty                         | N/A                                                   | N/A            |
| `Tool(name, input_schema)`| `tools[]` dict     | Serialize tool metadata to dict                   | Function body, execution context, MCP bindings       | reconstructable |
| Plugin settings (JSON)    | `configuration`    | Merge all service settings into `configuration`   | Per-plugin scoping                                    | portable       |
| `config.py` constants     | `configuration`    | Merge UPPERCASE constants into dict               | Python code structure (important: only values)        | portable       |
| Active plugins list       | `configuration`    | Store as `active_plugins` key                     | None                                                  | portable       |
| N/A (no decisions in CC)  | `decisions`        | Requires explicit extraction                      | Nothing — CC doesn't have decisions                  | N/A            |
| N/A (no tasks in CC)      | `tasks`            | Requires explicit extraction                      | Nothing — CC doesn't have tasks                      | N/A            |
| Runtime state (all forms) | `RuntimeState`     | Mark as `runtime_bound`                           | All runtime data intentionally excluded               | runtime_bound  |

---

## Model Gaps

### Gap 1: AgentIdentity is not present in Cheshire Cat

Cheshire Cat v2.0.23 has **no concept of agent identity**. The `Agent` class is
a runtime abstraction with a `slug` (Python string identifier) and a hardcoded
`system_prompt`. There is no:

- Agent ID
- Agent name
- Agent version
- Personality definition
- Persistent agent configuration

Zion's `AgentIdentity` (with `agent_id`, `name`, `version`) cannot be extracted
from Cheshire Cat — it would need to be synthesised.

**What should change in Zion**: Nothing yet. The adapter can populate
`AgentIdentity` with synthesised values (e.g., `agent_id="cheshire-cat"`,
`name="Cheshire Cat Agent"`, `version="2.0.23"`).

### Gap 2: Message model is insufficient

Zion's `Message` has:
- `role` ("system", "user", "assistant", "tool")
- `content` (plain string)
- `created_at`

Cheshire Cat's `Message` has:
- `role` ("user", "assistant", "tool") — **no "system" role**
- `content` (List[ContentBlock]) — **not a string**
- `tool_calls` (List[ToolCall]) — **not represented in Zion**
- `tool_call_id` (Optional[str]) — **not represented in Zion**
- `structuredContent` (Optional[dict]) — **not represented in Zion**
- No `created_at` field

**What should change in Zion**: Zion's `Message` model should be extended to
support:
- Structured content (not just plain text)
- Tool call representations
- Tool call ID referencing
- Removal of the "system" role (or keeping it but noting it is CC-specific)
- Optional `created_at` field

### Gap 3: Memory model is too structured

Zion's `MemoryEntry` (with `id`, `content`, `created_at`, `updated_at`,
`portability`) is more structured than Cheshire Cat's key-value store. Cheshire
Cat stores arbitrary JSON blobs under string keys — no timestamp, no content
field.

**What should change in Zion**: The adapter can map key-value pairs to
`MemoryEntry` objects, but the mapping loses the arbitrary JSON structure.
Zion may need a flexible `dict[str, Any]` field or a separate key-value
representation.

### Gap 4: No vector/embedding memory

Cheshire Cat 2.0.23 has **no vector memory** built in. Zion's `memory` field
(a list of `MemoryEntry`) is sufficient for what exists, but any future vector
memory plugin would require an extended model.

### Gap 5: Knowledge/documents not present

Cheshire Cat has no document ingestion pipeline. Zion's `knowledge` field
remains empty. No gap exists yet.

### Gap 6: Decisions and Tasks not present

Cheshire Cat has no decision logging or task tracking. Zion's `decisions` and
`tasks` fields remain empty. No gap exists yet.

---

## Security Concerns

The following data must NEVER be exported into Zion state:

| Secret                  | Source                         | Risk                                      |
|-------------------------|--------------------------------|-------------------------------------------|
| `API_KEY`               | `cat/config/defaults.py`       | Master API key grants full access         |
| `JWT_SECRET`            | `cat/config/defaults.py`       | JWT signing secret — token forgery        |
| LLM provider API keys   | Service settings in DB         | Access to external LLM APIs               |
| MCP server tokens       | MCP plugin settings            | Access to MCP server resources            |
| Database connection URL | `config.SQL`                   | Full database access                      |
| User JWT tokens         | In-memory (per request)        | Session hijacking                         |
| OAuth tokens            | Plugin data                    | Third-party account access                |

**Recommendation**: Any extraction adapter must:
1. Read settings blobs from the key-value store.
2. Strip any field named `api_key`, `token`, `secret`, `password` before
   including settings in Zion state.
3. Never export `API_KEY` or `JWT_SECRET` from config.
4. Never export the raw database connection string.

---

## Open Questions

1. **Plugin portability**: Is a Python plugin meaningfully portable to a
   non-Python runtime? Zion's portability model assumes "yes, with
   reconstruction", but the runtime requirement is absolute.

2. **Settings schema**: Service settings schemas are dynamic (`settings_schema()`
   override). Can a static Zion state represent settings for plugins whose
   schemas change between versions?

3. **User data scoping**: Cheshire Cat's per-user key-value store scopes data by
   `user_id`. Should Zion state include user-scoped partitions, or flatten
   everything?

4. **Active plugin state**: Plugins maintain in-memory state (e.g., model caches,
   open HTTP clients). Should Zion attempt to capture any of this, or leave it
   as entirely reconstructable?

5. **MCP tools**: MCP tool definitions are discovered at runtime from MCP
   servers. They are stateless per-call, but the server configuration (URL, auth)
   is state. Is server config "tool state" or "infrastructure config"?

6. **Embedder integration**: The `embedder()` verb exists in the ambient API
   but has no storage backend in core. Is embedding just a side-effect, or part
   of agent state?

7. **Conversation-continuity token**: Chat history alone may be insufficient to
   resume a conversation — LLM context windows, token budgets, and system prompt
   state are runtime-specific. How much of "conversation state" is truly portable?

---

## Conclusion

> **How much of a Cheshire Cat agent appears transferable into a runtime-independent Zion state?**

**What is portable**:
- Conversation history (JSON messages)
- Key-value store data (global and per-user)
- Plugin manifest metadata (JSON)
- Plugin configuration settings (JSON)
- Configuration values (excluding secrets)
- Active plugin list
- Tool definitions (name + JSON schema — not the implementation)

**What is reconstructable**:
- Agent identity (must be synthesized — does not exist in CC)
- Plugin code (Python source — requires compatible runtime)
- Plugin dependencies (requirements.txt — requires compatible environment)
- Tool implementations (need to be reimplemented per runtime)
- MadHatter caches (can be rebuilt from plugin files)

**What is runtime-bound**:
- All in-memory singletons (CheshireCat, services, caches)
- Per-request context (user, auth, stream)
- Active agent execution state (task, result, directives state)
- Model provider connections and cached model lists
- Python function bodies of tools and hooks
- LLM context window state
- JWT tokens and authentication state
- Database connection

**Overall assessment**: Most persistent data in Cheshire Cat v2.0.23 is already
JSON-serializable and stored in a database. The core challenge is not data
extraction — it is **semantic reconstruction** in a different runtime. Plugin
code, tool implementations, and hook functions are Python-specific and cannot
be moved to a non-Python runtime without reimplementation.

The Zion model is a reasonable starting point but has significant structural
gaps in message representation (structured content, tool calls) and memory
representation (flexible key-value vs structured entries).
