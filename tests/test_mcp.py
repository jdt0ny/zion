"""Test per il server MCP Zion."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from zion import AgentIdentity, MemoryEntry, ProjectState, Task, ZionState
from zion.mcp.server import (
    _WORK_DIR,
    _parse_state,
    zion_export,
    zion_import,
    zion_inspect,
    zion_measure,
    zion_round_trip,
)


def _make_state(**overrides) -> ZionState:
    defaults = dict(
        identity=AgentIdentity(agent_id="test-001", name="Test Agent", version="0.1"),
        project=ProjectState(id="proj-001", name="Test Project"),
        memory=[MemoryEntry(id="m1", content="Ricordo", created_at=datetime.now())],
        tasks=[Task(id="t1", title="Task", status="in_progress", created_at=datetime.now())],
    )
    defaults.update(overrides)
    return ZionState(**defaults)


class TestParseState:
    """Test per _parse_state."""

    def test_valid_json(self):
        state = _make_state()
        parsed = _parse_state(state.model_dump_json(by_alias=True))
        assert parsed.identity.agent_id == "test-001"

    def test_invalid_json(self):
        with pytest.raises(ValueError, match="JSON non valido"):
            _parse_state("not json")

    def test_invalid_state(self):
        with pytest.raises(ValueError, match="Stato Zion non valido"):
            _parse_state('{"not": "zion"}')


class TestZionInspect:
    """Test per zion_inspect."""

    def test_returns_summary(self):
        state = _make_state()
        result = json.loads(zion_inspect(state.model_dump_json(by_alias=True)))
        assert "identity" in result
        assert "portability_summary" in result
        assert result["memory_count"] == 1
        assert result["task_count"] == 1

    def test_invalid_json(self):
        result = json.loads(zion_inspect("bad"))
        assert "error" in result


class TestZionExport:
    """Test per zion_export."""

    def test_export_creates_file(self, tmp_path):
        state = _make_state()
        path = str(tmp_path / "test.json")
        result = json.loads(zion_export(
            state.model_dump_json(by_alias=True),
            path=path,
        ))
        assert result["path"] == path
        assert result["bytes"] > 0
        assert result["agent_id"] == "test-001"

    def test_export_default_path(self):
        state = _make_state()
        result = json.loads(zion_export(state.model_dump_json(by_alias=True)))
        assert "path" in result
        assert result["bytes"] > 0

    def test_export_default_path_is_sandboxed(self):
        """Un agent_id con separatori di percorso non deve uscire dalla work dir."""
        state = _make_state(
            identity=AgentIdentity(agent_id="../../evil", name="Evil", version="0.1")
        )
        result = json.loads(zion_export(state.model_dump_json(by_alias=True)))
        path = Path(result["path"])
        assert path.parent == _WORK_DIR
        assert path.name == "evil.json"


class TestZionImport:
    """Test per zion_import."""

    def test_import_valid_file(self, tmp_path):
        state = _make_state()
        path = tmp_path / "test.json"
        state.export(path) if hasattr(state, 'export') else None

        # Scrivi manualmente
        import json
        with open(path, "w") as f:
            json.dump(state.model_dump(mode="json", by_alias=True), f)

        result = json.loads(zion_import(str(path)))
        assert result["identity"]["agent_id"] == "test-001"

    def test_import_nonexistent_file(self):
        result = json.loads(zion_import("/tmp/non-esiste.json"))
        assert "error" in result


class TestZionMeasure:
    """Test per zion_measure."""

    def test_identical_states(self):
        state = _make_state()
        s = state.model_dump_json(by_alias=True)
        result = json.loads(zion_measure(s, s))
        assert result["overall_fidelity"] == 1.0

    def test_different_states(self):
        s1 = _make_state()
        s2 = _make_state(
            memory=[MemoryEntry(id="m2", content="Altro", created_at=datetime.now())]
        )
        result = json.loads(zion_measure(
            s1.model_dump_json(by_alias=True),
            s2.model_dump_json(by_alias=True),
        ))
        assert result["overall_fidelity"] < 1.0

    def test_invalid_input(self):
        result = json.loads(zion_measure("bad", "bad"))
        assert "error" in result


class TestZionRoundTrip:
    """Test per zion_round_trip."""

    def test_perfect_fidelity(self, tmp_path):
        state = _make_state()
        path = str(tmp_path / "rt.json")
        result = json.loads(zion_round_trip(
            state.model_dump_json(by_alias=True),
            path=path,
        ))
        assert result["overall_fidelity"] == 1.0
        assert result["total_bytes"] > 0

    def test_default_path(self):
        state = _make_state()
        result = json.loads(zion_round_trip(state.model_dump_json(by_alias=True)))
        assert result["overall_fidelity"] == 1.0

    def test_invalid_input(self):
        result = json.loads(zion_round_trip("bad"))
        assert "error" in result
