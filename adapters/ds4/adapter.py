"""
Adattatore per DS4 (di Salvatore Sanfilippo).

STATO: CONFINE DI RICERCA

Nessuna delle dimensioni di stato qui sotto e' stata verificata
su un'istanza reale di DS4. Servono esperimenti pratici.

Dimensione       Stato     Note
session          SCONOSCIUTO  serve un'istanza reale
conversation     SCONOSCIUTO  serve un'istanza reale
model            SCONOSCIUTO  serve un'istanza reale
tool metadata    SCONOSCIUTO  serve un'istanza reale
KV/session state SCONOSCIUTO  serve un'istanza reale
runtime          SCONOSCIUTO  serve un'istanza reale

Attenzione: la KV cache di DS4 NON va trattata come portabile.
"""

from zion.state import ZionState


class DS4Adapter:
    """
    Adattatore DS4.

    I tre metodi sono il contratto standard per tutti gli adattatori Zion:
    - inspect_state: esamina lo stato del runtime
    - export_state: estrae lo stato in formato Zion
    - import_state: carica uno stato Zion nel runtime
    """

    def inspect_state(self) -> dict:
        raise NotImplementedError(
            "Serve un'ispezione su un'istanza reale di DS4. "
            "Vedi il docstring del modulo."
        )

    def export_state(self) -> ZionState:
        raise NotImplementedError(
            "Serve un'ispezione su un'istanza reale di DS4. "
            "Vedi il docstring del modulo."
        )

    def import_state(self, state: ZionState) -> None:
        raise NotImplementedError(
            "Serve un'ispezione su un'istanza reale di DS4. "
            "Vedi il docstring del modulo."
        )
