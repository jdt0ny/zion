"""
Carica lo stato di un agente Zion da un file JSON.

L'operazione inversa di export_state.
"""

import json
from pathlib import Path

from zion.state import ZionState


def import_state(path: Path) -> ZionState:
    """
    Legge un file JSON e ricostruisce uno ZionState.

    Lancia un'eccezione se il file non esiste o se il JSON
    non corrisponde allo schema ZionState.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ZionState.model_validate(data)
