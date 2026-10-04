"""
Zion — Stato portabile per agenti AI.

Uso tipico:

    from zion import ZionState, export_state, import_state, inspect_state
"""

from zion.export import export_state
from zion.import_ import import_state
from zion.models import (
    AgentIdentity,
    Decision,
    KnowledgeEntry,
    MemoryEntry,
    MemoryLink,
    Message,
    Portability,
    ProjectState,
    RuntimeState,
    Task,
)
from zion.recovery import RecoveryReport, measure_recovery, round_trip_measure
from zion.state import ZionState, inspect_state

__all__ = [
    "AgentIdentity",
    "Decision",
    "KnowledgeEntry",
    "MemoryEntry",
    "MemoryLink",
    "Message",
    "Portability",
    "ProjectState",
    "RuntimeState",
    "Task",
    "ZionState",
    "export_state",
    "import_state",
    "inspect_state",
    "RecoveryReport",
    "measure_recovery",
    "round_trip_measure",
    "MigrationReport",
    "migrate",
    "check_compatibility",
    "reconcile",
]


def __getattr__(name):
    if name == "MigrationReport":
        from zion.migration import MigrationReport
        return MigrationReport
    if name == "migrate":
        from zion.migration import migrate
        return migrate
    if name == "check_compatibility":
        from zion.migration import check_compatibility
        return check_compatibility
    if name == "reconcile":
        from zion.reconciliation import reconcile
        return reconcile
    raise AttributeError(f"module 'zion' has no attribute '{name}'")
