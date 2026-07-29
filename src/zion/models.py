"""
Modelli dati di Zion.

Qui vivono i mattoncini che compongono lo stato di un agente AI:
memorie, decisioni, task, messaggi, identita', progetto e runtime.

Ogni elemento ha una classificazione di portabilita':
- portable:   si puo' salvare e spostare liberamente
- reconstructable: ricostruibile, ma non copiabile direttamente
- runtime_bound:  legato al motore che esegue l'agente
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# I tre livelli di portabilita' possibili
Portability = Literal["portable", "reconstructable", "runtime_bound"]


class MemoryEntry(BaseModel):
    """Un ricordo dell'agente: un fatto, un appunto, un'esperienza."""
    id: str
    content: str
    created_at: datetime
    updated_at: datetime | None = None
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
