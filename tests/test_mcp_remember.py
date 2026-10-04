"""Mossa 2: scrittura in esecuzione — zion_remember / zion_recall.

Un agente che lavora lascia traccia da solo, senza che nessuno chieda un
export: l'export resta un'operazione di distribuzione.
"""

import json
from pathlib import Path

import pytest

from zion import (
    AgentIdentity,
    MemoryEntry,
    ProjectState,
    ZionState,
    export_state,
    import_state,
)
from zion.mcp import server
from zion.mcp.server import zion_recall, zion_remember
from zion.recovery import measure_recovery

AGENT = "live-001"


@pytest.fixture(autouse=True)
def isolated_work_dir(monkeypatch, tmp_path):
    """Ogni test scrive nella sua work dir, mai in /tmp/zion-mcp."""
    monkeypatch.setattr(server, "_WORK_DIR", tmp_path)
    return tmp_path


def _existing_state(agent_id: str = AGENT) -> ZionState:
    state = ZionState(
        identity=AgentIdentity(agent_id=agent_id, name="Live", version="0.1"),
        project=ProjectState(id="p1", name="Progetto"),
        memory=[
            MemoryEntry(
                id="m1",
                content="ricordo di partenza",
                created_at="2026-01-01T00:00:00",
            )
        ],
    )
    export_state(state, _store(agent_id))
    return state


def _store(agent_id: str) -> Path:
    return Path(server._WORK_DIR) / f"{server._safe_filename(agent_id)}.json"


class TestZionRemember:
    def test_creates_state_when_missing(self):
        result = json.loads(zion_remember(agent_id=AGENT, content="primo ricordo"))
        assert "error" not in result
        assert result["created"] is True
        assert result["memory_count"] == 1
        assert _store(AGENT).exists()

        state = import_state(_store(AGENT))
        assert state.identity.agent_id == AGENT
        assert state.memory[0].content == "primo ricordo"

    def test_appends_without_touching_previous_memories(self):
        _existing_state()
        zion_remember(agent_id=AGENT, content="secondo")
        result = json.loads(zion_remember(agent_id=AGENT, content="terzo"))

        assert result["memory_count"] == 3
        state = import_state(_store(AGENT))
        assert [m.content for m in state.memory] == [
            "ricordo di partenza", "secondo", "terzo",
        ]

    def test_writes_episodic_fields(self):
        result = json.loads(zion_remember(
            agent_id=AGENT,
            content="ho scelto uv",
            context="sessione di packaging",
            salience=0.8,
            occurred_at="2026-09-29T14:34:00",
            links=[{"target": "m1", "relation": "follows"}],
        ))
        assert "error" not in result

        memory = import_state(_store(AGENT)).memory[0]
        assert memory.context == "sessione di packaging"
        assert memory.salience == 0.8
        assert memory.occurred_at.isoformat().startswith("2026-09-29T14:34:00")
        assert memory.links[0].target == "m1"
        assert memory.links[0].relation == "follows"

    def test_rejects_out_of_range_salience(self):
        result = json.loads(zion_remember(agent_id=AGENT, content="x", salience=2.0))
        assert "error" in result

    def test_empty_content_is_rejected(self):
        result = json.loads(zion_remember(agent_id=AGENT, content="   "))
        assert "error" in result
        assert not _store(AGENT).exists()

    def test_rejects_unknown_relation(self):
        result = json.loads(zion_remember(
            agent_id=AGENT, content="x",
            links=[{"target": "m1", "relation": "qualunque"}],
        ))
        assert "error" in result
        assert not _store(AGENT).exists()

    def test_rejects_malformed_occurred_at(self):
        result = json.loads(zion_remember(
            agent_id=AGENT, content="x", occurred_at="ieri",
        ))
        assert "error" in result

    def test_agent_id_is_sandboxed(self):
        result = json.loads(zion_remember(agent_id="../../evil", content="x"))
        assert "error" not in result
        path = Path(result["path"])
        assert path.parent == Path(server._WORK_DIR)
        assert path.name == "evil.json"

    def test_export_is_distribution_not_save(self):
        """Ciò che viene annotato in giro si esporta con fedeltà 1.0."""
        _existing_state()
        zion_remember(agent_id=AGENT, content="annotato mentre agivo")

        live = import_state(_store(AGENT))
        distribuzione = _store(AGENT).parent / "distribuzione.json"
        export_state(live, distribuzione)

        assert measure_recovery(live, import_state(distribuzione)).overall_fidelity == 1.0


class TestZionRecall:
    def test_finds_matching_content(self):
        _existing_state()
        zion_remember(agent_id=AGENT, content="server MCP in ascolto")
        zion_remember(agent_id=AGENT, content="caffè preso")

        result = json.loads(zion_recall(agent_id=AGENT, query="MCP"))
        assert "error" not in result
        assert result["matches"] == 1
        assert result["results"][0]["content"] == "server MCP in ascolto"

    def test_search_is_case_insensitive_and_covers_context(self):
        zion_remember(
            agent_id=AGENT, content="nota opaca", context="durante il RELEASE",
        )
        result = json.loads(zion_recall(agent_id=AGENT, query="release"))
        assert result["matches"] == 1

    def test_empty_query_returns_most_salient_first(self):
        zion_remember(agent_id=AGENT, content="banale", salience=0.2)
        zion_remember(agent_id=AGENT, content="importante", salience=0.9)

        result = json.loads(zion_recall(agent_id=AGENT, query=""))
        assert [r["content"] for r in result["results"]] == ["importante", "banale"]

    def test_limit_is_respected(self):
        for i in range(5):
            zion_remember(agent_id=AGENT, content=f"ricordo {i}")

        result = json.loads(zion_recall(agent_id=AGENT, query="", limit=2))
        assert len(result["results"]) == 2
        assert result["matches"] == 5

    def test_limit_below_one_is_rejected(self):
        zion_remember(agent_id=AGENT, content="x")
        result = json.loads(zion_recall(agent_id=AGENT, query="x", limit=0))
        assert "error" in result

    def test_missing_state_is_an_error(self):
        result = json.loads(zion_recall(agent_id="mai-esistito", query="x"))
        assert "error" in result

    def test_corrupt_store_is_reported(self):
        path = _store(AGENT)
        path.write_text("{non e' json", encoding="utf-8")
        result = json.loads(zion_recall(agent_id=AGENT, query="x"))
        assert "error" in result

    def test_recalled_entry_keeps_episode_shape(self):
        zion_remember(agent_id=AGENT, content="x", salience=0.7, context="ctx")
        entry = json.loads(zion_recall(agent_id=AGENT, query="x"))["results"][0]

        assert entry["salience"] == 0.7
        assert entry["context"] == "ctx"
        assert "occurred_at" in entry
        assert "created_at" in entry


def test_tools_are_registered():
    """I due tool devono essere registrati sul server MCP."""
    tools = getattr(server.mcp, "_tool_manager", None)
    if tools is None:
        pytest.skip("SDK MCP senza _tool_manager ispezionabile")
    assert {"zion_remember", "zion_recall"} <= set(tools._tools)
