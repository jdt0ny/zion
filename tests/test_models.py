import pytest
from pydantic import ValidationError

from zion.models import (
    AgentIdentity,
    Decision,
    MemoryEntry,
    Message,
    Portability,
    ProjectState,
    RuntimeState,
    Task,
)
from zion.state import ZionState


class TestModels:
    def test_valid_zion_state(self):
        state = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
        )
        assert state.schema_name == "zion-state"
        assert state.version == "0.1"

    def test_default_collections(self):
        state = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
        )
        assert state.conversation == []
        assert state.memory == []
        assert state.decisions == []
        assert state.tasks == []
        assert state.tools == []
        assert state.knowledge == []
        assert state.configuration == {}

    def test_default_runtime_state(self):
        state = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
        )
        assert state.runtime.engine is None
        assert state.runtime.model is None
        assert state.runtime.state == "reconstructable"

    def test_portability_values(self):
        for p in ("portable", "reconstructable", "runtime_bound"):
            memory = MemoryEntry(
                id="m1",
                content="test",
                created_at="2026-01-01T00:00:00",
                portability=p,
            )
            assert memory.portability == p

    def test_invalid_portability(self):
        with pytest.raises(ValidationError):
            MemoryEntry(
                id="m1",
                content="test",
                created_at="2026-01-01T00:00:00",
                portability="unsupported",
            )

    def test_invalid_task_status(self):
        with pytest.raises(ValidationError):
            Task(
                id="t1",
                title="test",
                status="unknown_status",
                created_at="2026-01-01T00:00:00",
            )

    def test_invalid_message_role(self):
        with pytest.raises(ValidationError):
            Message(
                role="admin",
                content="test",
                created_at="2026-01-01T00:00:00",
            )

    def test_project_defaults(self):
        project = ProjectState(id="p1", name="test")
        assert project.description == ""
        assert project.repository is None

    def test_runtime_state_portability_classification(self):
        rs = RuntimeState(engine="ds4", model="deepseek-v4-flash", state="runtime_bound")
        assert rs.state == "runtime_bound"
