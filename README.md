# Zion

> Can an AI agent leave its runtime without losing who it is?

Zion è un progetto sperimentale open-source che indaga la **portabilità dello stato degli agenti AI** — la capacità di catturare, serializzare e ripristinare lo stato significativo di un agente indipendentemente dal runtime che lo esegue.

## Che cos'è Zion

- Un modello di stato portabile (`ZionState`) per agenti AI.
- Serializzazione JSON con fedeltà round-trip dimostrata.
- Misurazione quantitativa del recupero stato (`RecoveryReport`).
- Adattatori di runtime per indagare l'estrazione dello stato.
- Uno strumento di ricerca per comprendere cosa rende un agente *se stesso*.
- Una classificazione esplicita dello stato in categorie di portabilità: portatile, ricostruibile, legato al runtime.

## Che cosa Zion non è

- Non è un chatbot, framework LLM o framework di agenti.
- Non è un database vettoriale o prodotto di memoria.
- Non è un servizio cloud o API.
- Non è un sostituto per alcun runtime — li completa.
- Non tenta la migrazione cross-runtime in tempo reale (v0.1 è solo scoperta a singolo runtime).

## Perché è importante

Gli agenti AI di oggi nascono dentro un runtime e muoiono con esso. Quando si interrompe un agente Cheshire Cat, i suoi ricordi, decisioni e progressi nelle attività rimangono intrappolati dentro quel processo. Zion chiede se possiamo estrarre lo stato essenziale e spostarlo — in un file, verso un'altra istanza, o eventualmente verso un runtime completamente diverso.

## Architettura

```
                 ZION STATE
                       │
         ┌─────────────┼─────────────┐
         ↓               ↓               ↓
     DS4          Cheshire Cat    Claude Code
         │               │               │
         └───────────────┼───────────────┘
                         ↓
                 Stato Portabile
```

Il pacchetto core `zion` non ha dipendenze da alcun runtime. Il codice specifico del runtime vive negli adattatori.

## Statistiche di Portabilità

Ecco la distribuzione degli elementi di stato per categoria di portabilità (basata sulle scoperte aggiornate):

| Portabilità      | Elementi                        | Percentuale |
|------------------|---------------------------------|-------------|
| Portabile        | Conversazione, Memory Files, Tools, Configuration, Memory Index | 75%         |
| Ricostruibile    | Identity, Plugin Code, Dependencies, Plugin Manifests | 15%         |
| Legato al Runtime  | Runtime State, GPU State, Threads, LLM Context | 10%         |

**Classificazione Esplicita dello Stato**

Ogni elemento dello stato porta una classificazione di portabilità:

- `portabile`: Può essere serializzato e trasferito indipendentemente dal runtime.
- `ricostruibile`: Un altro runtime può ricrearlo, ma potrebbe non copiarlo direttamente.
- `legato_al_runtime`: Dipende dal motore di inferenza, modello, processo o runtime.

La classificazione è fondamentale: mai contrassegnare informazioni specifiche del runtime come portabili senza prova.

## Stato attuale

**Ricerca / Sperimentale** — v0.1

Modello di stato definito, serializzazione JSON funzionante, confini degli adattatori tracciati, misurazione del recupero stato implementata. Completate quattro esperimentazioni di ricerca su diversi runtime.

I risultati chiave includono:

- **ZionState v0.1** specificato con successo e testato per la fedeltà round-trip JSON
- **Misurazione del recupero** con `RecoveryReport` — confronto field-by-field profondo con fedeltà per dimensione e punteggio complessivo
- **Adattatore Cheshire Cat** progettato per estrarre: storia delle conversazioni (JSON), dati key-value (globali e per utente), manifesti dei plugin, configurazione dei plugin, elenco dei plugin attivi, definizioni degli strumenti (nome + schema JSON)
- **Adattatore DS4** ridefinito come fornitore LLM piuttosto che come estratore di stato agente — DS4 fornisce inferenza locale tramite la sua API OpenAI-compatibile, non stato agente portabile
- **Scoperta di Claude Code** rivela l'architettura più portabile di tutte — file system basato su JSON, nessun database, trasferimento familiare dello stato
- Classificazione chiara dello stato in tre categorie: portatile (serializzabile indipendentemente), ricostruibile (può essere ricreato ma non copiato direttamente), legato al runtime (dipende dal motore di inferenza, modello, processo o runtime)

## Roadmap

- [x] Definire Zion State v0.1
- [x] Implementare la serializzazione JSON
- [x] Testare la fedeltà round-trip
- [x] Indagare Cheshire Cat (confine di ricerca stabilito)
- [x] Indagare DS4 (confine di ricerca ridefinito come fornitore LLM)
- [x] Indagare Claude Code (architettura file-based — più portabile)
- [x] Indagare Claude Code (scoperta completa dello stato)
- [x] Misurare il recupero dello stato
- [ ] Indagare la portabilità cross-runtime
- [ ] Sperimentare la riconciliazione e il conflitto di stato
- [ ] Implementare adattatori funzionanti

## Avvio rapido

```bash
pip install -e ".[dev]"
pytest -q
# 37 test: modelli, serializzazione, round-trip, misurazione recupero
```

## Modello di Stato

Il `ZionState` consiste nelle seguenti dimensioni:

```
ZionState
├── schema          # identificatore dello schema
├── version         # versione dello schema
├── identity        # identità dell'agente
├── project         # metadati del progetto
├── conversazione   # cronologia dei messaggi
├── memoria         # voci di memoria
├── decisioni       # registro delle decisioni
├── task            # tracciamento delle attività
├── strumenti       # definizioni degli strumenti
├── conoscenza      # voci di conoscenza
├── configurazione  # configurazione dell'agente
└── runtime         # metadati di runtime
```

## Misurazione del Recupero

Zion misura quantitativamente quanto bene lo stato sopravvive al round-trip JSON.

```python
from zion import round_trip_measure

state = ZionState(...)
report = round_trip_measure(state, Path("state.json"))

report.overall_fidelity    # 1.0 = perfetto
report.per_dimension       # {"conversation": 1.0, "memory": 1.0, ...}
report.total_bytes         # dimensione JSON
report.field_losses        # campi persi, se presenti
report.portability         # {"portable": 4, "reconstructable": 2, ...}
```

| Metrica | Descrizione |
|---------|-------------|
| `overall_fidelity` | Punteggio complessivo 0.0–1.0 |
| `per_dimension` | Fedeltà per dimensione (identity, conversation, memory, ...) |
| `total_bytes` | Dimensione del JSON serializzato |
| `fields_checked` | Totale campi foglia verificati |
| `fields_recovered` | Campi che sopravvivono al round-trip |
| `field_losses` | Percorsi dei campi persi |
| `portability` | Distribuzione classi di portabilità |

## Stato delle Sperimentazioni

Zion mantiene un registro dettagliato di scoperta per ogni runtime investigato. I documenti di ricerca sono in `specification/experiments/`:

| Esperimento | Runtime | Obiettivo | Stato |
|-------------|---------|-----------|-------|
| #001 | Cheshire Cat | Esplorare lo stato agente portabile | ✅ Completo |
| #002 | DS4 | Valutare DS4 come runtime di orchestrazione | ✅ Completo |
| #003 | Claude Code | Analizzare la gestione dello stato in Claude Code | ✅ Completo |
| #004 | Claude Code | Scoperta completa dello stato con analisi dettagliata | ✅ Completo |

## Dettagli Tecnici

La serializzazione utilizza JSON come formato canonico, garantendo:
- Leggibilità umana
- Determinismo dove pratico
- Indipendenza dalla serializzazione specifica di Python
- Adatto per il versionamento Git

Il nucleo non dipende da alcuna libreria di runtime. Gli adattatori implementano il contratto standard:
- `inspect_state()`: esamina lo stato del runtime
- `export_state()`: estrae lo stato in formato Zion
- `import_state()`: carica uno stato Zion nel runtime
- `measure_recovery()`: confronta due ZionState e misura la fedeltà
- `round_trip_measure()`: esporta → importa → misura in un colpo solo

## Licenza

MIT
