# DS4 State Portability Matrix

Experiment #002 — precise state mapping between DS4 (DwarfStar4) and Zion v0.1.

## Matrix

| State / Capability      | Exists | Persistent | Extractable | Portable | Reconstructable | Runtime-bound | Evidence |
|-------------------------|--------|------------|-------------|----------|-----------------|---------------|----------|
| Identity                | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No identity model in any source file |
| Conversation            | YES    | PARTIAL    | PARTIAL     | YES      | —               | —             | Messages in API requests (`ds4_server.c`). Agent transcript in memory (`ds4_agent.c`). Text visible in KV cache files for prefix matching only. |
| Memory                  | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No memory system of any kind |
| Context / KV state      | YES    | YES        | PARTIAL     | —        | —               | YES           | `ds4_kvstore` (`ds4_kvstore.c`, `ds4_kvstore.h`). Binary payload format "DSV4" — engine-version-specific, model-specific, quantization-specific |
| Tasks                   | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No task system |
| Tool definitions        | YES    | NO         | YES         | YES      | —               | —             | Eight tools hardcoded in `ds4_agent.c`. Names and DSML schemas are portable descriptions |
| Tool implementation     | YES    | NO         | NO          | —        | —               | YES           | C functions in `ds4_agent.c`. Hardcoded, not pluggable |
| Tool results            | YES    | NO         | YES         | YES      | —               | —             | Tool results appended as "tool" role messages in transcript |
| Configuration           | YES    | NO         | YES         | YES      | —               | —             | CLI flags only. No config file. `--ctx`, `--temp`, `--top-p`, etc. |
| Environment             | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No environment variable management |
| Processes               | YES    | NO         | NO          | —        | —               | YES           | Agent `bash` tool creates subprocesses. Not persisted |
| Model configuration     | YES    | PARTIAL    | YES         | YES      | —               | —             | CLI flags for model params. Not saved — must be re-specified |
| Model runtime           | YES    | NO         | NO          | —        | —               | YES           | `ds4_engine` — 81GB+ weights in GPU memory, Metal/CUDA graphs, GGUF mmap |
| Sessions                | YES    | PARTIAL    | PARTIAL     | —        | —               | YES           | `ds4_session` — runtime-bound GPU state. Disk KV cache provides limited prefix-based resume |
| Credentials             | NO     | N/A        | N/A         | N/A      | N/A             | N/A           | No credential storage. API key is dummy "dsv4-local" |
| Logs                    | YES    | YES        | YES         | YES      | —               | —             | Server `--trace` writes detailed traces. Agent logs to terminal |
| Caches                  | YES    | YES        | YES         | —        | YES             | —             | Disk KV cache at `~/.ds4/kvcache/<sha1>.kv`. Format is DS4-specific binary |
| GPU state               | YES    | NO         | NO          | —        | —               | YES           | Metal/CUDA graph state. In GPU memory only |
| Threads / mutexes       | YES    | NO         | NO          | —        | —               | YES           | Server: `pthread_mutex_t`, `pthread_cond_t`. Agent: UI + worker threads |
| Network connections     | YES    | NO         | NO          | —        | —               | YES           | Server client sockets, Chrome CDP, bash pipes |

## Classification Summary

| Classification | Components |
|----------------|------------|
| PORTABLE       | Conversation messages (JSON), tool names/schemas (DSML), CLI configuration flags, server traces, tool results (text), log data |
| RECONSTRUCTABLE| Disk KV cache files (same engine + model), model download scripts (`download_model.sh`), Makefile build targets |
| RUNTIME-BOUND  | `ds4_engine` (weights + graphs), `ds4_session` (KV cache + logits in GPU memory), active processes, threads/mutexes, network connections, GPU state, model binary payload ("DSV4") |
| NOT PRESENT    | Identity, memory (any type), tasks, environment variables, credentials, secrets |

## Critical Notes

1. **DS4 has no agent state.** Every state component in DS4 is either
   inference-specific (KV cache, engine, session) or incidental to the running
   process (threads, connections). There is no agent identity, no memory, no
   task tracking, no persistent configuration.

2. **The "conversation" is transient.** The API server receives messages in
   each request and does not store them. The native agent keeps a transcript
   in memory. The KV cache stores rendered text only for prefix matching
   (inference optimization), not as a conversation archive.

3. **The KV cache is NOT portable state.** The disk KV cache payload uses the
   "DSV4" binary format with magic bytes `0x34565344`. It contains GPU KV
   tensor data serialized in a DS4-engine-specific layout. It is portable only
   across identical DS4 engine versions running the same model GGUF with the
   same quantization.

4. **No secrets to protect.** DS4 has no credential management. The API key
   is a dummy value. No secrets need to be excluded from Zion state because
   none exist.

## References

All source paths are relative to `antirez/ds4` at commit `54b36ed`.
