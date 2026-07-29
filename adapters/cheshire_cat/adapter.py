"""
Adattatore per Cheshire Cat AI.

STATO: CONFINE DI RICERCA

Nessuna delle dimensioni di stato qui sotto e' stata verificata
su un'istanza reale di Cheshire Cat. Servono esperimenti pratici.

Dimensione       Stato     Note
identity         SCONOSCIUTO  serve un'istanza reale
conversation     SCONOSCIUTO  serve un'istanza reale
memory           SCONOSCIUTO  serve un'istanza reale
decisions        SCONOSCIUTO  serve un'istanza reale
tasks            SCONOSCIUTO  serve un'istanza reale
tools            SCONOSCIUTO  serve un'istanza reale
knowledge        SCONOSCIUTO  serve un'istanza reale
configuration    SCONOSCIUTO  serve un'istanza reale
runtime          SCONOSCIUTO  serve un'istanza reale

Non dichiariamo compatibilita' con API inesistenti.
"""

from zion.state import ZionState


class CheshireCatAdapter:
    """
    Adattatore Cheshire Cat.

    I tre metodi sono il contratto standard per tutti gli adattatori Zion:
    - inspect_state: esamina lo stato del runtime
    - export_state: estrae lo stato in formato Zion
    - import_state: carica uno stato Zion nel runtime
    """

    def inspect_state(self) -> dict:
        raise NotImplementedError(
            "Serve un'ispezione su un'istanza reale di Cheshire Cat. "
            "Vedi il docstring del modulo."
        )

    def export_state(self) -> ZionState:
        raise NotImplementedError(
            "Serve un'ispezione su un'istanza reale di Cheshire Cat. "
            "Vedi il docstring del modulo."
        )

    def import_state(self, state: ZionState) -> None:
        raise NotImplementedError(
            "Serve un'ispezione su un'istanza reale di Cheshire Cat. "
            "Vedi il docstring del modulo."
        )
