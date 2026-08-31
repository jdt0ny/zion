"""
Adattatore per Cheshire Cat AI.

Estrae lo stato da un'istanza Cheshire Cat e lo converte in ZionState.

Dimensioni mappate:
  identity      -> sintetizzato (Cheshire Cat non ha concetto di identita')
  conversation  -> PORTABLE (messaggi JSON dal database chats)
  memory        -> PORTABLE (coppie key-value globali e per utente)
  decisions     -> non presente (vuoto)
  tasks         -> non presente (vuoto)
  tools         -> PORTABLE (definizioni @tool) + RUNTIME_BOUND (implementazione)
  knowledge     -> non presente (vuoto)
  configuration -> PORTABLE (settings JSON, secret esclusi)
  runtime       -> RUNTIME_BOUND

Limitazioni:
  - Richiede un'istanza Cheshire Cat in esecuzione oppure il path al database
  - I secret (API key, token) vengono esclusi dall'export
  - Le implementazioni Python degli tool non sono portabili
"""

import json
import re
from pathlib import Path

from adapters.base import BaseAdapter
from zion.models import (
    AgentIdentity,
    MemoryEntry,
    Message,
    ProjectState,
    RuntimeState,
    Task,
    Decision,
)
from zion.state import ZionState

# Chiavi da escludere dall'export per sicurezza
_SECRET_PATTERNS = re.compile(
    r"(api_key|token|secret|password|jwt|oauth|credential)",
    re.IGNORECASE,
)


class CheshireCatAdapter(BaseAdapter):
    """
    Adattatore per Cheshire Cat AI.

    Parametri:
        base_url: URL base dell'istanza Cheshire Cat (es. http://localhost:1865)
        db_path:  path opzionale al file SQLite (es. cat_data/ccat_root/cat.db)
        user_id:  ID utente per filtrare la memoria per utente
    """

    def __init__(
        self,
        base_url: str = "http://localhost:1865",
        db_path: str | None = None,
        user_id: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.db_path = Path(db_path) if db_path else None
        self.user_id = user_id

    def inspect(self) -> dict:
        """Restituisce un riepilogo dello stato disponibile."""
        result = {
            "runtime": "cheshire_cat",
            "base_url": self.base_url,
            "dimensions": {},
        }

        if self.db_path and self.db_path.exists():
            result["database"] = str(self.db_path)
            result["dimensions"] = self._inspect_from_db()
        else:
            result["note"] = (
                "Database non trovato. "
                "Passa db_path per l'estrazione completa."
            )

        return result

    def export(self) -> ZionState:
        """Estrae lo stato da Cheshire Cat in formato ZionState."""
        identity = self._extract_identity()
        project = self._extract_project()
        conversation = self._extract_conversation()
        memory = self._extract_memory()
        tools = self._extract_tools()
        configuration = self._extract_configuration()

        return ZionState(
            identity=identity,
            project=project,
            conversation=conversation,
            memory=memory,
            decisions=[],
            tasks=[],
            tools=tools,
            knowledge=[],
            configuration=configuration,
            runtime=RuntimeState(
                engine="cheshire_cat",
                model=configuration.get("default_llm"),
                state="runtime_bound",
            ),
        )

    def import_state(self, state: ZionState) -> None:
        """Carica uno stato Zion in Cheshire Cat.

        Nota: l'import e' limitato alle dimensioni supportate.
        Le dimensioni non presenti in Cheshire Cat vengono ignorate.
        """
        if not self.db_path or not self.db_path.exists():
            raise FileNotFoundError(
                f"Database non trovato: {self.db_path}. "
                "Serve il path al database per l'import."
            )

        self._import_memory(state.memory)
        self._import_configuration(state.configuration)

    # ------------------------------------------------------------------
    # Estrazione dal database
    # ------------------------------------------------------------------

    def _inspect_from_db(self) -> dict:
        """Interroga il database SQLite per un riepilogo."""
        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        result = {}

        # Conta chats
        try:
            cursor.execute("SELECT COUNT(*) FROM ccat_chats")
            result["chat_count"] = cursor.fetchone()[0]
        except Exception:
            result["chat_count"] = 0

        # Conta coppie key-value globali
        try:
            cursor.execute("SELECT COUNT(*) FROM ccat_global_key_value")
            result["global_kv_count"] = cursor.fetchone()[0]
        except Exception:
            result["global_kv_count"] = 0

        # Conta coppie key-value per utente
        try:
            cursor.execute("SELECT COUNT(*) FROM ccat_user_key_value")
            result["user_kv_count"] = cursor.fetchone()[0]
        except Exception:
            result["user_kv_count"] = 0

        conn.close()
        return result

    def _extract_identity(self) -> AgentIdentity:
        """Sintetizza un'identita' da Cheshire Cat (non ha identita' propria)."""
        return AgentIdentity(
            agent_id="cheshire-cat",
            name="Cheshire Cat Agent",
            version="2.0.23",
        )

    def _extract_project(self) -> ProjectState:
        """Sintetizza info progetto."""
        return ProjectState(
            id="cheshire-cat-project",
            name="Cheshire Cat Project",
            description="Progetto estratto da Cheshire Cat AI",
        )

    def _extract_conversation(self) -> list[Message]:
        """Estrae la cronologia conversazioni dal database."""
        if not self.db_path or not self.db_path.exists():
            return []

        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        messages = []
        try:
            cursor.execute(
                "SELECT messages FROM ccat_chats ORDER BY updated_at"
            )
            for row in cursor.fetchall():
                chat_data = json.loads(row["messages"])
                for msg in chat_data:
                    role = msg.get("role", "user")
                    content = self._extract_text_content(msg.get("content", ""))
                    if content:
                        messages.append(
                            Message(
                                role=role,
                                content=content,
                                created_at="1970-01-01T00:00:00",
                            )
                        )
        except Exception:
            pass

        conn.close()
        return messages

    def _extract_text_content(self, content) -> str:
        """Estrae il testo puro da un ContentBlock o una stringa."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict):
                    texts.append(block.get("text", ""))
                elif isinstance(block, str):
                    texts.append(block)
            return " ".join(texts)
        return str(content)

    def _extract_memory(self) -> list[MemoryEntry]:
        """Estrae le coppie key-value come MemoryEntry."""
        if not self.db_path or not self.db_path.exists():
            return []

        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        entries = []
        try:
            # Memoria globale
            cursor.execute(
                "SELECT name, value FROM ccat_global_key_value"
            )
            for row in cursor.fetchall():
                entries.append(
                    MemoryEntry(
                        id=f"global:{row['name']}",
                        content=json.dumps(
                            {"key": row["name"], "value": row["value"]}
                        ),
                        created_at="1970-01-01T00:00:00",
                        portability="portable",
                    )
                )
        except Exception:
            pass

        try:
            # Memoria per utente
            if self.user_id:
                cursor.execute(
                    "SELECT name, value FROM ccat_user_key_value "
                    "WHERE user_id = ?",
                    (self.user_id,),
                )
                for row in cursor.fetchall():
                    entries.append(
                        MemoryEntry(
                            id=f"user:{self.user_id}:{row['name']}",
                            content=json.dumps(
                                {"key": row["name"], "value": row["value"]}
                            ),
                            created_at="1970-01-01T00:00:00",
                            portability="portable",
                        )
                    )
        except Exception:
            pass

        conn.close()
        return entries

    def _extract_tools(self) -> list[dict]:
        """Estrae le definizioni degli tool (senza implementazione)."""
        if not self.db_path or not self.db_path.exists():
            return []

        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        tools = []
        try:
            cursor.execute(
                "SELECT name, value FROM ccat_global_key_value "
                "WHERE name LIKE 'settings_%_tool_%'"
            )
            for row in cursor.fetchall():
                try:
                    tool_data = json.loads(row["value"])
                    tools.append({
                        "name": tool_data.get("name", row["name"]),
                        "description": tool_data.get("description", ""),
                        "input_schema": tool_data.get("input_schema", {}),
                        "portability": "portable",
                    })
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

        conn.close()
        return tools

    def _extract_configuration(self) -> dict:
        """Estrae la configurazione escludendo i secret."""
        if not self.db_path or not self.db_path.exists():
            return {}

        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        config = {}
        try:
            cursor.execute(
                "SELECT name, value FROM ccat_global_key_value "
                "WHERE name LIKE 'settings_%'"
            )
            for row in cursor.fetchall():
                key = row["name"]
                if _SECRET_PATTERNS.search(key):
                    continue
                try:
                    config[key] = json.loads(row["value"])
                except (json.JSONDecodeError, TypeError):
                    config[key] = row["value"]
        except Exception:
            pass

        conn.close()
        return config

    # ------------------------------------------------------------------
    # Import nel database
    # ------------------------------------------------------------------

    def _import_memory(self, memories: list[MemoryEntry]) -> None:
        """Importa le MemoryEntry nel database Cheshire Cat."""
        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        for entry in memories:
            try:
                data = json.loads(entry.content)
                key = data.get("key", entry.id)
                value = data.get("value", entry.content)

                if entry.id.startswith("user:"):
                    parts = entry.id.split(":")
                    user_id = parts[1] if len(parts) > 1 else "user"
                    cursor.execute(
                        "INSERT OR REPLACE INTO ccat_user_key_value "
                        "(user_id, name, value) VALUES (?, ?, ?)",
                        (user_id, key, value),
                    )
                else:
                    cursor.execute(
                        "INSERT OR REPLACE INTO ccat_global_key_value "
                        "(name, value) VALUES (?, ?)",
                        (key, value),
                    )
            except Exception:
                pass

        conn.commit()
        conn.close()

    def _import_configuration(self, config: dict) -> None:
        """Importa la configurazione nel database Cheshire Cat."""
        import sqlite3

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        for key, value in config.items():
            if _SECRET_PATTERNS.search(key):
                continue
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO ccat_global_key_value "
                    "(name, value) VALUES (?, ?)",
                    (f"settings_{key}", json.dumps(value)),
                )
            except Exception:
                pass

        conn.commit()
        conn.close()
