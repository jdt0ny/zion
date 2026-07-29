"""
Salva lo stato di un agente Zion su disco in formato JSON.

Il JSON prodotto e':
- leggibile dall'uomo (indentato)
- deterministico (stessi dati = stesso JSON)
- indipendente da Python (si puo' aprire con qualsiasi linguaggio)
- adatto per Git (differenze chiare tra versioni)
"""

import json
from pathlib import Path

from zion.state import ZionState


def export_state(state: ZionState, path: Path) -> None:
    """
    Esporta uno ZionState in un file JSON.

    Crea la cartella se non esiste. Usa by_alias=True perche'
    alcuni campi (es. schema_name) hanno un nome diverso nel JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = state.model_dump(mode="json", by_alias=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
