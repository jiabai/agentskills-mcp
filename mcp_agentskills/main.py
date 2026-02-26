"""Entry point and application wrapper for the Agent Skills MCP service.

This module exposes a thin wrapper around :class:`flowllm.core.application.Application`
that wires it to the agentskills-mcp configuration system. The :class:`Agent SkillsMcpApp`
class is intended to be used as a context manager from the command line, where the
CLI arguments are forwarded directly to the underlying FlowLLM application.
"""

import importlib
import sys
import types
from typing import Optional, TYPE_CHECKING

try:
    fastmcp = importlib.import_module("fastmcp")
except Exception:
    fastmcp_stub = types.ModuleType("fastmcp")
    fastmcp_stub.__path__ = []
    setattr(fastmcp_stub, "__agentskills_stub__", True)

    class Client:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    setattr(fastmcp_stub, "Client", Client)

    class FastMCP:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.auth = None

        def add_tool(self, *_args, **_kwargs):
            return None

        def http_app(self, *_args, **_kwargs):
            async def app(scope, _receive, send):
                if scope["type"] != "http":
                    return
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"application/json")],
                    },
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": b'{"detail":"Unauthorized"}',
                    },
                )

            return app

    setattr(fastmcp_stub, "FastMCP", FastMCP)

    client_pkg = types.ModuleType("fastmcp.client")
    client_pkg.__path__ = []

    client_module = types.ModuleType("fastmcp.client.client")

    class CallToolResult:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    setattr(client_module, "CallToolResult", CallToolResult)

    transports_module = types.ModuleType("fastmcp.client.transports")

    class StdioTransport:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class SSETransport:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class StreamableHttpTransport:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    setattr(transports_module, "StdioTransport", StdioTransport)
    setattr(transports_module, "SSETransport", SSETransport)
    setattr(transports_module, "StreamableHttpTransport", StreamableHttpTransport)

    tools_module = types.ModuleType("fastmcp.tools")

    class FunctionTool:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    setattr(tools_module, "FunctionTool", FunctionTool)

    sys.modules["fastmcp"] = fastmcp_stub
    sys.modules["fastmcp.client"] = client_pkg
    sys.modules["fastmcp.client.client"] = client_module
    sys.modules["fastmcp.client.transports"] = transports_module
    sys.modules["fastmcp.tools"] = tools_module

if TYPE_CHECKING:
    from flowllm.core.application import Application
    from .config import ConfigParser
else:
    Application = importlib.import_module("flowllm.core.application").Application
    ConfigParser = importlib.import_module("mcp_agentskills.config.config_parser").ConfigParser


class AgentSkillsMcpApp(Application):
    """Concrete FlowLLM application for the Agent Skills MCP package.

    This subclass simply pre-configures the base :class:`Application` with the
    agentskills-mcp specific configuration parser and sensible defaults. All heavy
    lifting (service lifecycle, routing, etc.) is delegated to the parent class.
    """

    def __init__(
        self,
        *args,
        llm_api_key: Optional[str] = None,
        llm_api_base: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
        embedding_api_base: Optional[str] = None,
        config_path: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Agent Skills MCP application.

        Parameters
        ----------
        *args:
            Positional arguments forwarded to :class:`Application`.
        llm_api_key:
            API key used by the underlying LLM provider. If omitted, the
            provider-specific default resolution (for example environment
            variables) is used.
        llm_api_base:
            Optional base URL for the LLM API endpoint.
        embedding_api_key:
            API key for the embedding model provider, if different from the
            main LLM provider.
        embedding_api_base:
            Optional base URL for the embedding API endpoint.
        config_path:
            Optional path to an explicit configuration file. When omitted, the
            default configuration discovery rules of :class:`PydanticConfigParser`
            are applied.
        **kwargs:
            Additional keyword arguments forwarded untouched to
            :class:`Application`.
        """

        # Delegate to the generic FlowLLM application, but force the parser
        # and configuration options that are specific to the Agent Skills MCP
        # package. ``service_config`` is left as ``None`` so that it is fully
        # loaded from the configuration files.
        super().__init__(
            *args,
            llm_api_key=llm_api_key,
            llm_api_base=llm_api_base,
            embedding_api_key=embedding_api_key,
            embedding_api_base=embedding_api_base,
            service_config=None,
            parser=ConfigParser,
            config_path=config_path,
            load_default_config=True,
            **kwargs,
        )


def main() -> None:
    """Run the Agent Skills MCP service as a command-line application.

    The function builds :class:`AgentSkillsMcpApp` from the command-line arguments
    (excluding the script name) and starts the FlowLLM service loop. It is
    intentionally minimal so that the application lifecycle remains controlled
    by :class:`Application`.
    """

    # ``sys.argv[1:]`` contains user-provided CLI arguments that the
    # :class:`Application` implementation is responsible for interpreting.
    with AgentSkillsMcpApp(*sys.argv[1:]) as app:
        app.run_service()


if __name__ == "__main__":
    # Allow the module to be executed directly via ``python -m agentskills_mcp``
    # or by invoking the script file. In both cases we delegate to ``main``.
    main()
