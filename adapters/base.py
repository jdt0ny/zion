"""
Adattatore base per runtime Zion.

Definisce il contratto standard che ogni adattatore deve implementare.
"""

from abc import ABC, abstractmethod

from zion.state import ZionState


class BaseAdapter(ABC):
    """
    Contratto standard per gli adattatori Zion.

    Ogni adattatore deve implementare i tre metodi:
    - inspect: esamina lo stato disponibile nel runtime
    - export: estrae lo stato in formato ZionState
    - import: carica uno stato Zion nel runtime
    """

    @abstractmethod
    def inspect(self) -> dict:
        """Restituisce un riepilogo dello stato disponibile nel runtime."""

    @abstractmethod
    def export(self) -> ZionState:
        """Estrae lo stato completo del runtime in formato ZionState."""

    @abstractmethod
    def import_state(self, state: ZionState) -> None:
        """Carica uno stato Zion nel runtime."""
