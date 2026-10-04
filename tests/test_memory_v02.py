"""Memoria episodica v0.2: struttura, vincoli e compatibilita' con v0.1."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from zion.export import export_state
from zion.import_ import import_state
from zion.models import AgentIdentity, KnowledgeEntry, MemoryEntry, MemoryLink, ProjectState
from zion.recovery import measure_recovery
from zion.state import ZionState, inspect_state

T0 = "2026-01-01T00:00:00"
T1 = "2026-01-01T00:00:01"


def _memory(**overrides) -> dict:
    base = {
        "id": "m1",
        "content": "Ho deciso di usare uv per Zion",
        "created_at": T1,
        "occurred_at": T0,
        "salience": 0.9,
        "context": "sessione di lavoro del 29/09",
    }
    base.update(overrides)
    return base


def _state(**overrides) -> ZionState:
    base = {
        "identity": AgentIdentity(agent_id="a1", name="test", version="1.0"),
        "project": ProjectState(id="p1", name="test-project"),
    }
    base.update(overrides)
    return ZionState(**base)


class TestEpisodicFields:
    def test_all_new_fields_survive_round_trip(self, tmp_path):
        memory = MemoryEntry.model_validate(
            _memory(links=[{"target": "m0", "relation": "caused_by"}])
        )
        state = _state(memory=[memory])

        path = tmp_path / "state.json"
        export_state(state, path)
        reloaded = import_state(path)

        assert measure_recovery(state, reloaded).overall_fidelity == 1.0
        reloaded_memory = reloaded.memory[0]
        assert reloaded_memory.occurred_at == datetime.fromisoformat(T0)
        assert reloaded_memory.salience == 0.9
        assert reloaded_memory.context == "sessione di lavoro del 29/09"
        assert reloaded_memory.links == [
            MemoryLink(target="m0", relation="caused_by")
        ]

    def test_links_preserve_order(self):
        memory = MemoryEntry.model_validate(
            _memory(
                links=[
                    {"target": "mA", "relation": "follows"},
                    {"target": "mB", "relation": "same_topic"},
                ]
            )
        )
        assert [link.target for link in memory.links] == ["mA", "mB"]

    def test_salience_bounds(self):
        assert MemoryEntry.model_validate(_memory(salience=0.0)).salience == 0.0
        assert MemoryEntry.model_validate(_memory(salience=1.0)).salience == 1.0

        for value in (-0.1, 1.5):
            with pytest.raises(ValidationError):
                MemoryEntry.model_validate(_memory(salience=value))

    def test_unknown_relation_rejected(self):
        with pytest.raises(ValidationError):
            MemoryEntry.model_validate(
                _memory(links=[{"target": "m0", "relation": "qualunque"}])
            )

    def test_occurred_after_created_rejected(self):
        with pytest.raises(ValidationError):
            MemoryEntry.model_validate(_memory(occurred_at=T1, created_at=T0))

    def test_salience_defaults_to_half(self):
        memory = MemoryEntry.model_validate(
            {"id": "m1", "content": "senza salienza", "created_at": T1}
        )
        assert memory.salience == 0.5


class TestBackwardCompatibility:
    def test_v01_memory_backfills_occurred_at(self):
        memory = MemoryEntry.model_validate(
            {"id": "m1", "content": "vecchio formato", "created_at": T1}
        )
        assert memory.occurred_at == datetime.fromisoformat(T1)
        assert memory.context is None
        assert memory.links == []

    def test_v01_state_keeps_fidelity_1(self, tmp_path):
        raw = {
            "schema": "zion-state",
            "version": "0.1",
            "identity": {"agent_id": "a1", "name": "test", "version": "1.0"},
            "project": {"id": "p1", "name": "test-project"},
            "memory": [
                {
                    "id": "m1",
                    "content": "ricordo vecchio",
                    "created_at": T1,
                    "portability": "portable",
                }
            ],
            "knowledge": [{"topic": "python", "content": "Python e' un linguaggio"}],
        }
        original = ZionState.model_validate(raw)

        path = tmp_path / "state.json"
        export_state(original, path)
        reloaded = import_state(path)

        assert measure_recovery(original, reloaded).overall_fidelity == 1.0
        assert reloaded.memory[0].occurred_at == datetime.fromisoformat(T1)


class TestDanglingLinks:
    def test_link_to_missing_memory_is_counted(self):
        memory = MemoryEntry.model_validate(
            _memory(links=[{"target": "m-assente", "relation": "follows"}])
        )
        summary = inspect_state(_state(memory=[memory]))
        assert summary["dangling_memory_links"] == 1

    def test_link_to_present_memory_is_not_counted(self):
        target = MemoryEntry.model_validate({"id": "m0", "content": "altro", "created_at": T1})
        source = MemoryEntry.model_validate(
            _memory(links=[{"target": "m0", "relation": "follows"}])
        )
        summary = inspect_state(_state(memory=[target, source]))
        assert summary["dangling_memory_links"] == 0


class TestKnowledge:
    def test_knowledge_is_typed(self):
        state = _state(knowledge=[{"content": "la Terra gira", "topic": "scienza"}])
        assert all(isinstance(entry, KnowledgeEntry) for entry in state.knowledge)
        assert state.knowledge[0].topic == "scienza"

    def test_legacy_keys_survive_round_trip(self, tmp_path):
        state = _state(knowledge=[{"topic": "python", "content": "linguaggio"}])
        path = tmp_path / "state.json"
        export_state(state, path)

        reloaded = import_state(path)
        assert reloaded.knowledge[0].model_dump() == state.knowledge[0].model_dump()
        assert measure_recovery(state, reloaded).overall_fidelity == 1.0

    def test_knowledge_has_no_occurred_at(self):
        assert "occurred_at" not in KnowledgeEntry.model_fields
        assert "occurred_at" in MemoryEntry.model_fields
        assert "salience" not in KnowledgeEntry.model_fields


class TestSchemaVersion:
    def test_new_states_are_v02(self):
        assert _state().version == "0.2"

    def test_v01_file_is_not_rewritten_on_load(self, tmp_path):
        raw = {
            "schema": "zion-state",
            "version": "0.1",
            "identity": {"agent_id": "a1", "name": "test", "version": "1.0"},
            "project": {"id": "p1", "name": "test-project"},
        }
        state = ZionState.model_validate(raw)
        assert state.version == "0.1"
