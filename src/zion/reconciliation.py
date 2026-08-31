"""
Riconciliazione conflitti di stato Zion.

Strategie per risolvere conflitti quando si migra lo stato
tra runtime diversi.

Strategie disponibili:
  - overwrite: sovrascrive lo stato destinazione con quello sorgente
  - merge: unisce gli stati (per collection)
  - keep_target: mantiene lo stato del destinazione
  - keep_source: mantiene lo stato del sorgente
  - manual: richiede decisione manuale
"""

from typing import Any, Callable

from zion.migration import Conflict
from zion.models import MemoryEntry
from zion.state import ZionState


def overwrite_strategy(
    source_state: ZionState,
    target_state: ZionState | None,
    conflicts: list[Conflict],
) -> ZionState:
    """Sovrascrive tutto con lo stato sorgente."""
    return source_state


def keep_target_strategy(
    source_state: ZionState,
    target_state: ZionState | None,
    conflicts: list[Conflict],
) -> ZionState:
    """Mantiene lo stato del destinazione (scarta il sorgente)."""
    if target_state is None:
        return source_state
    return target_state


def merge_strategy(
    source_state: ZionState,
    target_state: ZionState | None,
    conflicts: list[Conflict],
) -> ZionState:
    """Unisce gli stati, preferendo il sorgente per i conflitti."""
    if target_state is None:
        return source_state

    result = target_state.model_dump()

    # Merge conversation: concatena, deduplica per contenuto
    source_msgs = [m.model_dump() for m in source_state.conversation]
    target_msgs = [m.model_dump() for m in target_state.conversation]
    seen = set()
    merged_msgs = []
    for msg in target_msgs + source_msgs:
        key = (msg.get("role"), msg.get("content"))
        if key not in seen:
            seen.add(key)
            merged_msgs.append(msg)
    result["conversation"] = merged_msgs

    # Merge memory: unisci per ID, preferisci sorgente
    source_mem = {m.id: m.model_dump() for m in source_state.memory}
    target_mem = {m.id: m.model_dump() for m in target_state.memory}
    target_mem.update(source_mem)
    result["memory"] = list(target_mem.values())

    # Merge decisions: concatena, deduplica per ID
    source_dec = {d.id: d.model_dump() for d in source_state.decisions}
    target_dec = {d.id: d.model_dump() for d in target_state.decisions}
    target_dec.update(source_dec)
    result["decisions"] = list(target_dec.values())

    # Merge tasks: concatena, deduplica per ID
    source_tasks = {t.id: t.model_dump() for t in source_state.tasks}
    target_tasks = {t.id: t.model_dump() for t in target_state.tasks}
    target_tasks.update(source_tasks)
    result["tasks"] = list(target_tasks.values())

    # Merge tools: unisci per nome, preferisci sorgente
    source_tools = {t.get("name"): t for t in source_state.tools}
    target_tools = {t.get("name"): t for t in target_state.tools}
    target_tools.update(source_tools)
    result["tools"] = list(target_tools.values())

    # Merge configuration: unisci chiavi, preferisci sorgente
    merged_config = {**target_state.configuration, **source_state.configuration}
    result["configuration"] = merged_config

    return ZionState.model_validate(result)


def selective_merge_strategy(
    source_state: ZionState,
    target_state: ZionState | None,
    conflicts: list[Conflict],
    prefer_dimensions: list[str] | None = None,
) -> ZionState:
    """Merge selettivo: preferisce il sorgente solo per le dimensioni specificate."""
    if prefer_dimensions is None:
        prefer_dimensions = []

    if target_state is None:
        return source_state

    result = target_state.model_dump()

    for conflict in conflicts:
        dim = conflict.dimension.split(".")[0]

        if dim in prefer_dimensions:
            # Applica dal sorgente
            if dim == "identity":
                result["identity"] = source_state.identity.model_dump()
            elif dim == "conversation":
                result["conversation"] = [
                    m.model_dump() for m in source_state.conversation
                ]
            elif dim == "memory":
                source_mem = {
                    m.id: m.model_dump() for m in source_state.memory
                }
                target_mem = {
                    m.id: m.model_dump() for m in target_state.memory
                }
                target_mem.update(source_mem)
                result["memory"] = list(target_mem.values())
            elif dim == "configuration":
                result["configuration"] = {
                    **target_state.configuration,
                    **source_state.configuration,
                }

    return ZionState.model_validate(result)


# Registry delle strategie disponibili
STRATEGIES: dict[str, Callable] = {
    "overwrite": overwrite_strategy,
    "keep_target": keep_target_strategy,
    "merge": merge_strategy,
}


def get_strategy(name: str) -> Callable:
    """Restituisce una strategia per nome."""
    if name not in STRATEGIES:
        raise ValueError(
            f"Strategia sconosciuta: {name}. "
            f"Disponibili: {', '.join(STRATEGIES.keys())}"
        )
    return STRATEGIES[name]


def reconcile(
    source_state: ZionState,
    target_state: ZionState | None,
    conflicts: list[Conflict],
    strategy: str = "merge",
    **kwargs,
) -> ZionState:
    """
    Risolve i conflitti usando la strategia specificata.

    Parametri:
        source_state: stato dal runtime sorgente
        target_state: stato attuale del runtime destinazione (puo' essere None)
        conflicts: lista di conflitti rilevati
        strategy: nome della strategia da usare
        kwargs: argomenti aggiuntivi per la strategia

    Returns:
        ZionState risolto
    """
    fn = get_strategy(strategy)
    return fn(source_state, target_state, conflicts, **kwargs)
