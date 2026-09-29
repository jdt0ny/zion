"""Test per migrazione cross-runtime e riconciliazione conflitti."""

from datetime import datetime

import pytest

from zion import ZionState, AgentIdentity, ProjectState, MemoryEntry
from zion.migration import (
    check_compatibility,
    detect_conflicts,
    transform_for_target,
    Conflict,
)
from zion.reconciliation import (
    reconcile,
    merge_strategy,
    overwrite_strategy,
    keep_target_strategy,
    selective_merge_strategy,
    get_strategy,
)


def _make_state(**overrides) -> ZionState:
    defaults = dict(
        identity=AgentIdentity(agent_id="agent-1", name="Agent", version="1.0"),
        project=ProjectState(id="p1", name="Project"),
        runtime={"engine": "cheshire_cat", "state": "runtime_bound"},
    )
    defaults.update(overrides)
    return ZionState(**defaults)


class TestCheckCompatibility:
    """Test per check_compatibility."""

    def test_cc_to_cc(self):
        state = _make_state()
        compat = check_compatibility(state, "cheshire_cat")
        # CC supporta: identity, conversation, memory, tools, configuration, runtime
        assert compat["identity"] is True
        assert compat["conversation"] is True
        assert compat["memory"] is True
        assert compat["tools"] is True
        assert compat["configuration"] is True
        assert compat["runtime"] is True
        # CC NON supporta: decisions, tasks, knowledge
        assert compat["decisions"] is False
        assert compat["tasks"] is False
        assert compat["knowledge"] is False

    def test_cc_to_ds4_no_conversation(self):
        state = _make_state()
        compat = check_compatibility(state, "ds4")
        assert compat["conversation"] is False

    def test_cc_to_ds4_no_memory(self):
        state = _make_state()
        compat = check_compatibility(state, "ds4")
        assert compat["memory"] is False

    def test_cc_to_ds4_tools_ok(self):
        state = _make_state()
        compat = check_compatibility(state, "ds4")
        assert compat["tools"] is True

    def test_unknown_runtime(self):
        state = _make_state()
        compat = check_compatibility(state, "unknown_runtime")
        assert all(c is False for c in compat.values())


class TestDetectConflicts:
    """Test per detect_conflicts."""

    def test_no_conflicts_with_none_target(self):
        source = _make_state()
        conflicts = detect_conflicts(source, None)
        assert conflicts == []

    def test_identity_conflict(self):
        source = _make_state()
        target = _make_state(
            identity=AgentIdentity(agent_id="other", name="Other", version="2.0")
        )
        conflicts = detect_conflicts(source, target)
        identity_conflicts = [c for c in conflicts if "identity" in c.dimension]
        assert len(identity_conflicts) == 1

    def test_memory_conflict(self):
        source = _make_state(
            memory=[MemoryEntry(id="m1", content="from source", created_at=datetime.now())]
        )
        target = _make_state(
            memory=[MemoryEntry(id="m1", content="from target", created_at=datetime.now())]
        )
        conflicts = detect_conflicts(source, target)
        memory_conflicts = [c for c in conflicts if c.dimension == "memory"]
        assert len(memory_conflicts) == 1

    def test_no_memory_conflict_empty(self):
        source = _make_state()
        target = _make_state()
        conflicts = detect_conflicts(source, target)
        memory_conflicts = [c for c in conflicts if c.dimension == "memory"]
        assert len(memory_conflicts) == 0


class TestTransformForTarget:
    """Test per transform_for_target."""

    def test_clears_incompatible_dimensions(self):
        state = _make_state(
            memory=[MemoryEntry(id="m1", content="x", created_at=datetime.now())]
        )
        compat = {
            "identity": True, "conversation": False, "memory": False,
            "decisions": False, "tasks": False, "tools": True,
            "knowledge": False, "configuration": True, "runtime": True,
        }
        result = transform_for_target(state, "ds4", compat)
        assert result.memory == []
        assert result.conversation == []
        assert result.runtime.engine == "ds4"

    def test_keeps_compatible_dimensions(self):
        state = _make_state(
            memory=[MemoryEntry(id="m1", content="x", created_at=datetime.now())]
        )
        compat = {
            "identity": True, "conversation": True, "memory": True,
            "decisions": True, "tasks": True, "tools": True,
            "knowledge": True, "configuration": True, "runtime": True,
        }
        result = transform_for_target(state, "cheshire_cat", compat)
        assert len(result.memory) == 1
        assert result.runtime.engine == "cheshire_cat"


class TestReconciliation:
    """Test per le strategie di riconciliazione."""

    def test_overwrite(self):
        source = _make_state(
            identity=AgentIdentity(agent_id="src", name="Src", version="1"),
        )
        target = _make_state(
            identity=AgentIdentity(agent_id="tgt", name="Tgt", version="2"),
        )
        conflicts = detect_conflicts(source, target)
        result = reconcile(source, target, conflicts, strategy="overwrite")
        assert result.identity.agent_id == "src"

    def test_keep_target(self):
        source = _make_state(
            identity=AgentIdentity(agent_id="src", name="Src", version="1"),
        )
        target = _make_state(
            identity=AgentIdentity(agent_id="tgt", name="Tgt", version="2"),
        )
        conflicts = detect_conflicts(source, target)
        result = reconcile(source, target, conflicts, strategy="keep_target")
        assert result.identity.agent_id == "tgt"

    def test_merge_memory(self):
        source = _make_state(
            memory=[MemoryEntry(id="m1", content="from source", created_at=datetime.now())]
        )
        target = _make_state(
            memory=[MemoryEntry(id="m2", content="from target", created_at=datetime.now())]
        )
        conflicts = detect_conflicts(source, target)
        result = reconcile(source, target, conflicts, strategy="merge")
        ids = {m.id for m in result.memory}
        assert "m1" in ids
        assert "m2" in ids

    def test_merge_prefer_source_on_overlap(self):
        source = _make_state(
            memory=[MemoryEntry(id="m1", content="source version", created_at=datetime.now())]
        )
        target = _make_state(
            memory=[MemoryEntry(id="m1", content="target version", created_at=datetime.now())]
        )
        conflicts = detect_conflicts(source, target)
        result = reconcile(source, target, conflicts, strategy="merge")
        assert len(result.memory) == 1
        assert result.memory[0].content == "source version"

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError, match="Strategia sconosciuta"):
            get_strategy("nonexistent")

    def test_merge_with_none_target(self):
        source = _make_state(
            memory=[MemoryEntry(id="m1", content="x", created_at=datetime.now())]
        )
        result = reconcile(source, None, [], strategy="merge")
        assert len(result.memory) == 1

    def test_selective_merge_is_registered(self):
        """La strategia dichiarata nel CHANGELOG deve essere raggiungibile per nome."""
        assert get_strategy("selective_merge") is selective_merge_strategy

    def test_selective_merge_only_where_asked(self):
        """Preferisce il sorgente SOLO per le dimensioni in prefer_dimensions."""
        source = _make_state(
            identity=AgentIdentity(agent_id="src", name="Src", version="1"),
            memory=[MemoryEntry(id="m1", content="source version", created_at=datetime.now())],
        )
        target = _make_state(
            identity=AgentIdentity(agent_id="tgt", name="Tgt", version="2"),
            memory=[MemoryEntry(id="m1", content="target version", created_at=datetime.now())],
        )
        conflicts = detect_conflicts(source, target)
        result = reconcile(
            source,
            target,
            conflicts,
            strategy="selective_merge",
            prefer_dimensions=["memory"],
        )
        # identity non richiesta -> resta il valore del target
        assert result.identity.agent_id == "tgt"
        # memory richiesta -> vince il sorgente
        assert len(result.memory) == 1
        assert result.memory[0].content == "source version"
