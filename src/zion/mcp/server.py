"""
Zion MCP Server.

Espone le funzionalita' di Zion come strumenti MCP (Model Context Protocol),
permettendo ad agenti AI di esportare, importare, ispezionare e misurare
lo stato portabile di un agente.

Avvio: python -m zion.mcp.server
"""

import json
import tempfile
from pathlib import Path

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP as MCPServer

from zion.export import export_state
from zion.import_ import import_state
from zion.recovery import measure_recovery, round_trip_measure
from zion.state import ZionState, inspect_state


def _create_mcp_server() -> MCPServer:
    """Crea l'istanza del server MCP compatibile con SDK vecchio e nuovo."""
    try:
        return MCPServer(
            name="zion",
            title="Zion - Stato portabile per agenti AI",
            version="0.1.0",
            instructions=(
                "Zion gestisce lo stato portabile degli agenti AI. "
                "Usa i tools per esportare, importare, ispezionare "
                "e misurare la qualita' del round-trip di stato."
            ),
        )
    except TypeError:
        return MCPServer(
            "zion",
            instructions=(
                "Zion gestisce lo stato portabile degli agenti AI. "
                "Usa i tools per esportare, importare, ispezionare "
                "e misurare la qualita' del round-trip di stato."
            ),
        )


mcp = _create_mcp_server()

_WORK_DIR = Path(tempfile.gettempdir()) / "zion-mcp"


def _parse_state(state_json: str) -> ZionState:
    """Parsa una stringa JSON in un ZionState."""
    try:
        data = json.loads(state_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON non valido: {e}") from e
    try:
        return ZionState.model_validate(data)
    except Exception as e:
        raise ValueError(f"Stato Zion non valido: {e}") from e


def _ensure_work_dir() -> Path:
    """Crea la directory di lavoro temporanea."""
    _WORK_DIR.mkdir(parents=True, exist_ok=True)
    return _WORK_DIR


def _error(msg: str) -> str:
    """Restituisce un errore JSON."""
    return json.dumps({"error": msg})


@mcp.tool()
def zion_export(state_json: str, path: str | None = None) -> str:
    """
    Esporta uno stato Zion su file JSON.

    Args:
        state_json: Stato Zion come stringa JSON.
        path: Percorso output opzionale.

    Returns:
        Percorso del file creato e dimensione.
    """
    state = _parse_state(state_json)
    if path is None:
        work_dir = _ensure_work_dir()
        name = state.identity.agent_id
        file_path = work_dir / f"{name}.json"
    else:
        file_path = Path(path)

    try:
        export_state(state, file_path)
    except Exception as e:
        return _error(f"Export fallito: {e}")

    size = file_path.stat().st_size
    return json.dumps({
        "path": str(file_path),
        "bytes": size,
        "agent_id": state.identity.agent_id,
    })


@mcp.tool()
def zion_import(path: str) -> str:
    """
    Importa uno stato Zion da un file JSON.

    Args:
        path: Percorso del file JSON.

    Returns:
        Stato Zion deserializzato.
    """
    file_path = Path(path)
    if not file_path.exists():
        return _error(f"File non trovato: {path}")

    try:
        state = import_state(file_path)
    except Exception as e:
        return _error(f"Import fallito: {e}")

    data = state.model_dump(mode="json", by_alias=True)
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
def zion_inspect(state_json: str) -> str:
    """
    Ispeziona uno stato Zion e restituisce un riepilogo.

    Args:
        state_json: Stato Zion come stringa JSON.

    Returns:
        Riepilogo con identita' e conteggi portabilita'.
    """
    try:
        state = _parse_state(state_json)
    except ValueError as e:
        return _error(str(e))

    summary = inspect_state(state)
    return json.dumps(summary, indent=2, ensure_ascii=False)


@mcp.tool()
def zion_measure(original_json: str, recovered_json: str) -> str:
    """
    Confronta due stati Zion e misura la fedelta' del recupero.

    Args:
        original_json: Stato originale come JSON.
        recovered_json: Stato recuperato come JSON.

    Returns:
        RecoveryReport con fedelta' per dimensione.
    """
    try:
        original = _parse_state(original_json)
        recovered = _parse_state(recovered_json)
    except ValueError as e:
        return _error(str(e))

    report = measure_recovery(original, recovered)
    return json.dumps({
        "overall_fidelity": report.overall_fidelity,
        "per_dimension": report.per_dimension,
        "fields_checked": report.fields_checked,
        "fields_recovered": report.fields_recovered,
        "field_losses": report.field_losses,
        "portability": report.portability,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def zion_round_trip(state_json: str, path: str | None = None) -> str:
    """
    Round-trip completo: export, import, misura fedelta'.

    Args:
        state_json: Stato Zion come JSON.
        path: Percorso opzionale per il file temporaneo.

    Returns:
        RecoveryReport con fedelta' e dimensione JSON.
    """
    try:
        state = _parse_state(state_json)
    except ValueError as e:
        return _error(str(e))

    if path is None:
        work_dir = _ensure_work_dir()
        name = state.identity.agent_id
        file_path = work_dir / f"roundtrip-{name}.json"
    else:
        file_path = Path(path)

    try:
        report = round_trip_measure(state, file_path)
    except Exception as e:
        return _error(f"Round-trip fallito: {e}")

    return json.dumps({
        "overall_fidelity": report.overall_fidelity,
        "per_dimension": report.per_dimension,
        "total_bytes": report.total_bytes,
        "fields_checked": report.fields_checked,
        "fields_recovered": report.fields_recovered,
        "field_losses": report.field_losses,
        "portability": report.portability,
    }, indent=2, ensure_ascii=False)


def main():
    """Entry point per zion-mcp."""
    import asyncio
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
