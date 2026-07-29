"""
Utility per la gestione dei file su disco.
"""

from pathlib import Path


def ensure_directory(path: Path) -> Path:
    """Crea la cartella del file se non esiste e restituisce il path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
