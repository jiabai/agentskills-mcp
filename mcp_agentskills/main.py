"""CLI 入口点，负责启动 FlowLLM 独立模式。

此模块只负责命令行入口，AgentSkillsMcpApp 类已移至 core/app.py。
"""

import sys

from mcp_agentskills.core.app import AgentSkillsMcpApp


def main() -> None:
    """Run the Agent Skills MCP service as a command-line application.

    The function builds :class:`AgentSkillsMcpApp` from the command-line arguments
    (excluding the script name) and starts the FlowLLM service loop.
    """
    with AgentSkillsMcpApp(*sys.argv[1:]) as app:
        app.run_service()


if __name__ == "__main__":
    main()
