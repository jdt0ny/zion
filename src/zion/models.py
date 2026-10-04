"""
Modelli dati di Zion.

Qui vivono i mattoncini che compongono lo stato di un agente AI:
memorie, conoscenza, decisioni, task, messaggi, identita', progetto e
runtime.

Ogni elemento ha una classificazione di portabilita':
- portable:   si puo' salvare e spostare liberamente
- reconstructable: ricostruibile, ma non copiabile direttamente
- runtime_bound:  legato al motore che esegue l'agente
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# I tre livelli di portabilita' possibili
Portability = Literal["portable", "reconstructable", "runtime_bound"]

# Tipi di relazione tra due ricordi
MemoryRelation = Literal["caused_by", "follows", "same_topic", "contradicts"]


class MemoryLink(BaseModel):
    """Un legame strutturato da un ricordo a un altro.

    target puo' puntare a un ricordo assente nell'export corrente:
    e' un caso lecito (export parziale) e viene contato da inspect_state.
    """
    target: str
    relation: MemoryRelation


class MemoryEntry(BaseModel):
    """Un ricordo episodico: cosa e' successo, quando, con quale salienza.

    created_at  = quando il ricordo e' stato scritto.
    occurred_at = quando l'evento e' successo (non puo' essere futuro).
    salience    = 0..1, quanto il ricordo conta.
    """
    id: str
    content: str
    created_at: datetime
    occurred_at: datetime
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    context: str | None = None
    links: list[MemoryLink] = Field(default_factory=list)
    updated_at: datetime | None = None
    portability: Portability = "portable"

    @model_validator(mode="before")
    @classmethod
    def backfill_occurred_at(cls, data: Any) -> Any:
        """Uno stato v0.1 non ha occurred_at: si allinea a created_at."""
        if isinstance(data, dict) and "occurred_at" not in data:
            data = {**data, "occurred_at": data.get("created_at")}
        return data

    @model_validator(mode="after")
    def check_occurred_before_created(self) -> "MemoryEntry":
        if self.occurred_at > self.created_at:
            raise ValueError("occurred_at non puo' essere successivo a created_at")
        return self


class KnowledgeEntry(BaseModel):
    """Un fatto: conoscenza dichiarativa, non episodica.

    Non ha occurred_at (un fatto non e' legato a un momento) ne' salience.
    I campi extra sono conservati: le voci legacy sono dizionari liberi
    e perderli sarebbe una perdita di fedelta'.
    """
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    content: str
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime | None = None
    portability: Portability = "portable"


class Decision(BaseModel):
    """Una decisione presa dall'agente o per l'agente."""
    id: str
    title: str
    decision: str
    created_at: datetime
    portability: Portability = "portable"


class Task(BaseModel):
    """Un'attivita' in corso o futura."""
    id: str
    title: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    created_at: datetime
    portability: Portability = "portable"


class Message(BaseModel):
    """Un messaggio dello scambio conversazionale."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    created_at: datetime


class AgentIdentity(BaseModel):
    """Chi e' l'agente: ID, nome, versione."""
    agent_id: str
    name: str
    version: str


class ProjectState(BaseModel):
    """A quale progetto appartiene l'agente."""
    id: str
    name: str
    repository: str | None = None
    description: str = ""


class RuntimeState(BaseModel):
    """Che motore sta eseguendo l'agente in questo momento."""
    engine: str | None = None
    model: str | None = None
    state: Portability = "reconstructable"
