"""
Misurazione del recupero dello stato Zion.

Misura quantitativamente quanto bene uno stato ZionState sopravvive
al round-trip JSON (export → import), producendo un report leggibile
con fedelta' per dimensione e un punteggio complessivo.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from zion.export import export_state
from zion.import_ import import_state
from zion.state import ZionState


@dataclass
class RecoveryReport:
    """
    Report quantitativo del recupero dello stato.

    Contiene:
    - overall_fidelity: punteggio complessivo (0.0 = perso, 1.0 = perfetto)
    - per_dimension: fedelta' per ogni dimensione dello stato
    - total_bytes: dimensione del JSON serializzato
    - fields_checked: totale campi verificati
    - fields_recovered: campi che sopravvivono al round-trip
    - field_losses: lista di percorsi dei campi persi
    - portability: distribuzione delle classi di portabilita'
    """
    overall_fidelity: float = 0.0
    per_dimension: dict[str, float] = field(default_factory=dict)
    total_bytes: int = 0
    fields_checked: int = 0
    fields_recovered: int = 0
    field_losses: list[str] = field(default_factory=list)
    portability: dict[str, int] = field(default_factory=dict)


def _count_portability(state: ZionState) -> dict[str, int]:
    """Conta gli elementi per classe di portabilita'."""
    counts = {"portable": 0, "reconstructable": 0, "runtime_bound": 0}

    for entry in state.memory:
        counts[entry.portability] = counts.get(entry.portability, 0) + 1
    for decision in state.decisions:
        counts[decision.portability] = counts.get(decision.portability, 0) + 1
    for task in state.tasks:
        counts[task.portability] = counts.get(task.portability, 0) + 1

    rs = state.runtime.state
    counts[rs] = counts.get(rs, 0) + 1

    return counts


def _count_leaves(value: Any) -> int:
    """
    Conta quanti campi foglia ha un valore annidato.

    - dict: somma i leaves di tutti i valori
    - list: somma i leaves di tutti gli elementi
    - scalare: 1
    """
    if isinstance(value, dict):
        return sum(_count_leaves(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_count_leaves(item) for item in value)
    return 1


def _normalize_datetime(value: Any) -> Any:
    """
    Normalizza un datetime al secondo per confronto tollerante.

    Se il valore e' un datetime, tronca i microsecondi.
    Altrimenti restituisce il valore cosi' com'e'.
    """
    if isinstance(value, datetime):
        return value.replace(microsecond=0)
    return value


def _deep_compare(a: Any, b: Any, path: str) -> tuple[int, int, list[str]]:
    """
    Confronto ricorsivo tra due valori.

    Restituisce (checked, recovered, losses).
    I conteggi sono sempre "foglia" — ogni valore scalare conta come 1.
    Le chiavi/liste mancanti contano i leaves del valore mancante.
    I datetime vengono confrontati al secondo (toleranza ai microsecondi).
    """
    losses: list[str] = []

    if type(a) is not type(b):
        return 1, 0, [path]

    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        checked = 0
        recovered = 0
        for key in sorted(all_keys):
            sub_path = f"{path}.{key}" if path else str(key)
            if key not in a:
                c = _count_leaves(b[key])
                checked += c
                losses.append(sub_path)
            elif key not in b:
                c = _count_leaves(a[key])
                checked += c
                losses.append(sub_path)
            else:
                c, r, lost = _deep_compare(a[key], b[key], sub_path)
                checked += c
                recovered += r
                losses.extend(lost)
        return checked, recovered, losses

    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            checked = (
                sum(_count_leaves(item) for item in a)
                + sum(_count_leaves(item) for item in b)
            )
            return checked, 0, [f"{path} (length {len(a)} → {len(b)})"]
        checked = 0
        recovered = 0
        for i, (item_a, item_b) in enumerate(zip(a, b, strict=False)):
            sub_path = f"{path}[{i}]"
            c, r, lost = _deep_compare(item_a, item_b, sub_path)
            checked += c
            recovered += r
            losses.extend(lost)
        return checked, recovered, losses

    # Valore scalare — confronto con tolleranza ai microsecondi
    norm_a = _normalize_datetime(a)
    norm_b = _normalize_datetime(b)
    if norm_a == norm_b:
        return 1, 1, []

    return 1, 0, [path]


def measure_recovery(original: ZionState, recovered: ZionState) -> RecoveryReport:
    """
    Confronta due ZionState e misura la fedelta' del recupero.

    Calcola la fedelta' per ogni dimensione, il punteggio complessivo,
    e raccoglie informazioni sui campi persi.
    """
    report = RecoveryReport()

    dimensions = [
        ("identity", original.identity.model_dump(), recovered.identity.model_dump()),
        ("project", original.project.model_dump(), recovered.project.model_dump()),
        ("conversation", [m.model_dump() for m in original.conversation],
         [m.model_dump() for m in recovered.conversation]),
        ("memory", [m.model_dump() for m in original.memory],
         [m.model_dump() for m in recovered.memory]),
        ("decisions", [d.model_dump() for d in original.decisions],
         [d.model_dump() for d in recovered.decisions]),
        ("tasks", [t.model_dump() for t in original.tasks],
         [t.model_dump() for t in recovered.tasks]),
        ("tools", original.tools, recovered.tools),
        ("knowledge", [k.model_dump() for k in original.knowledge],
         [k.model_dump() for k in recovered.knowledge]),
        ("configuration", original.configuration, recovered.configuration),
        ("runtime", original.runtime.model_dump(), recovered.runtime.model_dump()),
    ]

    total_checked = 0
    total_recovered = 0

    for name, orig, recov in dimensions:
        c, r, losses = _deep_compare(orig, recov, name)
        total_checked += c
        total_recovered += r
        report.field_losses.extend(losses)

        if c > 0:
            report.per_dimension[name] = r / c
        else:
            report.per_dimension[name] = 1.0

    report.fields_checked = total_checked
    report.fields_recovered = total_recovered
    report.overall_fidelity = total_recovered / total_checked if total_checked > 0 else 1.0
    report.portability = _count_portability(original)

    return report


def round_trip_measure(state: ZionState, path: Path) -> RecoveryReport:
    """
    Esegue un round-trip completo (export → import) e misura la fedelta'.

    Salva lo stato in JSON, lo ricarica, e confronta con l'originale.
    Restituisce un RecoveryReport con tutti i punteggi.
    """
    export_state(state, path)
    total_bytes = path.stat().st_size

    recovered = import_state(path)
    report = measure_recovery(state, recovered)
    report.total_bytes = total_bytes

    return report
