from pathlib import Path

from zion.models import (
    AgentIdentity,
    Decision,
    MemoryEntry,
    Message,
    ProjectState,
    RuntimeState,
    Task,
)
from zion.state import ZionState
from zion.export import export_state
from zion.import_ import import_state


def build_representative_state() -> ZionState:
    return ZionState(
        identity=AgentIdentity(
            agent_id="zion-001",
            name="Zion",
            version="0.1.0",
        ),
        project=ProjectState(
            id="glitch-lab",
            name="Glitch Lab",
            repository="https://github.com/example/glitch-lab",
            description="AI agent state portability research",
        ),
        memory=[
            MemoryEntry(
                id="mem-1",
                content="The project uses Python.",
                created_at="2026-01-01T00:00:00",
            ),
            MemoryEntry(
                id="mem-2",
                content="The goal is AI agent state portability.",
                created_at="2026-01-01T00:00:01",
            ),
        ],
        decisions=[
            Decision(
                id="dec-1",
                title="First runtime",
                decision="Start with Cheshire Cat.",
                created_at="2026-01-01T00:00:00",
            ),
            Decision(
                id="dec-2",
                title="Second runtime",
                decision="Use DS4 as the second runtime.",
                created_at="2026-01-01T00:00:01",
            ),
        ],
        tasks=[
            Task(
                id="task-1",
                title="Cheshire Cat adapter",
                status="in_progress",
                created_at="2026-01-01T00:00:00",
            ),
            Task(
                id="task-2",
                title="Investigate DS4 state",
                status="pending",
                created_at="2026-01-01T00:00:01",
            ),
        ],
        conversation=[
            Message(role="system", content="You are Zion, an AI agent.", created_at="2026-01-01T00:00:00"),
            Message(role="user", content="What is the goal?", created_at="2026-01-01T00:00:01"),
            Message(role="assistant", content="AI agent state portability.", created_at="2026-01-01T00:00:02"),
            Message(role="user", content="Where do we start?", created_at="2026-01-01T00:00:03"),
            Message(role="assistant", content="With Cheshire Cat.", created_at="2026-01-01T00:00:04"),
        ],
        tools=[
            {
                "name": "mock_tool",
                "description": "A mock tool for testing.",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        runtime=RuntimeState(
            engine="cheshire_cat",
            model=None,
            state="reconstructable",
        ),
    )


class TestRoundTrip:
    def test_representative_state_round_trip(self, tmp_path: Path):
        original = build_representative_state()
        path = tmp_path / "zion_state.json"

        export_state(original, path)
        reloaded = import_state(path)

        assert reloaded.identity.agent_id == "zion-001"
        assert reloaded.identity.name == "Zion"
        assert reloaded.project.name == "Glitch Lab"
        assert reloaded.project.repository == "https://github.com/example/glitch-lab"

        assert len(reloaded.memory) == 2
        assert reloaded.memory[0].content == "The project uses Python."
        assert reloaded.memory[1].content == "The goal is AI agent state portability."

        assert len(reloaded.decisions) == 2
        assert reloaded.decisions[0].decision == "Start with Cheshire Cat."
        assert reloaded.decisions[1].decision == "Use DS4 as the second runtime."

        assert len(reloaded.tasks) == 2
        assert reloaded.tasks[0].title == "Cheshire Cat adapter"
        assert reloaded.tasks[0].status == "in_progress"
        assert reloaded.tasks[1].title == "Investigate DS4 state"
        assert reloaded.tasks[1].status == "pending"

        assert len(reloaded.conversation) == 5
        assert reloaded.conversation[0].role == "system"
        assert reloaded.conversation[0].content == "You are Zion, an AI agent."
        assert reloaded.conversation[3].role == "user"
        assert reloaded.conversation[3].content == "Where do we start?"
        assert reloaded.conversation[4].role == "assistant"
        assert reloaded.conversation[4].content == "With Cheshire Cat."

        assert len(reloaded.tools) == 1
        assert reloaded.tools[0]["name"] == "mock_tool"

        assert reloaded.runtime.engine == "cheshire_cat"
        assert reloaded.runtime.state == "reconstructable"

    def test_runtime_bound_not_accidentally_portable(self, tmp_path: Path):
        state = build_representative_state()
        state.runtime = RuntimeState(
            engine="ds4",
            model="deepseek-v4-flash",
            state="runtime_bound",
        )
        path = tmp_path / "zion_state.json"
        export_state(state, path)
        reloaded = import_state(path)

        assert reloaded.runtime.state == "runtime_bound"
        assert reloaded.runtime.state != "portable"
