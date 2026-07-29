"""
Tracciamento eventi del ciclo di vita dello stato.

TODO: Questo modulo e' un abbozzo. In futuro registrera' ogni
operazione su ZionState (esportazione, importazione, modifica).
"""

from datetime import datetime


class StateEvent:
    """
    Un singolo evento nella vita di uno stato Zion.

    kind: il tipo di evento (es. "export", "import", "modify")
    description: descrizione leggibile dell'evento
    timestamp: quando e' successo
    """
    kind: str
    description: str
    timestamp: datetime

    def __init__(self, kind: str, description: str) -> None:
        self.kind = kind
        self.description = description
        self.timestamp = datetime.now()
