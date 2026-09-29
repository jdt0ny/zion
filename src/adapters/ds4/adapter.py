"""
Adattatore per DS4 (DwarfStar4) — fornitore LLM locale.

DS4 NON e' un framework di agenti: e' un engine di inferenza locale
con API OpenAI/Anthropic-compatibile. Questo adattatore espone DS4
come fornitore LLM, non come estrattore di stato agente.

Stato mappato:
  identity      -> non presente (DS4 non ha identita' di agente)
  conversation  -> non persistente (server stateless)
  memory        -> non presente
  decisions     -> non presente
  tasks         -> non presente
  tools         -> 8 hardcoded (names + schema portabili)
  knowledge     -> non presente
  configuration -> PORTABLE (flag CLI)
  runtime       -> RUNTIME_BOUND (engine, GPU, session)

Uso tipico:
  adapter = DS4Adapter(base_url="http://localhost:11434")
  config = adapter.get_model_config()
  tools = adapter.get_tool_definitions()
"""

from adapters.base import BaseAdapter
from zion.models import (
    AgentIdentity,
    ProjectState,
    RuntimeState,
)
from zion.state import ZionState

# Tool hardcoded di DS4 (da ds4_agent.c)
_DS4_TOOLS = [
    {
        "name": "read",
        "description": "Legge il contenuto di un file",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path del file"}
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "write",
        "description": "Scrive contenuto in un file",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "edit",
        "description": "Modifica una porzione di file",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
            },
            "required": ["file_path", "old_text", "new_text"],
        },
    },
    {
        "name": "list",
        "description": "Elenca i file in una directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path della directory"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "search",
        "description": "Cerca testo nei file del progetto",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "bash",
        "description": "Esegue un comando bash",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "google_search",
        "description": "Cerca su Google",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "visit_page",
        "description": "Visita una pagina web e ne estrae il contenuto",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
            },
            "required": ["url"],
        },
    },
]


class DS4Adapter(BaseAdapter):
    """
    Adattatore DS4 come fornitore LLM locale.

    Parametri:
        base_url: URL del server DS4 (default: http://localhost:11434)
        api_key:  chiave API (default: "dsv4-local" per inferenza locale)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        api_key: str = "dsv4-local",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def inspect(self) -> dict:
        """Restituisce un riepilogo della configurazione DS4."""
        return {
            "runtime": "ds4",
            "base_url": self.base_url,
            "role": "llm_provider",
            "note": (
                "DS4 e' un engine di inferenza, non un framework agenti. "
                "Non ha stato agente estraibile."
            ),
            "dimensions": {
                "identity": "non_presente",
                "conversation": "non_persistente",
                "memory": "non_presente",
                "decisions": "non_presente",
                "tasks": "non_presente",
                "tools": "hardcoded_8",
                "knowledge": "non_presente",
                "configuration": "portabile_cli",
                "runtime": "runtime_bound",
            },
        }

    def export(self) -> ZionState:
        """Esporta la configurazione DS4 come ZionState.

        Nota: DS4 non ha stato agente. Questo export cattura
        solo la configurazione e i tool disponibili.
        """
        return ZionState(
            identity=AgentIdentity(
                agent_id="ds4",
                name="DS4 Local LLM",
                version="1.0.0",
            ),
            project=ProjectState(
                id="ds4-project",
                name="DS4 Local Inference",
                description="Configurazione DS4 (DwarfStar4) come fornitore LLM",
            ),
            conversation=[],
            memory=[],
            decisions=[],
            tasks=[],
            tools=_DS4_TOOLS,
            knowledge=[],
            configuration={
                "base_url": self.base_url,
                "api_compatibility": ["openai", "anthropic"],
                "model_type": "local_gguf",
            },
            runtime=RuntimeState(
                engine="ds4",
                model=None,
                state="runtime_bound",
            ),
        )

    def import_state(self, state: ZionState) -> None:
        """Import non supportato per DS4.

        DS4 non ha stato agente. L'unica configurazione importabile
        e' il modello e i parametri di inferenza, che sono CLI flags.
        """
        raise NotImplementedError(
            "DS4 non supporta l'import di stato agente. "
            "E' un engine di inferenza locale. "
            "Usa i flag CLI per configurarlo."
        )

    def get_model_config(self) -> dict:
        """Restituisce la configurazione modello per DS4."""
        return {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "api_type": "openai",
            "model": "deepseek-v4-flash",
        }

    def get_tool_definitions(self) -> list[dict]:
        """Restituisce le definizioni degli tool DS4."""
        return list(_DS4_TOOLS)
