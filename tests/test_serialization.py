import json
from pathlib import Path

import pytest

from zion.models import AgentIdentity, Message, ProjectState, RuntimeState
from zion.state import ZionState
from zion.export import export_state
from zion.import_ import import_state


class TestSerialization:
    def test_round_trip(self, tmp_path: Path):
        original = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
            conversation=[
                Message(role="user", content="Hello", created_at="2026-01-01T00:00:00"),
                Message(role="assistant", content="Hi", created_at="2026-01-01T00:00:01"),
            ],
            runtime=RuntimeState(engine="test", model="v1", state="reconstructable"),
        )

        path = tmp_path / "state.json"
        export_state(original, path)
        reloaded = import_state(path)

        assert reloaded.schema_name == original.schema_name
        assert reloaded.version == original.version
        assert reloaded.identity.agent_id == "a1"
        assert reloaded.identity.name == "test"
        assert reloaded.project.id == "p1"
        assert len(reloaded.conversation) == 2
        assert reloaded.conversation[0].content == "Hello"
        assert reloaded.conversation[1].content == "Hi"
        assert reloaded.runtime.engine == "test"

    def test_json_is_human_readable(self, tmp_path: Path):
        state = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
        )
        path = tmp_path / "state.json"
        export_state(state, path)

        with open(path) as f:
            raw = f.read()

        data = json.loads(raw)
        assert data["schema"] == "zion-state"
        assert data["version"] == "0.1"
        assert "\n" in raw

    def test_empty_collections_survive_round_trip(self, tmp_path: Path):
        state = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
        )
        path = tmp_path / "state.json"
        export_state(state, path)
        reloaded = import_state(path)

        assert reloaded.conversation == []
        assert reloaded.memory == []
        assert reloaded.decisions == []
        assert reloaded.tasks == []
        assert reloaded.tools == []
        assert reloaded.knowledge == []

    def test_runtime_bound_state_preserved(self, tmp_path: Path):
        state = ZionState(
            identity=AgentIdentity(agent_id="a1", name="test", version="1.0"),
            project=ProjectState(id="p1", name="test-project"),
            runtime=RuntimeState(engine="ds4", model="deepseek-v4-flash", state="runtime_bound"),
        )
        path = tmp_path / "state.json"
        export_state(state, path)
        reloaded = import_state(path)

        assert reloaded.runtime.state == "runtime_bound"
