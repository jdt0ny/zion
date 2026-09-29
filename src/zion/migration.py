"""
Migrazione cross-runtime per Zion.

Permette di spostare lo stato di un agente da un runtime all'altro,
gestendo le incompatibilita' e i conflitti.

Flusso:
  1. Export dal runtime sorgente -> ZionState
  2. Analisi compatibilita' con il runtime destinazione
  3. Riconciliazione conflitti (se richiesto)
  4. Transformazione per adattarsi al runtime destinazione
  5. Import nel runtime destinazione
"""

from dataclasses import dataclass, field
from typing import Any

from adapters.base import BaseAdapter
from zion.state import ZionState


@dataclass
class MigrationReport:
    """Rapporto di migrazione tra runtime."""
    source_runtime: str
    target_runtime: str
    dimensions_migrated: list[str] = field(default_factory=list)
    dimensions_skipped: list[str] = field(default_factory=list)
    dimensions_transformed: list[str] = field(default_factory=list)
    conflicts_found: list[dict] = field(default_factory=list)
    conflicts_resolved: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    success: bool = False


@dataclass
class Conflict:
    """Conflitto tra stato sorgente e destinazione."""
    dimension: str
    source_value: Any
    target_value: Any
    conflict_type: str  # "overwrite", "merge", "skip"


# Mappa di compatibilita' per dimensione
# True = portabile direttamente, False = non trasferibile
DIMENSION_COMPATIBILITY = {
    "identity": {
        "cheshire_cat": True,
        "ds4": True,
    },
    "conversation": {
        "cheshire_cat": True,
        "ds4": False,  # DS4 non persiste conversazioni
    },
    "memory": {
        "cheshire_cat": True,
        "ds4": False,  # DS4 non ha sistema di memoria
    },
    "decisions": {
        "cheshire_cat": False,  # CC non ha sistema di decisioni
        "ds4": False,
    },
    "tasks": {
        "cheshire_cat": False,  # CC non ha sistema di task
        "ds4": False,
    },
    "tools": {
        "cheshire_cat": True,
        "ds4": True,
    },
    "knowledge": {
        "cheshire_cat": False,
        "ds4": False,
    },
    "configuration": {
        "cheshire_cat": True,
        "ds4": True,
    },
    "runtime": {
        "cheshire_cat": True,
        "ds4": True,
    },
}


def check_compatibility(
    state: ZionState,
    target_runtime: str,
) -> dict[str, bool]:
    """
    Verifica la compatibilita' di uno stato con un runtime destinazione.

    Restituisce un dict dimensione -> compatibile. Un runtime destinazione
    assente dalla tabella ma uguale a quello corrente dello stato viene
    considerato compatibile: non c'e' nessuna migrazione da fare.
    """
    result = {}
    source_runtime = state.runtime.engine

    for dimension in DIMENSION_COMPATIBILITY:
        target_compat = DIMENSION_COMPATIBILITY.get(dimension, {})
        if target_runtime in target_compat:
            result[dimension] = target_compat[target_runtime]
        elif target_runtime == source_runtime:
            result[dimension] = True
        else:
            # Runtime sconosciuto: conservativo, marca come non compatibile
            result[dimension] = False

    return result


def detect_conflicts(
    source_state: ZionState,
    target_state: ZionState | None,
) -> list[Conflict]:
    """
    Rileva conflitti tra lo stato sorgente e lo stato attuale
    del runtime destinazione.

    Se target_state e' None, non ci sono conflitti.
    """
    if target_state is None:
        return []

    conflicts = []

    # Confronta identity
    if source_state.identity.agent_id != target_state.identity.agent_id:
        conflicts.append(Conflict(
            dimension="identity.agent_id",
            source_value=source_state.identity.agent_id,
            target_value=target_state.identity.agent_id,
            conflict_type="overwrite",
        ))

    # Confronta conversazioni
    if (source_state.conversation and target_state.conversation):
        conflicts.append(Conflict(
            dimension="conversation",
            source_value=f"{len(source_state.conversation)} messaggi",
            target_value=f"{len(target_state.conversation)} messaggi",
            conflict_type="merge",
        ))

    # Confronta memoria
    if source_state.memory and target_state.memory:
        source_keys = {m.id for m in source_state.memory}
        target_keys = {m.id for m in target_state.memory}
        overlapping = source_keys & target_keys
        if overlapping:
            conflicts.append(Conflict(
                dimension="memory",
                source_value=f"{len(source_keys)} voci",
                target_value=f"{len(target_keys)} voci",
                conflict_type="merge",
            ))

    # Confronta tool
    if source_state.tools and target_state.tools:
        source_names = {t.get("name") for t in source_state.tools}
        target_names = {t.get("name") for t in target_state.tools}
        overlapping = source_names & target_names
        if overlapping:
            conflicts.append(Conflict(
                dimension="tools",
                source_value=f"{len(source_names)} tool",
                target_value=f"{len(target_names)} tool",
                conflict_type="overwrite",
            ))

    # Confronta configurazione
    if source_state.configuration and target_state.configuration:
        overlapping = set(source_state.configuration) & set(target_state.configuration)
        if overlapping:
            conflicts.append(Conflict(
                dimension="configuration",
                source_value=f"{len(source_state.configuration)} chiavi",
                target_value=f"{len(target_state.configuration)} chiavi",
                conflict_type="merge",
            ))

    return conflicts


def transform_for_target(
    state: ZionState,
    target_runtime: str,
    compatibility: dict[str, bool],
) -> ZionState:
    """
    Trasforma uno stato per essere compatibile con il runtime destinazione.

    Le dimensioni non compatibili vengono svuotate.
    """
    data = state.model_dump()

    # Svuota le dimensioni non compatibili
    for dimension, compatible in compatibility.items():
        if not compatible:
            if dimension == "conversation":
                data["conversation"] = []
            elif dimension == "memory":
                data["memory"] = []
            elif dimension == "decisions":
                data["decisions"] = []
            elif dimension == "tasks":
                data["tasks"] = []
            elif dimension == "knowledge":
                data["knowledge"] = []

    # Aggiorna il runtime
    data["runtime"]["engine"] = target_runtime

    return ZionState.model_validate(data)


def migrate(
    source: BaseAdapter,
    target: BaseAdapter,
    resolve_conflicts_fn=None,
) -> MigrationReport:
    """
    Esegue una migrazione completa tra due runtime.

    Parametri:
        source: adattatore del runtime sorgente
        target: adattatore del runtime destinazione
        resolve_conflicts_fn: funzione opzionale per risolvere i conflitti.
            Accetta (source_state, target_state, conflicts) e restituisce
            lo stato risolto.

    Returns:
        MigrationReport con il risultato della migrazione.
    """
    report = MigrationReport(
        source_runtime=source.inspect().get("runtime", "unknown"),
        target_runtime=target.inspect().get("runtime", "unknown"),
    )

    # 1. Export dal sorgente
    try:
        source_state = source.export()
    except Exception as e:
        report.warnings.append(f"Export fallito: {e}")
        return report

    # 2. Verifica compatibilita'
    compatibility = check_compatibility(source_state, report.target_runtime)
    for dim, compat in compatibility.items():
        if compat:
            report.dimensions_migrated.append(dim)
        else:
            report.dimensions_skipped.append(dim)
            report.warnings.append(
                f"Dimensione '{dim}' non compatibile con {report.target_runtime}"
            )

    # 3. Rileva conflitti
    try:
        target_state = target.export()
    except Exception:
        target_state = None

    conflicts = detect_conflicts(source_state, target_state)
    report.conflicts_found = [
        {"dimension": c.dimension, "type": c.conflict_type}
        for c in conflicts
    ]

    # 4. Risolvi conflitti
    if resolve_conflicts_fn and conflicts:
        try:
            source_state = resolve_conflicts_fn(
                source_state, target_state, conflicts
            )
            report.conflicts_resolved = report.conflicts_found
        except Exception as e:
            report.warnings.append(f"Risoluzione conflitti fallita: {e}")

    # 5. Trasforma per il destinazione
    transformed = transform_for_target(
        source_state, report.target_runtime, compatibility
    )
    report.dimensions_transformed = [
        d for d, c in compatibility.items() if not c
    ]

    # 6. Import nel destinazione
    try:
        target.import_state(transformed)
        report.success = True
    except Exception as e:
        report.warnings.append(f"Import fallito: {e}")

    return report
