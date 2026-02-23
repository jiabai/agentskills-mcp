"""Configuration helpers for the Agent Skills MCP package.

The configuration layer is built on top of FlowLLM's ``PydanticConfigParser``
and exposes a single public ``ConfigParser`` class that knows how to locate
and load agentskills-mcp specific settings.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_agentskills.config.config_parser import ConfigParser


def __getattr__(name: str):
    if name == "ConfigParser":
        from mcp_agentskills.config.config_parser import ConfigParser

        return ConfigParser
    raise AttributeError(name)


__all__ = ["ConfigParser"]
