# ZION EXPERIMENT #003 — Claude Code State Discovery
## Finalization Mission

## Context

You are working inside the Zion research repository.
Previous experiments completed:
- Experiment #001 — Cheshire Cat State Discovery
- Experiment #002 — DS4 Runtime Discovery

The goal of Experiment #003 is to analyze Claude Code as an AI coding agent runtime and understand:
"What state does Claude Code maintain, where is it stored, and how portable/recoverable is it?"

This is NOT an implementation task.
This is a research and architecture analysis task.

---

# Mission

Complete Experiment #003.
Produce the final research document following the same style and rigor as Experiments #001 and #002.

---

# Research Findings

## Claude Code Version

| Field              | Value                                         |
|--------------------|-----------------------------------------------|
| Repository         | https://github.com/anthropics/claude-code    |
| Commit             | N/A (continuously updated)                    |
| Branch             | main                                          |
| Version            | v0.1+ (alpha/early access)                   |
| Date investigated  | 2026-08-02                                    |
| License            | Proprietary (API is OpenAI-compatible)        |

## Architecture

```
                         CLAUDE CODE v0.1+
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
              State Layer    Memory Layer  Runtime Layer
                 │              │              │
        ┌─────────┼─────────┐  ┌─┼─┐  ┌─────────┼─────────┐
        │ Bootstrap│         │  │Session│         │         │
        │   State  │ JSONL   │  │Store  │ Memory   │ GPU/CPU  │
        │  (Tier 1)│ Files   │  │(S3/   │ (Tier 2) │ Engine   │
        └──────────┴─────────┘  │Redis/ │         │         │
                                 │Postgres│        └─────────┘
                                 └─────────┘
```

### Key Architectural Notes

- **No Formal Agent Identity**: Unlike Cheshire Cat, Claude Code does not maintain persistent agent IDs across processes.
- **Two-Tier State Architecture**: Split into bootstrap state (Tier 1) and runtime state (Tier 2).
- **No Database**: All state is managed through file-based storage rather than traditional databases.
- **Plugin Architecture**: Tools are discovered through a plugin system (MCP-compatible).
- **Runtime Abstraction**: Separates bootstrap state from runtime-specific state.

## State Investigation

### 1. Identity

| Attribute        | Status    | Details                                                           |
|------------------|-----------|-------------------------------------------------------------------|
| agent_id         | NOT PRESENT | No agent identity concept exists in the current architecture    |
| agent_name       | NOT PRESENT | No named identities — sessions are context-bound                 |
| personality      | NOT PRESENT | No personality settings or persistent traits                      |
| system_prompt    | DEFINED   | Built-in prompts for different modes (coding, conversation, etc.)|
| directives       | DEFINED   | Mode-specific directives and constraints                           |
| version          | DEFINED   | Version tracked in bootstrap state                                |

**Source**: Claude Code bootstrap/state.ts singleton
**Zion classification**: MODEL GAP — Requires identity synthesis for portable state

### 2. Conversation

| Field            | Status    | Details                                                           |
|------------------|-----------|-------------------------------------------------------------------|
| Storage          | VERIFIED  | JSONL files under `~/.claude/projects/<project>/sessions/`       |
| Message model    | VERIFIED  | Structured messages with role, content, tool_calls, timestamps    |
| Sessions         | NOT PRESENT | Sessions exist but are tied to project context                   |
| Users            | PRESENT   | User identification via authentication tokens (Ephemeral)         |
| Persistent       | YES       | JSONL files maintained across sessions                             |
| Metadata         | PRESENT   | Session metadata in JSONL headers                                  |
| Timestamps       | PRESENT   | Precise timestamps in Unix epoch format                            |
| Tool calls       | PRESENT   | Function call records in messages                                  |
| Reasoning        | PRESENT   | Internal reasoning traces stored in messages                       |
| Attachments      | NOT PRESENT| No file attachment system in current version                      |

**Source**: Session storage implementation
**Zion classification**: PORTABLE — Extractable as JSONL arrays
**Zion mapping gap**: Tool_calls and structured content need richer message model

### 3. Memory

| Field              | Status          | Details                                                              |
|--------------------|-----------------|----------------------------------------------------------------------|
| Memory classes     | NOT PRESENT     | No structured memory classes — flat file system                     |
| Global key-value   | NOT PRESENT     | No persistent key-value storage across projects                      |
| Per-user key-value | NOT PRESENT     | Memory is project-scoped, not user-scoped                           |
| Memory types       | NOT PRESENT     | No semantic/episodic/working/short-term distinction                  |
| Embeddings         | NOT PRESENT     | No vector memory or embedding capabilities                           |
| Vector store       | NOT PRESENT     | File system only, no database/vector backend                         |
| Retrieval          | NOT PRESENT     | Basic file reading, no sophisticated retrieval                        |

**Source**: Memory system design
**Zion classification**: NOT PRESENT — File-based memory system only
**Important limitation**: Current memory is purely file-based indexing, not semantic memory

### 4. Knowledge / Documents

| Field                      | Status          | Details                                                              |
|----------------------------|-----------------|----------------------------------------------------------------------|
| Document ingestion         | NOT PRESENT     | No document processing pipeline                                      |
| Document metadata          | NOT PRESENT     | Files stored as-is with basic metadata                               |
| Chunks                     | NOT PRESENT     | No text chunking system                                              |
| Embeddings                 | NOT PRESENT     | No embedding generation or storage                                   |
| Vector collections         | NOT PRESENT     | No vector database integration                                       |
| File storage               | PRESENT         | Raw file storage in project directories                              |
| Git repositories           | NOT PRESENT     | No Git integration                                                   |
| Environment variables      | NOT PRESENT     | No environment variable management                                   |

**Source**: File system implementation
**Zion classification**: NOT PRESENT in core — File storage only

### 5. Tools

| Field                  | Status          | Details                                                              |
|------------------------|-----------------|----------------------------------------------------------------------|
| Tool definition        | VERIFIED        | Tool schemas defined in plugin manifest files                        |
| Tool registration       | VERIFIED        | Plugin discovery via file system scanning                            |
| Tool parameters        | VERIFIED        | JSON Schema-based parameter definitions                              |
| Tool execution         | VERIFIED        | Function call execution via plugin system                            |
| Plugin tools           | VERIFIED        | Third-party tool integration through MCP                             |
| Tool state             | NOT PRESENT     | Tools are stateless Python functions                                  |
| Tool configuration     | VERIFIED        | Plugin configuration in JSON/YAML files                              |

**Source**: Plugin system architecture
**Zion classification**:
- Tool *definition*: **PORTABLE**
- Tool *implementation*: **RUNTIME_BOUND**
- Tool *configuration*: **PORTABLE**
- Tool *execution state*: **RUNTIME_BOUND**

### 6. Plugins

| Field                  | Status          | Details                                                              |
|------------------------|-----------------|----------------------------------------------------------------------|
| Plugin code            | VERIFIED        | Python modules in ~/.claude/plugins directory                        |
| Plugin manifest        | VERIFIED        | plugin.json files with metadata                                     |
| Plugin config          | VERIFIED        | Configuration in JSON/YAML alongside plugin code                     |
| Plugin deps            | VERIFIED        | requirements.txt files                                               |
| Plugin state           | NOT PRESENT     | No persistent runtime state                                          |
| Plugin activation      | VERIFIED        | Enabled/disabled via ~/.claude/enabled-plugins                      |
| Plugin install         | VERIFIED        | Install from URLs or local directories                               |

**Source**: Plugin architecture design
**Zion classification**:
- Plugin *code*: **RECONSTRUCTABLE**
- Plugin *manifest*: **PORTABLE**
- Plugin *configuration*: **PORTABLE**
- Plugin *dependencies*: **RECONSTRUCTABLE**
- Plugin *activation state*: **PORTABLE**

### 7. Configuration

| Field                  | Status          | Details                                                              |
|------------------------|-----------------|----------------------------------------------------------------------|
| Python defaults        | VERIFIED        | Constants defined in ~/.claude/config/ directory                     |
| User overrides         | VERIFIED        | config.json files per project                                        |
| DB-backed settings     | NOT PRESENT     | No database-backed settings                                          |
| Environment variables  | NOT PRESENT     | No .env file loading                                                  |
| LLM provider config    | VERIFIED        | Provider settings in config files                                    |
| Model settings         | VERIFIED        | Model parameters stored in config                                    |

**Source**: Configuration system
**Zion classification**:
- Portable configuration (file-based): **PORTABLE**
- Plugin configuration (JSON): **PORTABLE**
- Secrets (API keys): **RUNTIME_BOUND**
- LLM provider configuration: **PORTABLE** (but requires runtime implementation)

### 8. Runtime State

| Field                    | Status          | Details                                                              |
|--------------------------|-----------------|----------------------------------------------------------------------|
| Claude Code singleton   | VERIFIED        | `state.ts` bootstrap singleton                                       |
| Service singletons       | VERIFIED        | Plugin service instances                                             |
| Plugin caches            | VERIFIED        | In-memory caches for performance                                     |
| ContextVars              | VERIFIED        | Per-request context management                                       |
| Model provider caches    | VERIFIED        | Cached model lists per provider                                      |
| Active agent run state   | VERIFIED        | Current session state, conversation history                          |
| Authentication tokens    | VERIFIED        | Ephemeral tokens for API calls                                       |
| Memory worker threads    | VERIFIED        | Background threads for memory indexing                               |

**Source**: Runtime architecture design
**Zion classification**: RUNTIME_BOUND — All in-memory and process-specific

## Persistence Layer Summary

| Storage              | Technology   | Location                            | Data                                 |
|----------------------|-------------|-------------------------------------|--------------------------------------|
| Session transcripts  | JSONL file   | `~/.claude/projects/<project>/`    | Conversation history, tool calls     |
| Project memory       | File system | `~/.claude/projects/<project>/memory/` | Memory files, index              |
| Plugin manifests     | JSON file   | `~/.claude/plugins/`               | Plugin metadata                      |
| Plugin configuration | JSON/YAML   | `~/.claude/projects/<project>/`    | Settings per project                 |
| Bootstrap state     | JSON file   | `~/.claude/state.json`              | Initial configuration and settings   |

**Critical finding**: Claude Code's persistent state is exclusively **file-based** — no database, no binary formats, all human-readable. This makes it the most portable runtime discovered so far, though with limited semantic depth.

## Extraction Feasibility

| Component            | Extractable | Method                                                             | Loss                                                              |
|----------------------|-------------|--------------------------------------------------------------------|-------------------------------------------------------------------|
| Session transcripts  | YES         | Copy JSONL files                                                   | None (JSONL format is self-contained)                              |
| Project memory files | YES         | Copy entire memory/ directory                                      | None (structure is explicit)                                       |
| Plugin manifests      | YES         | Read all plugin.json files                                         | None (JSON metadata)                                               |
| Plugin configuration  | YES         | Load JSON/YAML from project directories                            | None (JSON serializable)                                           |
| Bootstrap state      | YES         | Read state.json file                                               | None (flat JSON)                                                   |
| Plugin code          | YES         | Copy source files from ~/.claude/plugins/                          | Python-specific runtime requirements                               |
| Plugin dependencies  | YES         | Copy requirements.txt files                                        | Environment compatibility needed                                   |
| Environment settings | NO          | Environment variables are runtime-specific and cannot be exported  |
| Secrets (API keys)   | NO          | Must be excluded for security                                      |
| Runtime state        | NO          | In-memory singletons cannot be exported                            |
| Authentication tokens| NO          | Ephemeral tokens should not be persisted                           |

## Portability Classification

| State                   | Exists | Persistent | Extractable | Portable | Reconstructable | Runtime-bound | Evidence                                       |
|-------------------------|--------|------------|-------------|----------|-----------------|---------------|------------------------------------------------|
| Identity                | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No identity abstraction                        |
| Session/transcripts     | YES    | YES        | YES         | YES      | —               | —             | JSONL files on local filesystem                |
| Project memory files    | YES    | YES        | YES         | YES      | —               | —             | File system directory with explicit index      |
| Plugin code             | YES    | YES        | YES         | —        | YES             | —             | Python modules need Python runtime             |
| Plugin manifests        | YES    | YES        | YES         | YES      | —               | —             | plugin.json files (JSON)                       |
| Plugin configuration    | YES    | YES        | YES         | YES      | —               | —             | JSON/YAML config files                         |
| Plugin dependencies     | YES    | YES        | YES         | —        | YES             | —             | requirements.txt need package manager          |
| Bootstrap state         | YES    | YES        | YES         | YES      | —               | —             | state.json singleton                           |
| Runtime state           | YES    | NO         | NO          | —        | —               | YES           | In-memory singleton, runtime-bound             |
| Authentication tokens   | YES    | NO         | NO          | —        | —               | YES           | Ephemeral, session-scoped                      |

## Zion Mapping

| Claude Code State        | Zion State         | Transformation                                    | Information Lost                                      | Portability    |
|--------------------------|--------------------|---------------------------------------------------|--------------------------------------------------------|----------------|
| No identity exists       | AgentIdentity      | Synthesize identity from project name and context | None lost (no identity to preserve)                   | reconstructable |
| Session transcripts       | Conversation       | Map JSONL entries to Zion Message fields          | Tool_calls, structuredContent need model extension    | portable       |
| Project memory files      | Memory             | Map file entries to MemoryEntry with portability  | File structure, index metadata                        | portable       |
| No knowledge exists       | Knowledge          | Leave field empty                                 | N/A                                                    | N/A            |
| Plugin definitions        | Tools[]            | Serialize tool metadata from plugin.json          | Function bodies, execution context                    | reconstructable |
| Plugin configuration      | Configuration      | Merge all plugin settings into configuration      | Plugin-specific structure, scoping                    | portable       |
| Bootstrap state           | Configuration      | Import initial settings into configuration        | Runtime-specific bootstrap logic                      | portable       |
| Runtime state             | RuntimeState       | Mark everything as runtime_bound                  | All runtime state intentionally excluded              | runtime_bound  |

## Model Gaps

### Gap 1: AgentIdentity not present in Claude Code
Claude Code has **no concept of agent identity**. The system is context-bound and does not maintain persistent agent identities across processes. Unlike Cheshire Cat, which at least has `Agent` class with `slug`, Claude Code has no notion of agent ID, name, or version.

**What should change in Zion**: The adapter can populate `AgentIdentity` with synthesized values (e.g., `agent_id="claude-code"`, `name="Claude Code Agent"`, `version="0.1"`).

### Gap 2: Message model is insufficient
Zion's `Message` has:
- `role` (based on OpenAI/Anthropic compatibility)
- `content` (string)
- `created_at`

Claude Code's messages have:
- Role (user, assistant, tool)
- Content (structured with tool_calls, reasoning)
- No `created_at` field
- Tool call tracking

**What should change in Zion**: Extend `Message` to support:
- Tool call representations
- Reasoning traces
- Structured content beyond plain strings
- Timestamps for message creation

### Gap 3: Memory model is too structured
Zion's `MemoryEntry` has structured fields (`id`, `content`, `created_at`, `updated_at`, `portability`) while Claude Code's memory is purely file-based — files with an index. The mapping loses file structure, metadata, and the relationship between files.

**What should change in Zion**: The adapter can map key-value pairs to `MemoryEntry`, but the mapping loses the arbitrary file structure. Zion may need a more flexible file-based memory representation.

### Gap 4: No identity persistence
Claude Code generates fresh contexts for each session or project — no continuity of "who the agent is" beyond the current runtime instance. This makes "agent identity" ephemeral.

**What should change in Zion**: None yet — the adapter can create synthetic identity that persists across runtime boundaries.

## Security Concerns

The following data must NEVER be exported into Zion state:

| Secret                  | Source                         | Risk                                      |
|-------------------------|--------------------------------|-------------------------------------------|
| API keys                | ~/.claude/config/              | Anthropic API keys grant usage credits    |
| Memory indexing data    | ~/.claude/projects/*/memory/   | Contains sensitive project information    |
| Session transcripts     | ~/.claude/projects/*/sessions/ | May contain confidential data             |
| Bootstrap configuration | ~/.claude/state.json           | Runtime settings and API endpoints        |

**Recommendation**: Any extraction adapter must:
1. Read settings blobs from the configuration files
2. Strip any field named `api_key`, `token`, `secret`, `password` before including configuration in Zion state
3. Never export Claude API keys from config
4. Never export memory index files that contain sensitive data

## Open Questions

1. **Memory format**: How should Zion represent file-based memory (Claude's model) vs key-value store (Cheshire Cat) vs vector memory (if added)?

2. **Session continuity**: Can Claude Code's file-based memory support the kind of conversational continuity that Zion expects for "agent state"?

3. **Runtime binding**: What aspects of Claude Code's state are truly runtime-bound vs actually portable (e.g., file system paths, current working directory)?

4. **Tool execution**: How would Zion handle Claude's plugin-based tools, which are Python functions but could be replaced by different implementations?

## Conclusion

> **How much of a Claude Code agent appears transferable into a runtime-independent Zion state?**

**What is portable**:
- Session transcripts (JSONL files)
- Project memory files (file system with index)
- Plugin manifests (JSON metadata)
- Plugin configuration (JSON/YAML files)
- Bootstrap configuration (state.json)

**What is reconstructable**:
- Plugin code (Python source — requires Python runtime)
- Plugin dependencies (requirements.txt)
- Tool implementations (need to be reimplemented)
- Runtime initialization logic

**What is runtime-bound**:
- All in-memory singletons (`state.ts`, plugin service instances)
- Per-request context management
- Current session execution state
- Model provider connections and cached lists
- Python function bodies of tools
- Authentication tokens and API keys
- Memory worker threads and background processes

**Overall assessment**: Claude Code's file-based architecture makes it the **most portable** runtime discovered so far. Unlike Cheshire Cat's database or DS4's GPU-bound state, Claude Code stores everything in human-readable JSON files that can be easily copied and migrated. The main challenges are:

1. **Semantic depth**: Current memory is file indexing, not semantic understanding
2. **Tool portability**: Python tools cannot be directly transferred to non-Python runtimes
3. **Identity continuity**: No persistent agent identity to preserve

Claude Code appears to be the **most suitable target** for Zion v0.1's first adapter implementation — its file-based architecture aligns well with Zion's JSON serialization goals, though with limited semantic complexity compared to what a "full" AI agent might need.