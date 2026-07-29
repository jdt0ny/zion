"""
Il contenitore principale di Zion.

ZionState e' lo stato completo e portabile di un agente AI.
Contiene identita', progetto, conversazione, memorie, decisioni,
task, strumenti, conoscenza, configurazione e runtime.

In questo file c'e' anche inspect_state(), che fa un riepilogo
di tutto lo stato e della sua portabilita'.
"""

from typing import Any

from pydantic import BaseModel, Field

from zion.models import (
    AgentIdentity,
    Decision,
    MemoryEntry,
    Message,
    ProjectState,
    RuntimeState,
    Task,
)


class ZionState(BaseModel):
    """
    Stato completo e portabile di un agente AI.

    Questo e' il cuore di Zion. Ogni campo rappresenta una dimensione
    dello stato dell'agente. I campi con default_factory=list partono
    vuoti se non specificati.

    Nota tecnica: schema_name si chiama "schema" nel JSON finale
    (per via di serialization_alias). Serve a identificare il formato.
    """
    model_config = {"populate_by_name": True}

    schema_name: str = Field(
        default="zion-state",
        serialization_alias="schema",
        validation_alias="schema",
    )
    version: str = "0.1"

    identity: AgentIdentity
    project: ProjectState

    conversation: list[Message] = Field(default_factory=list)
    memory: list[MemoryEntry] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)

    tools: list[dict[str, Any]] = Field(default_factory=list)
    knowledge: list[dict[str, Any]] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)

    runtime: RuntimeState = Field(default_factory=RuntimeState)


def inspect_state(state: ZionState) -> dict:
    """
    Ispeziona lo stato e restituisce un riepilogo.

    Il risultato contiene:
    - identita' e progetto
    - quanti elementi ci sono per ogni dimensione
    - un sommario di portabilita' (portatile / ricostruibile / legato al runtime)
    """
    conta_portabile = 0
    conta_ricostruibile = 0
    conta_legato_al_runtime = 0

    # Conta la portabilita' delle memorie
    for entry in state.memory:
        if entry.portability == "portable":
            conta_portabile += 1
        elif entry.portability == "reconstructable":
            conta_ricostruibile += 1
        else:
            conta_legato_al_runtime += 1

    # Conta la portabilita' delle decisioni
    for decision in state.decisions:
        if decision.portability == "portable":
            conta_portabile += 1
        elif decision.portability == "reconstructable":
            conta_ricostruibile += 1
        else:
            conta_legato_al_runtime += 1

    # Conta la portabilita' dei task
    for task in state.tasks:
        if task.portability == "portable":
            conta_portabile += 1
        elif task.portability == "reconstructable":
            conta_ricostruibile += 1
        else:
            conta_legato_al_runtime += 1

    # Conta la portabilita' del runtime stesso
    if state.runtime.state == "portable":
        conta_portabile += 1
    elif state.runtime.state == "reconstructable":
        conta_ricostruibile += 1
    else:
        conta_legato_al_runtime += 1

    return {
        "identity": state.identity.model_dump(),
        "project": state.project.model_dump(),
        "message_count": len(state.conversation),
        "memory_count": len(state.memory),
        "decision_count": len(state.decisions),
        "task_count": len(state.tasks),
        "tool_count": len(state.tools),
        "knowledge_count": len(state.knowledge),
        "runtime": state.runtime.model_dump(),
        "portability_summary": {
            "portable": conta_portabile,
            "reconstructable": conta_ricostruibile,
            "runtime_bound": conta_legato_al_runtime,
        },
    }
