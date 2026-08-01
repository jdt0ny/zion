# Related Projects

## Purpose
Track other projects, frameworks, and tools that overlap with Zion's research goals. This helps avoid reinvention and identify potential integration points.

## Categories

### Agent Frameworks with State Management
| Project | Language | State Model | Portability | Notes |
|---------|----------|-------------|-------------|-------|
| **Cheshire Cat** | Python | Key-value + conversations | Partial (JSON export) | Primary research target; plugin system |
| **LangChain** | Python/JS | Memory classes, conversation buffers | In-memory only | No native portable state |
| **AutoGen** | Python | Agent state in conversation history | Limited | Multi-agent, no cross-runtime |
| **Semantic Kernel** | C#/Python/JS | Memory, skills, plugins | Partial | Microsoft; skill portability focus |

### Local Inference Engines
| Project | Language | Model Support | API Compatibility | Notes |
|---------|----------|---------------|-------------------|-------|
| **DS4** | C | DeepSeek V4, GLM 5.2 | OpenAI/Anthropic compatible | Primary research target |
| **Ollama** | Go | Many (GGUF) | OpenAI compatible | Mature ecosystem |
| **llama.cpp** | C++ | GGUF models | OpenAI compatible | Foundation for many |
| **vLLM** | Python | Many | OpenAI compatible | High-throughput serving |

### State Serialization / Portability
| Project | Focus | Format | Status |
|---------|-------|--------|--------|
| **AgentState** (hypothetical) | Cross-runtime agent state | JSON/YAML | Research phase |
| **LangSmith** | Tracing/debugging | Proprietary | Commercial |
| **Weights & Biases** | Experiment tracking | Proprietary | Commercial |

## Integration Opportunities

### Immediate (v0.1-v0.3)
- [ ] Cheshire Cat adapter for conversation + key-value extraction
- [ ] DS4 as LLM provider via OpenAI-compatible API
- [ ] Round-trip JSON test suite against real Cheshire Cat instances

### Medium-term (v0.4-v0.5)
- [ ] Explore LangChain's `Memory` abstraction as a target for Zion state import
- [ ] Investigate `llama.cpp` server as alternative local LLM backend
- [ ] Design adapter interface for any OpenAI-compatible provider

### Long-term (v1.0+)
- [ ] Cross-runtime migration: Cheshire Cat → custom runtime
- [ ] State reconciliation for conflicting portable state
- [ ] Standardized agent state interchange format (beyond JSON)

## Competitive Landscape Gaps
1. **No open standard** for portable AI agent state across runtimes
2. **No framework** treats LLM provider configuration as portable state
3. **No tool** explicitly classifies state into portable/reconstructable/runtime_bound

## Contribution Tracking
- Add new projects as discovered
- Note any collaboration or PR opportunities
- Link to Zion issues that reference these projects