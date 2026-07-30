# Cheshire Cat State Portability Matrix

Experiment #001 — precise state mapping between Cheshire Cat AI v2.0.23 and Zion v0.1.

## Matrix

| State               | Exists | Persistent | Extractable | Portable | Reconstructable | Runtime-bound | Evidence |
|---------------------|--------|------------|-------------|----------|-----------------|---------------|----------|
| Identity            | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No identity model in any source file |
| Conversation        | YES    | YES        | YES         | YES      | —               | —             | `ChatDB` (`cat/scaffold/plugins/chats/db.py`), `Message` (`cat/types/messages.py`) |
| Key-value memory    | YES    | YES        | YES         | YES      | —               | —             | `Store`/`UserStore` (`cat/db/helper.py`), `KeyValueDB`/`UserKeyValueDB` (`cat/db/models.py`) |
| Vector/embed memory | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | Not present in core codebase |
| Knowledge/documents | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | Not present in core codebase |
| Tool definitions    | YES    | PARTIAL    | PARTIAL     | YES      | YES             | —             | `Tool` class (`cat/mad_hatter/decorators/tool.py`); name+input_schema portable, `func` body is not |
| Tool implementation | YES    | NO         | PARTIAL     | —        | —               | YES           | Python function bodies in Agent subclasses; requires compatible runtime |
| Tool configuration  | YES    | YES        | YES         | YES      | —               | —             | MCP server settings (`cat/scaffold/plugins/mcp_client/config.py`); service settings in global store |
| Plugin code         | YES    | YES        | YES         | —        | YES             | —             | Python source on filesystem (`cat/mad_hatter/plugin.py`); requires compatible runtime |
| Plugin manifest     | YES    | YES        | YES         | YES      | —               | —             | `plugin.json` → `PluginManifest` (`cat/mad_hatter/plugin_manifest.py`) |
| Plugin config       | YES    | YES        | YES         | YES      | —               | —             | Service `Settings` persisted in key-value store (`cat/services/service.py`) |
| Plugin activation   | YES    | YES        | YES         | YES      | —               | —             | `active_plugins` list in global store (`cat/mad_hatter/mad_hatter.py`) |
| Python config       | YES    | YES        | YES         | YES      | —               | —             | `config.py` in project folder (`cat/config/__init__.py`) |
| DB-backed settings  | YES    | YES        | YES         | YES      | —               | —             | Service settings in global key-value store (`cat/services/service.py`) |
| Secrets (API_KEY)   | YES    | YES        | YES         | —        | —               | —             | Must NOT be exported (`cat/config/defaults.py`) |
| CheshireCat single  | YES    | NO         | NO          | —        | —               | YES           | `_ccat` module global (`cat/ambient/runtime.py`) |
| Service singletons  | YES    | NO         | NO          | —        | —               | YES           | Cached on class via `ServiceMeta` (`cat/services/service.py`) |
| MadHatter caches    | YES    | NO         | PARTIAL     | —        | YES             | —             | `hooks`, `endpoints`, `service_classes` dicts; rebuildable from plugin files (`cat/mad_hatter/mad_hatter.py`) |
| ContextVars         | YES    | NO         | NO          | —        | —               | YES           | Per-request context (`cat/ambient/context_vars.py`) |
| Model caches        | YES    | NO         | NO          | —        | —               | YES           | In-memory `_models` on providers (`cat/services/model_providers/openai_compatible.py`) |
| Agent run state     | YES    | NO         | NO          | —        | —               | YES           | Per-call instance fields (`cat/services/agents/base.py`) |

## Notes

- "EXISTS" means the state component has a concrete representation in the
  Cheshire Cat source code (class, table, variable, file). "NO" means the
  abstraction does not exist anywhere in the codebase.
- "PORTABLE" means the data is JSON-serializable and can be meaningfully
  interpreted outside the original runtime. Tool *implementation* is not
  portable because it is Python function bytecode.
- "RECONSTRUCTABLE" means the state is reproducible given the same
  configuration/code/source but cannot be directly copied as a blob.
- "RUNTIME-BOUND" means the state depends on process memory, network
  connections, or runtime-specific execution context.
- Secrets (API keys, tokens, passwords) are marked as "extractable" but must
  be intentionally excluded from Zion state as a security requirement.

## References

All source paths are relative to `cheshire-cat-ai/core` at commit `1493ce3`.
