"""
Zion MCP Server.

Espone le funzionalita' di Zion come strumenti MCP (Model Context Protocol),
permettendo ad agenti AI di esportare, importare, ispezionare, misurare
lo stato portabile di un agente e di annotare/richiamare ricordi mentre
agiscono.

Avvio: python -m zion.mcp.server
"""

import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from mcp.server.mcpserver import MCPServer
from pydantic import ValidationError

from zion.export import export_state
from zion.import_ import import_state
from zion.models import AgentIdentity, MemoryEntry, ProjectState
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
                "e misurare la qualita' del round-trip di stato, "
                "e zion_remember/zion_recall per annotare e cercare "
                "ricordi durante l'azione."
            ),
        )
    except TypeError:
        return MCPServer(
            "zion",
            instructions=(
                "Zion gestisce lo stato portabile degli agenti AI. "
                "Usa i tools per esportare, importare, ispezionare "
                "e misurare la qualita' del round-trip di stato, "
                "e zion_remember/zion_recall per annotare e cercare "
                "ricordi durante l'azione."
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


def _safe_filename(value: str) -> str:
    """Riduce un id a nome file sicuro: niente separatori di percorso."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return name or "zion-state"


def _allowed_roots() -> list[Path]:
    """Root dentro le quali un path esplicito viene accettato."""
    return [Path(tempfile.gettempdir()), Path.cwd(), Path.home()]


def _resolve_allowed_path(value: str) -> Path | None:
    """Risolve il path e lo accetta solo se cade dentro una root consentita."""
    candidate = Path(value).expanduser().resolve()
    for root in _allowed_roots():
        if candidate.is_relative_to(root.resolve()):
            return candidate
    return None


def _path_error(value: str) -> str:
    """Errore JSON per un path fuori dalle root consentite."""
    roots = ", ".join(str(root) for root in _allowed_roots())
    return _error(f"Path non consentito: {value}. Root ammesse: {roots}")


def _store_path(agent_id: str) -> Path:
    """File dello stato vivo di un agente, dentro la work dir."""
    return _ensure_work_dir() / f"{_safe_filename(agent_id)}.json"


def _load_or_create_state(agent_id: str) -> tuple[ZionState, bool]:
    """Carica lo stato vivo dell'agente; se assente ne crea uno minimo.

    Restituisce (stato, True se appena creato). La creazione non scrive
    nulla su disco: il primo salvataggio lo fa zion_remember alla fine.
    """
    path = _store_path(agent_id)
    if path.exists():
        return import_state(path), False
    state = ZionState(
        identity=AgentIdentity(agent_id=agent_id, name=agent_id, version="unknown"),
        project=ProjectState(id="", name=""),
    )
    return state, True


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
        file_path = work_dir / f"{_safe_filename(state.identity.agent_id)}.json"
    else:
        resolved = _resolve_allowed_path(path)
        if resolved is None:
            return _path_error(path)
        file_path = resolved

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
    resolved = _resolve_allowed_path(path)
    if resolved is None:
        return _path_error(path)

    file_path = resolved
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
        file_path = work_dir / f"roundtrip-{_safe_filename(state.identity.agent_id)}.json"
    else:
        resolved = _resolve_allowed_path(path)
        if resolved is None:
            return _path_error(path)
        file_path = resolved

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


@mcp.tool()
def zion_remember(
    agent_id: str,
    content: str,
    context: str | None = None,
    salience: float = 0.5,
    occurred_at: str | None = None,
    links: list[dict] | None = None,
) -> str:
    """
    Annota un ricordo nello stato vivo dell'agente, mentre agisce.

    Non serve un export: il ricordo viene salvato subito nel file di stato
    dell'agente. L'export resta un'operazione di distribuzione.

    Args:
        agent_id: Identita' dell'agente (usata come nome file, sanificata).
        content: Testo del ricordo.
        context: Situazione in cui il ricordo e' stato fissato.
        salience: Peso del ricordo, 0.0-1.0 (default 0.5).
        occurred_at: Quando l'evento e' successo, ISO 8601 (default: adesso).
        links: Collegamenti ad altri ricordi [{target, relation}].

    Returns:
        L'id del ricordo, il conteggio memorie e il percorso del file.
    """
    if not content.strip():
        return _error("content vuoto: un ricordo senza contenuto non serve")

    try:
        when = datetime.fromisoformat(occurred_at) if occurred_at else datetime.now()
    except ValueError:
        return _error(f"occurred_at non e' un timestamp ISO valido: {occurred_at}")

    state, created = _load_or_create_state(agent_id)
    try:
        memory = MemoryEntry.model_validate({
            "id": f"mem-{uuid4().hex}",
            "content": content,
            "created_at": datetime.now(),
            "occurred_at": when,
            "salience": salience,
            "context": context,
            "links": links or [],
        })
    except ValidationError as e:
        return _error(f"Ricordo non valido: {e}")

    state.memory.append(memory)
    path = _store_path(agent_id)
    try:
        export_state(state, path)
    except Exception as e:
        return _error(f"Salvataggio fallito: {e}")

    return json.dumps({
        "agent_id": agent_id,
        "id": memory.id,
        "path": str(path),
        "memory_count": len(state.memory),
        "created": created,
    }, ensure_ascii=False)


@mcp.tool()
def zion_recall(agent_id: str, query: str = "", limit: int = 5) -> str:
    """
    Cerca nei ricordi dell'agente, senza passare per un export.

    Ricerca testuale tra i contenuti e i contesti (maiuscole/minuscole
    ignorate). Con query vuota restituisce i ricordi piu' salienti.

    Args:
        agent_id: Identita' dell'agente di cui leggere lo stato vivo.
        query: Testo da cercare; vuoto = tutti i ricordi.
        limit: Numero massimo di risultati (default 5).

    Returns:
        Numero totale di corrispondenze e i ricordi trovati, ordinati per
        salienza decrescente e, a parita', dal piu' recente.
    """
    if limit < 1:
        return _error(f"limit deve essere almeno 1, ricevuto {limit}")

    path = _store_path(agent_id)
    if not path.exists():
        return _error(
            f"Nessuno stato vivo per '{agent_id}': "
            "annota con zion_remember o esporta prima uno stato"
        )

    try:
        state = import_state(path)
    except Exception as e:
        return _error(f"Lettura fallita: {e}")

    needle = query.strip().lower()
    matches = [
        memory for memory in state.memory
        if not needle
        or needle in memory.content.lower()
        or (memory.context is not None and needle in memory.context.lower())
    ]
    matches.sort(key=lambda m: (m.salience, m.occurred_at), reverse=True)

    results = [
        {
            "id": memory.id,
            "content": memory.content,
            "context": memory.context,
            "occurred_at": memory.occurred_at.isoformat(),
            "created_at": memory.created_at.isoformat(),
            "salience": memory.salience,
            "links": [link.model_dump() for link in memory.links],
            "portability": memory.portability,
        }
        for memory in matches[:limit]
    ]

    return json.dumps({
        "agent_id": agent_id,
        "query": query,
        "matches": len(matches),
        "results": results,
    }, ensure_ascii=False, indent=2)


def main():
    """Entry point per zion-mcp."""
    import asyncio

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
