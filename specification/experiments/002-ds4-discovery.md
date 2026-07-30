# ZION EXPERIMENT #002 — DS4 Runtime & Local Orchestration Discovery

## Objective

Determine what DS4 (DwarfStar4) by Salvatore Sanfilippo is, how it operates,
and whether it could serve as a local orchestration/execution layer for a Zion
portable agent state.

## DS4 Version

| Field              | Value                                         |
|--------------------|-----------------------------------------------|
| Repository         | https://github.com/antirez/ds4                |
| Commit             | `54b36ed`                                     |
| Branch             | `main`                                        |
| Version            | Rolling (no tagged release)                   |
| Date investigated  | 2026-07-30                                    |
| License            | MIT (with GGML retained notices)              |
| Author             | Salvatore Sanfilippo (antirez)                |

## Architecture

```
                        DS4 (DwarfStar4)
                               │
                    ┌──────────┴──────────┐
                    │                     │
               ds4.c engine          ds4_agent.c
          (~65K lines C)          (~11K lines C)
                    │                     │
         ┌──────────┴──────────┐     Hardcoded tools:
         │                     │     read, write, edit
    ds4_server.c          ds4_cli.c     search, bash,
    (~17.5K lines)        (~2.2K lines) google_search,
         │                     │     visit_page
         │                ┌────┘
  OpenAI/Anthropic       │
  compatible HTTP API    │ Interactive REPL
         │               │
         └───────┬───────┘
                 │
          ds4_session
      (mutable inference timeline)
                 │
        ┌────────┴────────┐
        │                 │
   ds4_kvstore        GPU Graph
   (disk KV cache)   (Metal/CUDA/ROCm)
        │                 │
   ~/.ds4/kvcache/    GGUF model
   .kv files          (ds4flash.gguf)
```

### Key files

| File               | Purpose                                                     |
|--------------------|-------------------------------------------------------------|
| `ds4.c`            | Core inference engine: GGUF loading, tokenizer, CPU ref, Metal/CUDA/ROCm graph scheduling, session create/sync/eval/save/load, chat prompt construction |
| `ds4.h`            | Public API header: engine open/close, session lifecycle, chat API, sample/argmax, payload save/load |
| `ds4_server.c`     | HTTP server: worker queue, OpenAI/Anthropic endpoints, tool-call mapping (DSML ↔ JSON), disk KV cache policy, SSE streaming, batched sessions |
| `ds4_agent.c`      | Native coding agent: terminal UI, two-thread architecture (UI + worker), tool execution, session persistence, context compaction, web subsystem |
| `ds4_cli.c`        | CLI and interactive REPL with linenoise                      |
| `ds4_kvstore.c`    | Disk KV store: SHA1-prefix-addressed checkpoint files, eviction policy (LRU with decaying hits), tool-id map persistence |
| `ds4_kvstore.h`    | KV store public API: open/close, store, try_load, evict       |
| `ds4_web.c`        | Web subsystem: Chrome CDP integration for google_search and visit_page tools |
| `ds4_metal.m`      | Objective-C Metal runtime and kernel wrappers                 |

## Central Abstraction

| Aspect       | Finding                                                     |
|--------------|-------------------------------------------------------------|
| Abstraction  | `ds4_session` — a mutable inference timeline                |
| Source       | `ds4.h:328-463`, `ds4.c:~56773-59928`                      |
| Purpose      | Owns the live KV cache, logits, and checkpoint token sequence for one conversation. Created per inference context, used for sync, eval, argmax, save/load. |
| Persistent   | Partially — session state can be saved/loaded to disk via `ds4_session_save_payload()` / `ds4_session_load_payload()`. KV store wraps this with SHA1-addressed files. |
| Runtime-bound| YES — the session owns GPU graph state, Metal buffers, CUDA allocations, and in-memory token vectors. The saved payload is a graph-specific binary format tied to the exact DS4 engine version and model layout. |

The `ds4_session` is NOT an "agent session" — it is a **token inference timeline**.
It tracks the token prefix, the live KV cache, and the next-token logits. It is
meaningless outside the DS4 inference engine.

## Local Orchestration

DS4 does NOT orchestrate local work in any general sense.

| Capability               | Status         | Evidence                                                        |
|--------------------------|----------------|-----------------------------------------------------------------|
| Process creation         | LIMITED        | `ds4_agent.c` can start `bash` subprocesses via the `bash` tool. `agent_execute_tool_call()` in `ds4_agent.c:~7910` reads/writes files, runs bash commands. |
| Subprocess execution     | LIMITED        | Only the `bash` tool in `ds4_agent.c` — starts a background shell job, monitors via `bash_status`/`bash_stop`. |
| Shell commands           | YES (agent)    | `bash` tool executes shell commands. Only in the native agent, not in the server. |
| Filesystem operations    | YES (agent)    | Built-in tools: `read`, `write`, `edit`, `list`, `search`. Agent only. |
| Tool execution           | YES (hardcoded)| Eight hardcoded tools in `ds4_agent.c`. Server handles DSML tool calls via API, but does not execute local tools. |
| Concurrency              | THREADED       | `ds4_server.c`: multiple client threads + worker thread(s) + decode coordinator. `ds4_agent.c`: two threads (UI + worker). Mutex-based synchronization. |
| Background tasks         | LIMITED        | Agent bash tool runs commands in background. No general background task system. |
| Workers/queues           | YES (server)   | Job queue in `ds4_server.c` — a linked list of jobs protected by mutex, processed by a single worker thread. |
| Event loops              | NO             | No event loop. Blocking threaded model.                         |
| Lifecycle management     | NO             | No lifecycle management for processes or services.              |
| Process termination      | LIMITED        | Agent `bash_stop` tool sends SIGTERM to a bash job.              |
| Restart/recovery         | NO             | No process restart or recovery mechanism.                       |
| Timeouts                 | NO             | No timeout mechanism for tool execution.                        |
| Error handling           | MINIMAL        | Tool errors returned as text to the model.                      |
| Isolation                | NO             | No sandboxing, no containers, no permission model.              |
| Environment variables    | NO             | No environment variable management.                             |
| Working directories      | NO             | No working directory management.                                |

**Conclusion**: DS4 is NOT a local orchestrator. It is an inference engine with
a built-in coding agent that can execute a small set of hardcoded local tools.
There is no general orchestration framework, no plugin system for tools, no
workflow engine, no process lifecycle management.

## LLM Integration

| Capability               | Status         | Evidence                                                        |
|--------------------------|----------------|-----------------------------------------------------------------|
| Supported models         | DeepSeek V4 Flash/PRO, GLM 5.2 | README and model download system. |
| Local inference          | YES            | Native Metal (Apple Silicon), CUDA (NVIDIA), ROCm (AMD Strix Halo) backends. |
| Remote/cloud models      | NO             | No cloud provider support. Pure local inference.                |
| API abstraction          | OpenAI + Anthropic compatible | `POST /v1/chat/completions`, `POST /v1/responses`, `POST /v1/messages`, `POST /v1/completions`. |
| Model configuration      | CLI flags      | `--model`, `--ctx`, `--temp`, `--top-p`, `--top-k`, `--min-p`, `--seed`, thinking modes. |
| Prompt construction      | Built-in       | `ds4_chat_begin()`, `ds4_chat_append_message()`, `ds4_chat_append_assistant_prefix()` — handles BOS, roles, think tokens, DSML tool syntax. |
| Conversation history     | Server API     | Messages array in API requests. Agent keeps transcript in memory + disk KV cache. |
| Tool calling             | Native DSML    | Model emits DSML-formatted tool calls. Server maps to/from OpenAI/Anthropic JSON. Agent processes natively. |
| Streaming                | YES            | SSE streaming for all API endpoints. Tool name + arguments streamed as deltas. |
| Retries                  | NO             | No built-in retry mechanism.                                    |
| Model state              | Runtime-bound  | `ds4_engine` holds ~81GB+ of quantized weights mapped from GGUF. GPU buffers, Metal graphs, CUDA streams — all runtime-bound. |

**LLM integration conclusion**: DS4 is itself an LLM provider. It does not
integrate with external providers. It serves its own local inference through
OpenAI/Anthropic-compatible endpoints.

## Ollama Compatibility

| Aspect                    | Status         | Evidence                                                        |
|---------------------------|----------------|-----------------------------------------------------------------|
| Direct Ollama support     | NOT PRESENT    | No Ollama integration in source code.                           |
| OpenAI-compatible API     | YES            | `POST /v1/chat/completions` — standard OpenAI format.           |
| HTTP model provider       | YES            | Server on port 8000, configurable via `--host` and `--port`.     |
| Configurable base URLs    | YES            | Not applicable (DS4 is server, not client).                     |
| Model names               | YES            | Exposes model from loaded GGUF via `GET /v1/models`.            |
| Streaming                 | YES            | SSE streaming for all endpoints.                                |
| Tool calling              | YES            | DSML ↔ OpenAI/Anthropic JSON tool call mapping.                 |
| Structured output         | NO             | Not supported.                                                  |
| Embeddings                | NO             | No embedding endpoint. The `embedder()` verb does not exist in DS4. |
| Local inference assumptions| YES           | Entirely local inference, no cloud dependency.                  |

**Ollama compatibility conclusion**: DS4 does NOT integrate with Ollama. DS4 IS
its own local inference engine — it is a direct competitor/replacement for
Ollama when running DeepSeek V4 Flash. The server exposes an
OpenAI-compatible API that any OpenAI SDK client can use, which is functionally
similar to what Ollama provides, but the model support is limited to DeepSeek
V4 Flash/PRO and GLM 5.2.

If Zion needs a local LLM, DS4 can serve as the inference backend exactly as
Ollama would — by running `ds4-server` and connecting via the
OpenAI-compatible API.

## State Investigation

| State               | Exists | Persistent | Extractable | Portable | Reconstructable | Runtime-bound | Evidence |
|---------------------|--------|------------|-------------|----------|-----------------|---------------|----------|
| Identity            | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No agent identity in DS4. The engine has no identity concept. |
| Conversation        | YES    | PARTIAL    | PARTIAL     | YES      | —               | —             | Messages in API request body. Agent transcript in memory + disk KV store. |
| Memory              | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No vector memory, no key-value memory, no semantic/episodic memory. |
| Context / KV state  | YES    | YES        | PARTIAL     | —        | —               | YES           | `ds4_kvstore` — disk KV cache is a binary payload tied to DS4 engine version and model layout. |
| Tasks               | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No task system.                                                |
| Tools (definitions) | YES    | NO         | YES         | YES      | —               | —             | Tool names and schemas are hardcoded in `ds4_agent.c`. Server tools are API-provided. |
| Tools (impl)        | YES    | NO         | NO          | —        | —               | YES           | Python/C code in `ds4_agent.c` — hardcoded, not pluggable.     |
| Tool results        | YES    | NO         | YES         | YES      | —               | —             | Tool results appear as messages in the transcript.            |
| Configuration       | YES    | YES        | YES         | YES      | —               | —             | CLI flags, no config file. Server settings via CLI flags.      |
| Environment         | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No environment variable management.                            |
| Processes           | YES    | NO         | NO          | —        | —               | YES           | The agent's `bash` tool creates subprocesses. No persistence. |
| Model config        | YES    | PARTIAL    | YES         | YES      | —               | —             | CLI flags like `--temp`, `--ctx`, `--top-p`. Not saved.       |
| Model runtime       | YES    | NO         | NO          | —        | —               | YES           | `ds4_engine` holds 81GB+ of model weights in GPU memory.      |
| Sessions            | YES    | PARTIAL    | PARTIAL     | —        | —               | YES           | `ds4_session` is runtime-bound. Disk KV cache provides limited resumption. |
| Credentials         | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No credential storage. API key is dummy "dsv4-local".         |
| Logs                | YES    | YES        | YES         | YES      | —               | —             | Server `--trace` writes detailed traces. Agent logs to terminal. |
| Caches              | YES    | YES        | YES         | —        | YES             | —             | Disk KV cache at `~/.ds4/kvcache/`. Rebuildable from saved KV checkpoints. |

## Persistence

| Storage           | Technology   | Location                            | Data                                |
|-------------------|-------------|-------------------------------------|-------------------------------------|
| Disk KV cache     | Binary file  | `~/.ds4/kvcache/<sha1>.kv`         | KV cache header + rendered text + DS4 session payload + optional tool-id map |
| Server traces     | Text file    | Configurable via `--trace`          | Full request/response log          |
| Agent sessions    | Binary file  | `~/.ds4/kvcache/`                  | Same format as KV cache, with session title trailer |

**Critical finding**: DS4's persistent state is exclusively **KV cache tokens
for fast inference resume**. It is NOT agent state, NOT conversation history
(though text is included for prefix matching), NOT memory, NOT tool state. The
payload is a GPU graph dump — model-specific, engine-version-specific, and
quantization-specific.

## Tools

| Aspect              | Status         | Details                                                              |
|---------------------|----------------|----------------------------------------------------------------------|
| Definition          | Hardcoded      | Eight tools in `ds4_agent.c`: `read`, `more`, `write`, `list`, `edit`, `search`, `google_search`, `visit_page`, `bash`, `bash_status`, `bash_stop`. |
| Discovery           | Hardcoded      | Tools are built into the agent binary. No runtime discovery.         |
| Schemas             | Hardcoded      | Each tool has a hardcoded DSML schema. Server maps to OpenAI/Anthropic tool schemas. |
| Execution           | Native C       | Tool execution is C functions in `ds4_agent.c`. No sandboxing.       |
| Results             | Text           | All tools return text, appended as "tool" role messages.             |
| Errors              | Text           | Errors returned as tool result text to the model.                    |
| Persistence         | NO             | Tool execution state is not persisted. Tool results appear in transcript. |
| Pluggability        | NO             | No plugin system for adding new tools. Tools are hardcoded.          |

**Classification**:
- Tool *definitions* (name, schema): PORTABLE
- Tool *implementations*: RUNTIME_BOUND (hardcoded C functions)
- Tool *configuration*: PORTABLE (API tool schemas from client)
- Tool *execution state*: RUNTIME_BOUND (in-flight tool calls)
- Tool *results*: PORTABLE (text messages in transcript)

## Filesystem and Environment

| Capability              | Status         | Details                                                              |
|-------------------------|----------------|----------------------------------------------------------------------|
| Workspace management    | NO             | `--chdir` flag sets working directory. No project/workspace abstraction. |
| Project directory       | MINIMAL        | Agent hardcodes `--chdir /path/to/ds4` for loading Metal kernels.    |
| File reading            | YES (agent)    | `read` and `more` tools read file contents with line range.          |
| File writing            | YES (agent)    | `write` tool writes text to file. `edit` tool does old/new text replacement. |
| Search                  | YES (agent)    | `search` tool does recursive text/regex search.                      |
| Git repositories        | NO             | No Git integration.                                                  |
| Environment variables   | NO             | No environment variable management.                                  |
| Virtual environments    | NO             | No venv/pyenv/conda management.                                      |
| Dependencies            | NO             | No package manager integration.                                      |
| Shell                   | YES (agent)    | `bash` tool executes shell commands.                                 |
| Ports/services          | NO             | No port or service management.                                       |

## Security

| Aspect                    | Status         | Details                                                              |
|---------------------------|----------------|----------------------------------------------------------------------|
| Command execution restrictions | NO        | The `bash` tool can run arbitrary shell commands. No restriction.    |
| Filesystem restrictions   | NO             | Tools can read/write any file the process can access. No sandbox.    |
| Subprocess permissions    | NO             | Subprocesses inherit process permissions.                            |
| Sandboxing                | NO             | No sandbox, container, or isolation mechanism.                       |
| Credentials               | NONE           | API key is dummy "dsv4-local". No real credential storage.           |
| Network access            | YES (agent)    | `google_search` and `visit_page` tools make network requests via Chrome CDP. |
| Authentication            | NO             | No authentication on the server. The API key field is accepted but ignored. |
| Secrets management        | NO             | No secrets management.                                               |

**Security note**: DS4 has no security model. The native agent trusts the model
to call tools appropriately. The server has no authentication. There are no
secrets to exclude from Zion state because DS4 does not store any secrets.

## Runtime-Bound State

All of the following are `runtime_bound` and cannot be meaningfully serialized:

| State                     | Reason                                                              |
|---------------------------|---------------------------------------------------------------------|
| `ds4_engine`              | 81GB+ of model weights in GPU/Metal/CUDA memory. GGUF mmap.        |
| `ds4_session`             | Live KV cache, graph state, logits. GPU-internal state.            |
| Disk KV cache payload     | Binary format tied to DS4 engine version, model layout, quantization. |
| Active agent run          | Per-agent variables: transcript tokens, tool results, context window. |
| Network connections       | Server client sockets, Chrome CDP connections, bash subprocess pipes. |
| GPU graph state           | Metal graphs, CUDA streams, GPU buffers.                           |
| Threads and mutexes       | Pthreads, condition variables, mutex locks.                        |
| Bash subprocesses         | Running shell processes from agent `bash` tool.                    |

## Zion Relationship

### Evaluated architectures

**Architecture A: `Zion → DS4 → LLM/Tools`**

NOT VALID. DS4 is not a generic orchestration layer. It is an LLM inference
engine with a hardcoded agent. Zion cannot send a workload to DS4 and expect
DS4 to orchestrate it — DS4 only generates tokens for the model it was built for.

**Architecture B: `DS4 → Zion → LLM/Tools`**

NOT VALID. DS4 has no concept of portable agent state and no mechanism to
consume or produce ZionState.

**Architecture C: `Zion State → DS4 Runtime → LLM/Tools/OS`**

PARTIALLY VALID. DS4 can serve as the **LLM provider** in this stack, but NOT
as the orchestration runtime. The correct role is:

```
Zion State
    │
    ▼
Agent Framework (e.g., Cheshire Cat, opencode, custom)
    │
    ├── DS4 (via OpenAI-compatible API)  ← local LLM inference
    ├── Filesystem
    ├── Tools
    └── OS
```

**Architecture D: `Zion → Adapters → Various Runtimes`**

MOST ACCURATE. DS4 fits as a target in Zion's adapter architecture — but the
adapter role is different from Cheshire Cat:

- Cheshire Cat adapter: extract/import portable agent state (conversations, memories, config)
- DS4 adapter: connect to DS4 as an LLM inference provider (model config, API URL)

### Correct relationship

```
Zion portable agent state
    │
    ▼
Runtime Adapter
    │
    ├── Cheshire Cat (for state extraction/import from CC)
    │
    └── DS4 (for local LLM inference as OpenAI-compatible provider)
```

DS4 is not a runtime that can execute a Zion agent. It is a local model
inference engine. The appropriate integration is at the **LLM provider level**,
not the **runtime level**.

## Zion vs DS4 Responsibility Boundary

| Responsibility            | Zion     | DS4      | Shared  | External         |
|---------------------------|----------|----------|---------|------------------|
| Persistent agent state    | PRIMARY  | NO       | —       | —                |
| Conversation              | PRIMARY  | NO       | —       | —                |
| Memory                    | PRIMARY  | NO       | —       | —                |
| Tool definitions          | PRIMARY  | HARDCODED| —       | —                |
| Tool execution            | NO       | AGENT    | POSSIBLE| —                |
| Local process execution   | NO       | AGENT    | POSSIBLE| —                |
| Filesystem operations     | NO       | AGENT    | POSSIBLE| —                |
| LLM inference             | NO       | PRIMARY  | —       | —                |
| Ollama integration        | NO       | N/A      | —       | NOT SUPPORTED    |
| Runtime environment       | NO       | LIMITED  | —       | OS               |
| Portable state export     | PRIMARY  | NO       | —       | —                |
| State import/reconstruct  | PRIMARY  | NO       | —       | —                |
| Session persistence       | PRIMARY  | KV ONLY  | —       | —                |
| GPU management            | NO       | PRIMARY  | —       | Metal/CUDA/ROCm  |
| Model serving             | NO       | PRIMARY  | —       | —                |

**Key finding**: Zion and DS4 have no overlapping responsibility. Zion owns
portable agent state. DS4 owns local LLM inference. The only integration point
is DS4's OpenAI-compatible API as an LLM backend for agents whose state Zion
manages.

## Cheshire Cat vs DS4 Comparison

| Capability                | Cheshire Cat               | DS4                        | Zion relevance               |
|---------------------------|----------------------------|----------------------------|------------------------------|
| Persistent conversation   | YES (ChatDB JSON)          | NO (only KV tokens)        | Zion should own conversation |
| Key-value memory          | YES (Store/UserStore)      | NO                         | Zion should own memory       |
| Vector memory             | NOT PRESENT                | NOT PRESENT                | Future Zion consideration    |
| Tool definitions          | Defined (@tool)            | Hardcoded in C             | Zion should own definitions  |
| Tool execution            | Python agent methods       | Hardcoded C functions      | Runtime-specific             |
| Plugin system             | YES (MadHatter)            | NO                         | Zion-agnostic                |
| Local process execution   | NO                         | LIMITED (agent bash tool)  | Future consideration         |
| Filesystem control        | NO (only uploads)          | YES (agent tools)          | Future consideration         |
| LLM abstraction           | YES (ModelProvider)        | N/A (is the LLM)           | Zion should be LLM-agnostic  |
| Local LLM support         | Via provider               | NATIVE                     | Complementary                |
| Runtime reconstruction    | Rebuildable from plugins   | KV cache resume            | Different concerns           |
| Portable state            | YES (JSON)                 | NO (binary only)           | Zion's core purpose          |

**Complementary roles**: Cheshire Cat and DS4 solve completely different
problems. Cheshire Cat is an agent framework with state management. DS4 is a
local inference engine. They are not alternatives — they could be combined in
different layers of a stack.

## Local Coding-Agent Feasibility

Scenario evaluation: Zion + DS4 as a local coding assistant.

| Capability                    | Status       | Details                                                        |
|-------------------------------|--------------|----------------------------------------------------------------|
| Persistent memory             | Zion's job   | Zion must implement memory. DS4 provides none.                 |
| Remembers conversations       | Zion's job   | DS4 API sends full history each request. Zion manages it.      |
| Local project work            | DS4 agent    | DS4's native agent supports this. NOT via Zion.                |
| Local tools (read/write/edit) | DS4 agent    | Hardcoded into `ds4_agent.c`. NOT extensible by Zion.          |
| Local LLM                     | DS4          | DS4 IS the local LLM. Runs via `ds4-server`.                   |
| Can be stopped                | OS process   | Both Zion and DS4 are OS processes. Can be killed.             |
| Move to another machine       | Zion + DS4   | Zion state is portable. DS4 requires the same model + same engine on target. |
| Reconstruct portable state    | Zion         | Zion's primary responsibility.                                 |

**Conclusion**: A local coding agent combining Zion and DS4 is PARTIALLY
FEASIBLE but requires significant architectural work:

1. Zion manages agent state (conversation, memory, configuration)
2. DS4 provides local LLM inference via its OpenAI-compatible API
3. The tools are split: Zion owns tool *definitions* and *scheduling*, the
   runtime owns tool *execution*
4. DS4's native agent cannot be used — it is a monolithic binary with no
   external state management. Zion would need to work with `ds4-server` only,
   bypassing `ds4-agent` entirely.

The most practical architecture:

```
Zion
  │
  ├── manages state (conversation, memory, config)
  │
  ├── calls DS4 via OpenAI API (LLM inference only)
  │
  └── executes tools locally (filesystem, bash, etc.)
```

## Model Gaps

### Gap 1: DS4 is not an orchestration layer

The experiment hypothesis was based on a category error. DS4 is a local
inference engine, not a local orchestrator. It cannot replace the execution
layer of an agent framework. Zion must look elsewhere for orchestration.

### Gap 2: DS4's adapter role is different from Cheshire Cat's

The existing `adapters/ds4/` directory in Zion suggests a symmetric role to
the Cheshire Cat adapter (extract/import agent state). This is incorrect —
DS4 has no agent state to extract. The integration should be at the LLM
provider level, which is a fundamentally different adapter interface.

**What should change in Zion**: The DS4 adapter concept should be reconsidered.
DS4 does NOT belong in the same adapter category as Cheshire Cat. It is an
LLM provider, not an agent framework with persistent state.

### Gap 3: No model for "LLM provider configuration" in Zion

Zion has no abstraction for configuring an LLM backend. `RuntimeState` has
`engine` and `model` but no `provider_url`, `api_key`, or `provider_type`
fields.

**What should change in Zion**: A `ProviderConfig` or `LLMConfig` model may be
needed to represent the LLM backend configuration as portable state.

### Gap 4: No model for runtime reconstruction requirements

Zion cannot currently express "this agent needs a local LLM running at
http://localhost:8080" or "this agent requires DS4 with DeepSeek V4 Flash
Q2-imatrix". These are runtime requirements, not agent state, but they are
necessary for reconstructing the agent in a new environment.

## Open Questions

1. **Is DS4 even the right project?** The name "DS4" appears in Zion's existing
   codebase alongside Cheshire Cat as if it were a comparable agent framework.
   This experiment reveals it is not. Was DS4 intended to be something else?

2. **Should Zion define LLM provider configuration?** If Zion agents need to
   reconstruct their runtime environment, they need to know what LLM to use,
   where it is, and how to connect to it. Is this "agent state" or
   "infrastructure configuration"?

3. **Agent tool portability**: How should Zion represent tool definitions that
   can be reconstructed in different runtimes? DS4's tools are hardcoded C
   functions. Cheshire Cat's tools are Python `@tool` decorators. Neither is
   portable without reimplementation.

4. **KV cache as agent state?**: DS4's disk KV cache is the closest thing it
   has to "persistent agent state". But it is a model-specific binary blob that
   survives server restarts. Is this "agent session state" or just "inference
   optimization cache"?

## Conclusion

> **Is DS4 a technically suitable local orchestration layer for Zion, and if so, what should the boundary between Zion and DS4 be?**

**NO. DS4 is NOT suitable as a local orchestration layer for Zion.**

DS4 (DwarfStar4) is a **specialized local inference engine** for DeepSeek V4
Flash on Apple Silicon, CUDA, and ROCm. It is not an agent framework, not an
orchestrator, not a process manager, and not a general-purpose runtime.

DS4's role in a Zion architecture would be as an **LLM inference provider**,
accessible through its OpenAI-compatible HTTP API — exactly the same role
Ollama, or any OpenAI-compatible service would play. The `ds4-server` binary
serves models via standard OpenAI endpoints, and any Zion agent that supports
OpenAI-compatible providers can use it.

The existing `adapters/ds4/` directory in Zion is based on a misunderstanding
of DS4's purpose. DS4 has no agent state to extract or import. Its persistent
data (KV cache files) is inference-specific binary data tied to engine version,
model layout, and quantization — not portable agent state.

The recommended architecture is:

```
Zion portable agent state
        │
        ▼
Agent Runtime (any framework)
        │
        ├── DS4 (via OpenAI API)  ← LOCAL LLM INFERENCE
        ├── Other LLM providers
        └── Local tools (filesystem, shell, etc.)
```

Zion owns the portable agent state. DS4 provides local inference. They are
complementary at different layers of the stack, not overlapping alternatives.
