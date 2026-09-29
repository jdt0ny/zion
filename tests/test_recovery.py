from datetime import datetime
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
from zion.recovery import RecoveryReport, _count_leaves, measure_recovery, round_trip_measure
from zion.state import ZionState


def _full_state() -> ZionState:
    """Stato rappresentativo con tutte le dimensioni populate."""
    return ZionState(
        identity=AgentIdentity(agent_id="a1", name="Test Agent", version="1.0"),
        project=ProjectState(
            id="p1", name="Test Project",
            repository="https://example.com/repo",
            description="A test project",
        ),
        conversation=[
            Message(
                role="system",
                content="You are a test agent.",
                created_at="2026-01-01T00:00:00",
            ),
            Message(role="user", content="Hello", created_at="2026-01-01T00:00:01"),
            Message(role="assistant", content="Hi there", created_at="2026-01-01T00:00:02"),
        ],
        memory=[
            MemoryEntry(id="m1", content="Fact one", created_at="2026-01-01T00:00:00"),
            MemoryEntry(
                id="m2",
                content="Fact two",
                created_at="2026-01-01T00:00:01",
                portability="reconstructable",
            ),
        ],
        decisions=[
            Decision(
                id="d1",
                title="Approach",
                decision="Use TDD",
                created_at="2026-01-01T00:00:00",
            ),
        ],
        tasks=[
            Task(
                id="t1",
                title="Implement recovery",
                status="in_progress",
                created_at="2026-01-01T00:00:00",
            ),
            Task(id="t2", title="Write tests", status="pending", created_at="2026-01-01T00:00:01"),
        ],
        tools=[
            {
                "name": "search",
                "description": "Search files",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
            },
        ],
        knowledge=[
            {"topic": "python", "content": "Python is a programming language"},
        ],
        configuration={"temperature": 0.7, "max_tokens": 4096},
        runtime=RuntimeState(engine="test", model="v1", state="reconstructable"),
    )


def _empty_state() -> ZionState:
    """Stato minimo con solo identita' e progetto."""
    return ZionState(
        identity=AgentIdentity(agent_id="a1", name="Empty Agent", version="0.1"),
        project=ProjectState(id="p1", name="Empty"),
    )


class TestRecoveryReport:
    def test_report_creation(self):
        report = RecoveryReport()
        assert report.overall_fidelity == 0.0
        assert report.per_dimension == {}
        assert report.total_bytes == 0
        assert report.fields_checked == 0
        assert report.fields_recovered == 0
        assert report.field_losses == []
        assert report.portability == {}

    def test_report_with_values(self):
        report = RecoveryReport(
            overall_fidelity=0.95,
            per_dimension={"identity": 1.0, "memory": 0.9},
            total_bytes=1024,
            fields_checked=20,
            fields_recovered=19,
            field_losses=["memory[0].updated_at"],
            portability={"portable": 5, "reconstructable": 2, "runtime_bound": 1},
        )
        assert report.overall_fidelity == 0.95
        assert len(report.per_dimension) == 2
        assert report.total_bytes == 1024
        assert len(report.field_losses) == 1


class TestMeasureRecovery:
    def test_identical_state_perfect_fidelity(self):
        state = _full_state()
        report = measure_recovery(state, state)
        assert report.overall_fidelity == 1.0
        assert report.fields_checked > 0
        assert report.fields_recovered == report.fields_checked
        assert report.field_losses == []

    def test_empty_state_perfect_fidelity(self):
        state = _empty_state()
        report = measure_recovery(state, state)
        assert report.overall_fidelity == 1.0
        assert report.field_losses == []

    def test_per_dimension_scores(self):
        state = _full_state()
        report = measure_recovery(state, state)
        for dim, score in report.per_dimension.items():
            assert score == 1.0, f"Dimension {dim} has fidelity {score}, expected 1.0"

    def test_portability_counts(self):
        state = _full_state()
        report = measure_recovery(state, state)
        assert report.portability["portable"] >= 2
        assert report.portability["reconstructable"] >= 1

    def test_detects_lost_field(self):
        original = _full_state()
        recovered = _full_state()
        recovered.identity.name = "Different Agent"
        report = measure_recovery(original, recovered)
        assert report.overall_fidelity < 1.0
        assert any("identity" in loss for loss in report.field_losses)

    def test_detects_lost_list_element(self):
        original = _full_state()
        recovered = _full_state()
        recovered.conversation = recovered.conversation[:2]
        report = measure_recovery(original, recovered)
        assert report.overall_fidelity < 1.0
        assert any("conversation" in loss for loss in report.field_losses)


class TestRoundTripMeasure:
    def test_full_state_round_trip(self, tmp_path: Path):
        state = _full_state()
        path = tmp_path / "recovery.json"
        report = round_trip_measure(state, path)

        assert report.overall_fidelity == 1.0
        assert report.total_bytes > 0
        assert report.fields_checked > 0
        assert report.fields_recovered == report.fields_checked
        assert report.field_losses == []

    def test_empty_state_round_trip(self, tmp_path: Path):
        state = _empty_state()
        path = tmp_path / "empty.json"
        report = round_trip_measure(state, path)

        assert report.overall_fidelity == 1.0
        assert report.total_bytes > 0

    def test_json_file_created(self, tmp_path: Path):
        state = _full_state()
        path = tmp_path / "output.json"
        round_trip_measure(state, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_portability_distribution_in_report(self, tmp_path: Path):
        state = _full_state()
        path = tmp_path / "state.json"
        report = round_trip_measure(state, path)

        assert "portable" in report.portability
        assert "reconstructable" in report.portability
        assert "runtime_bound" in report.portability

    def test_per_dimension_complete(self, tmp_path: Path):
        state = _full_state()
        path = tmp_path / "state.json"
        report = round_trip_measure(state, path)

        expected_dims = {"identity", "project", "conversation", "memory",
                         "decisions", "tasks", "tools", "knowledge",
                         "configuration", "runtime"}
        assert set(report.per_dimension.keys()) == expected_dims
        for dim, score in report.per_dimension.items():
            assert 0.0 <= score <= 1.0, f"Dimension {dim} out of range: {score}"


class TestCountLeaves:
    def test_scalar(self):
        assert _count_leaves(42) == 1
        assert _count_leaves("hello") == 1
        assert _count_leaves(None) == 1

    def test_dict(self):
        assert _count_leaves({"a": 1}) == 1
        assert _count_leaves({"a": 1, "b": 2}) == 2
        assert _count_leaves({"a": {"x": 1, "y": 2}}) == 2

    def test_list(self):
        assert _count_leaves([1, 2, 3]) == 3
        assert _count_leaves([{"a": 1}, {"b": 2}]) == 2

    def test_nested(self):
        value = {"a": [{"x": 1}, {"y": 2}], "b": 3}
        assert _count_leaves(value) == 3


class TestLeafCountingInComparison:
    def test_missing_dict_key_counts_leaves(self):
        from zion.recovery import _deep_compare
        a = {"x": 1}
        b = {"x": 1, "config": {"a": 1, "b": 2, "c": 3}}
        checked, recovered, losses = _deep_compare(a, b, "test")
        assert checked == 4
        assert recovered == 1
        assert len(losses) == 1

    def test_list_length_mismatch_counts_leaves(self):
        from zion.recovery import _deep_compare
        a = [{"x": 1, "y": 2}, {"z": 3}]
        b = [{"x": 1}]
        checked, recovered, losses = _deep_compare(a, b, "test")
        assert checked == 4
        assert recovered == 0
        assert len(losses) == 1


class TestDatetimeTolerance:
    def test_identical_datetimes(self):
        from zion.recovery import _deep_compare
        dt = datetime(2026, 1, 1, 12, 30, 45, 123456)
        checked, recovered, losses = _deep_compare(dt, dt, "test")
        assert checked == 1
        assert recovered == 1
        assert losses == []

    def test_microsecond_difference_tolerated(self):
        from zion.recovery import _deep_compare
        dt1 = datetime(2026, 1, 1, 12, 30, 45, 0)
        dt2 = datetime(2026, 1, 1, 12, 30, 45, 999999)
        checked, recovered, losses = _deep_compare(dt1, dt2, "test")
        assert checked == 1
        assert recovered == 1
        assert losses == []

    def test_second_difference_not_tolerated(self):
        from zion.recovery import _deep_compare
        dt1 = datetime(2026, 1, 1, 12, 30, 45)
        dt2 = datetime(2026, 1, 1, 12, 30, 46)
        checked, recovered, losses = _deep_compare(dt1, dt2, "test")
        assert checked == 1
        assert recovered == 0
        assert len(losses) == 1
