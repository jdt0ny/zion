# Changelog

Tutte le modifiche significative a Zion sono documentate in questo file.

Il formato si basa su [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Aggiunto

- **Server MCP** — strumenti MCP (Model Context Protocol) per gestire lo stato portabile degli agenti AI.
  - `zion_export`: esporta uno stato Zion su file JSON.
  - `zion_import`: importa uno stato Zion da file JSON.
  - `zion_inspect`: riepilogo stato con conteggi di portabilità.
  - `zion_measure`: confronta due stati e misura la fedeltà del recupero.
  - `zion_round_trip`: export → import → misura in un solo call.
  - Entry point `zion-mcp` (console script) con avvio in modalità stdio.
  - Extra `pip install -e ".[mcp]"` per dipendenze opzionali.
  - Istruzioni di configurazione per Claude Desktop in README.

## [0.1.0] - 2025

### Aggiunto

- Modello `ZionState` v0.1 con 10 dimensioni di stato (identity, project, conversation, memory, decisions, tasks, tools, knowledge, configuration, runtime).
- Modelli Pydantic: `AgentIdentity`, `ProjectState`, `Message`, `MemoryEntry`, `Decision`, `Task`, `RuntimeState`.
- Serializzazione JSON con fedeltà round-trip dimostrata.
- Misurazione quantitativa del recupero (`RecoveryReport`) con fedeltà per dimensione.
- Classificazione dello stato in tre categorie di portabilità: portatile, ricostruibile, legato al runtime.
- Test: 37 assertions su modelli, serializzazione, round-trip e misurazione recupero.
- Adattatori stub per Cheshire Cat e DS4.
- Specifiche e documenti di ricerca per 4 esperimenti (Cheshire Cat, DS4, Claude Code).
