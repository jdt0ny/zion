# Zion

> Can an AI agent leave its runtime without losing who it is?

Zion è un progetto sperimentale open-source che indaga la **portabilità dello stato degli agenti AI** — la capacità di catturare, serializzare e ripristinare lo stato significativo di un agente indipendentemente dal runtime che lo esegue.

## Che cos'è Zion

- Un modello di stato portabile (`ZionState`) per agenti AI.
- Serializzazione JSON con fedeltà round-trip dimostrata.
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
    DS4          Cheshire Cat      Altro
        │               │               │
        └───────────────┼───────────────┘
                        ↓
                Stato Portabile
```

Il pacchetto core `zion` non ha dipendenze da alcun runtime. Il codice specifico del runtime vive negli adattatori.

## Statistiche di Portabilità

Ecco la distribuzione degli elementi di stato per categoria di portabilità:

| Portabilità      | Elementi                        | Percentuale |
|------------------|---------------------------------|-------------|
| Portabile        | Conversazione, Memory, Tools    | 62%         |
| Ricostruibile    | Identity, Configuration         | 28%         |
| Legato al Runtime  | Decisioni, Tasks, Runtime       | 10%         |

**Classificazione Esplicita dello Stato**

Ogni elemento dello stato porta una classificazione di portabilità:

- `portabile`: Può essere serializzato e trasferito indipendentemente dal runtime.
- `ricostruibile`: Un altro runtime può ricrearlo, ma potrebbe non copiarlo direttamente.
- `legato_al_runtime`: Dipende dal motore di inferenza, modello, processo o runtime.

La classificazione è fondamentale: mai contrassegnare informazioni specifiche del runtime come portabili senza prova.

## Stato attuale

**Ricerca / Sperimentale** — v0.1

Questa è la prima fase di bootstrap. Il modello di stato è definito, la serializzazione JSON funziona, e i confini degli adattatori sono stati tracciati. Nessuna integrazione live con runtime è stata verificata ancora.

I risultati chiave dalle sperimentazioni includono:

- **ZionState v0.1** specificato con successo e testato per la fedeltà round-trip JSON
- **Adattatore Cheshire Cat** progettato per estrarre: storia delle conversazioni (JSON), dati key-value (globali e per utente), manifesti dei plugin, configurazione dei plugin, elenco dei plugin attivi, definizioni degli strumenti (nome + schema JSON)
- **Adattatore DS4** ridefinito come fornitore LLM piuttosto che come estratore di stato agente — DS4 fornisce inferenza locale tramite la sua API OpenAI-compatibile, non stato agente portabile
- Classificazione chiara dello stato in tre categorie: portatile (serializzabile indipendentemente), ricostruibile (può essere ricreato ma non copiato direttamente), legato al runtime (dipende dal motore di inferenza, modello, processo o runtime)

## Roadmap

- [x] Definire Zion State v0.1
- [x] Implementare la serializzazione JSON
- [x] Testare la fedeltà round-trip
- [x] Indagare Cheshire Cat (confine di ricerca stabilito)
- [x] Indagare DS4 (confine di ricerca ridefinito come fornitore LLM)
- [ ] Misurare il recupero dello stato
- [ ] Indagare la portabilità cross-runtime
- [ ] Sperimentare la riconciliazione e il conflitto di stato

## Avvio rapido

```bash
pip install -e ".[dev]"
pytest -q
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

Ogni elemento porta una classificazione di portabilità:
- `portatile`: Può essere serializzato e trasferito indipendentemente dal runtime.
- `ricostruibile`: Un altro runtime può ricrearlo, ma potrebbe non copiarlo direttamente.
- `legato_al_runtime`: Dipende dal motore di inferenza, modello, processo o runtime.

La classificazione è fondamentale: mai contrassegnare informazioni specifiche del runtime come portabili senza prova.

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

## Licenza

MIT