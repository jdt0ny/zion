"""Sessione MCP reale via stdio: un agente lascia traccia senza export.

Qui non si chiama la funzione in-process: si avvia `python -m zion.mcp.server`
come processo separato, si negozia il protocollo MCP e si invocano i tool come
li invocherebbe un client vero. La persistenza viene verificata riavviando il
processo: se la traccia sopravvive a un riavvio senza export, il ciclo di vita
non dipende da un salvataggio manuale.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

AGENT = "agente-e2e"
TIMEOUT = 30


def _server_params(work_dir: Path) -> StdioServerParameters:
    """Server con la sua work dir: TMPDIR isola i file di stato."""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "zion.mcp.server"],
        env={**os.environ, "TMPDIR": str(work_dir)},
    )


def _text(result) -> str:
    """Testo restituito da call_tool, con errore se il tool ha fallito."""
    chunks = [c.text for c in result.content if getattr(c, "type", None) == "text"]
    assert not result.is_error, f"tool in errore: {''.join(chunks)}"
    return "".join(chunks)


async def _remember(params, **kwargs) -> dict:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return json.loads(_text(await session.call_tool("zion_remember", kwargs)))


async def _recall(params, **kwargs) -> dict:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return json.loads(_text(await session.call_tool("zion_recall", kwargs)))


async def _scenario(work_dir: Path) -> dict:
    params = _server_params(work_dir)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = {tool.name for tool in (await session.list_tools()).tools}
            assert {"zion_export", "zion_remember", "zion_recall"} <= tools

            saved = json.loads(_text(await session.call_tool(
                "zion_remember",
                {
                    "agent_id": AGENT,
                    "content": "ho avviato il server MCP per un test reale",
                    "context": "sessione via stdio",
                    "salience": 0.9,
                },
            )))
            assert "error" not in saved

            found = json.loads(_text(await session.call_tool(
                "zion_recall",
                {"agent_id": AGENT, "query": "stdio"},
            )))

    # Processo terminato, nessun export: la traccia deve restare.
    restarted = await _recall(params, agent_id=AGENT, query="MCP")
    return {"saved": saved, "found": found, "restarted": restarted}


def test_agent_leaves_a_trace_without_export(tmp_path):
    result = asyncio.run(asyncio.wait_for(_scenario(tmp_path), timeout=TIMEOUT))

    assert result["saved"]["memory_count"] == 1
    assert result["saved"]["created"] is True

    assert result["found"]["matches"] == 1
    entry = result["found"]["results"][0]
    assert entry["salience"] == 0.9
    assert entry["context"] == "sessione via stdio"

    # Il processo-server è stato riavviato e la ricerca trova ancora il ricordo.
    assert result["restarted"]["matches"] == 1
    assert result["restarted"]["results"][0]["content"] == (
        "ho avviato il server MCP per un test reale"
    )


def test_recall_on_a_fresh_process_without_state(tmp_path):
    """Un processo nuovo senza stato dichiara di non averlo, non inventa."""
    params = _server_params(tmp_path)
    outcome = asyncio.run(asyncio.wait_for(_fresh_recall(params), timeout=TIMEOUT))
    assert "error" in outcome


async def _fresh_recall(params) -> dict:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return json.loads(_text(await session.call_tool(
                "zion_recall",
                {"agent_id": "nessuno", "query": "x"},
            )))


def test_remember_rejects_bad_salience_over_the_wire(tmp_path):
    params = _server_params(tmp_path)
    outcome = asyncio.run(asyncio.wait_for(
        _remember(params, agent_id=AGENT, content="x", salience=9.0),
        timeout=TIMEOUT,
    ))
    assert "error" in outcome
    assert not list(tmp_path.glob("*.json"))
