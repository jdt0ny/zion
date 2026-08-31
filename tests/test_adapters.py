"""Test per gli adapter Zion."""

from datetime import datetime

import pytest

from adapters import BaseAdapter, CheshireCatAdapter, DS4Adapter
from adapters.base import BaseAdapter
from zion import ZionState, AgentIdentity, ProjectState, MemoryEntry
from zion.state import ZionState


class TestBaseAdapter:
    """Test per l'adapter base astratto."""

    def test_cannot_instantiate_base(self):
        with pytest.raises(TypeError):
            BaseAdapter()


class TestCheshireCatAdapter:
    """Test per CheshireCatAdapter."""

    def test_inspect_without_db(self):
        adapter = CheshireCatAdapter(base_url="http://localhost:1865")
        result = adapter.inspect()
        assert result["runtime"] == "cheshire_cat"
        assert "note" in result

    def test_export_without_db(self):
        adapter = CheshireCatAdapter(base_url="http://localhost:1865")
        state = adapter.export()
        assert isinstance(state, ZionState)
        assert state.identity.agent_id == "cheshire-cat"
        assert state.identity.name == "Cheshire Cat Agent"
        assert state.runtime.engine == "cheshire_cat"

    def test_export_conversation_empty_without_db(self):
        adapter = CheshireCatAdapter()
        state = adapter.export()
        assert state.conversation == []

    def test_export_memory_empty_without_db(self):
        adapter = CheshireCatAdapter()
        state = adapter.export()
        assert state.memory == []

    def test_export_tools_empty_without_db(self):
        adapter = CheshireCatAdapter()
        state = adapter.export()
        assert state.tools == []

    def test_export_configuration_empty_without_db(self):
        adapter = CheshireCatAdapter()
        state = adapter.export()
        assert state.configuration == {}

    def test_import_without_db_raises(self):
        adapter = CheshireCatAdapter()
        state = ZionState(
            identity=AgentIdentity(agent_id="test", name="T", version="1"),
            project=ProjectState(id="p", name="P"),
        )
        with pytest.raises(FileNotFoundError):
            adapter.import_state(state)

    def test_extract_text_content_string(self):
        adapter = CheshireCatAdapter()
        result = adapter._extract_text_content("hello")
        assert result == "hello"

    def test_extract_text_content_list(self):
        adapter = CheshireCatAdapter()
        blocks = [{"text": "hello"}, {"text": "world"}]
        result = adapter._extract_text_content(blocks)
        assert result == "hello world"

    def test_extract_text_content_mixed(self):
        adapter = CheshireCatAdapter()
        blocks = [{"text": "hello"}, "world"]
        result = adapter._extract_text_content(blocks)
        assert result == "hello world"


class TestDS4Adapter:
    """Test per DS4Adapter."""

    def test_inspect(self):
        adapter = DS4Adapter(base_url="http://localhost:11434")
        result = adapter.inspect()
        assert result["runtime"] == "ds4"
        assert result["role"] == "llm_provider"

    def test_export(self):
        adapter = DS4Adapter(base_url="http://localhost:11434")
        state = adapter.export()
        assert isinstance(state, ZionState)
        assert state.identity.agent_id == "ds4"
        assert state.identity.name == "DS4 Local LLM"
        assert state.runtime.engine == "ds4"

    def test_export_has_8_tools(self):
        adapter = DS4Adapter()
        state = adapter.export()
        assert len(state.tools) == 8

    def test_export_tool_names(self):
        adapter = DS4Adapter()
        state = adapter.export()
        names = {t["name"] for t in state.tools}
        expected = {
            "read", "write", "edit", "list",
            "search", "bash", "google_search", "visit_page",
        }
        assert names == expected

    def test_export_configuration(self):
        adapter = DS4Adapter(base_url="http://custom:8080")
        state = adapter.export()
        assert state.configuration["base_url"] == "http://custom:8080"
        assert "openai" in state.configuration["api_compatibility"]

    def test_import_raises(self):
        adapter = DS4Adapter()
        state = ZionState(
            identity=AgentIdentity(agent_id="test", name="T", version="1"),
            project=ProjectState(id="p", name="P"),
        )
        with pytest.raises(NotImplementedError):
            adapter.import_state(state)

    def test_get_model_config(self):
        adapter = DS4Adapter(base_url="http://myhost:9090", api_key="sk-test")
        config = adapter.get_model_config()
        assert config["base_url"] == "http://myhost:9090"
        assert config["api_key"] == "sk-test"
        assert config["api_type"] == "openai"

    def test_get_tool_definitions(self):
        adapter = DS4Adapter()
        tools = adapter.get_tool_definitions()
        assert len(tools) == 8
        assert all("name" in t for t in tools)
        assert all("input_schema" in t for t in tools)
