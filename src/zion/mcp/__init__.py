"""Zion MCP Server — strumenti MCP per lo stato portabile degli agenti AI.

`mcp` e' importato in lazy: un import eagerly eseguirebbe il server due
volte quando lo si lancia con `python -m zion.mcp.server` (runpy importa
il pacchetto prima del modulo).
"""

__all__ = ["mcp"]


def __getattr__(name):
    if name == "mcp":
        from zion.mcp.server import mcp
        return mcp
    raise AttributeError(f"module 'zion.mcp' has no attribute {name}")
