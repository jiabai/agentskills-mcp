# <img src="docs/figure/agentskills-logo.png" alt="Agent Skills MCP Logo" width="5%" style="vertical-align: middle;"> AgentSkills MCP: Bringing Anthropic's Agent Skills to Any MCP-compatible Agent


<p align="center">
  <strong></strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/mcp-agentskills/"><img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python Version"></a>
  <a href="https://pypi.org/project/mcp-agentskills/"><img src="https://img.shields.io/pypi/v/mcp-agentskills.svg?logo=pypi" alt="PyPI Version"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-black" alt="License"></a>
  <a href="https://github.com/zouyingcao/agentskills-mcp"><img src="https://img.shields.io/github/stars/zouyingcao/agentskills-mcp?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  简体中文 | <a href="./README.md">English</a>
</p>


## 📖 项目概览

Agent Skills是Anthropic近期推出的一个新功能，通过将专业技能封装为模块化的资源，让Claude按需转变为满足各类场景需求的“定制专家”。
AgentSkills MCP基于[FlowLLM](https://github.com/flowllm-ai/flowllm)框架，将Claude专有的Agent Skills功能解锁并开放给所有支持MCP的Agent，
模拟了Anthropic官方在其[Agent Skills工程博客](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)中提出的**渐进式披露**（**Progressive Disclosure**）设计，
让Agent按需加载必要的技能信息，从而高效利用有限的上下文窗口。

### 💡 为什么选择AgentSkills MCP?

- ✅ **零代码配置**：一键安装(``pip install mcp-agentskills`` 或 ``uv pip install mcp-agentskills``)
- ✅ **开箱即用**: 面向官方Skill格式设计，完全兼容[Anthropic的Agent Skills](https://github.com/anthropics/skills)
- ✅ **MCP支持**：多种传输方式（stdio/SSE/HTTP），适配任何支持MCP的Agent
- ✅ **Skill路径灵活**：自定义Skill目录，并自动检测、解析与加载


## 🔥 最新动态

- **[2025-12]** 🎉 发布 mcp-agentskills v0.1.0


## 🚀 快速开始
### 安装

使用 pip 安装 AgentSkills MCP：

```bash
pip install mcp-agentskills
```

或使用 uv：

```bash
uv pip install mcp-agentskills
```

<details>
<summary><strong>用于开发（若需修改代码）：</strong></summary>

```bash
git clone https://github.com/zouyingcao/agentskills-mcp.git
cd agentskills-mcp

conda create -n agentskills-mcp python==3.10
conda activate agentskills-mcp
pip install -e .
```
</details>

---
### 加载Skills

1. 创建存放Skills的目录, 比如：

```bash
mkdir skills
```

2. 从GitHub开源的仓库中克隆，比如：

```bash
https://github.com/anthropics/skills
https://github.com/ComposioHQ/awesome-claude-skills
```

3. 将收集到的Skills添加进第1步中创建的目录，每个Skill是一个文件夹，包含一个SKILL.md文件。

---

### 运行
<details>
<summary><strong>本地进程通信模式（stdio）</strong></summary>

<p align="left">
  <sub>该模式执行 `uvx` 命令直接运行 AgentSkills MCP，通过标准输入/输出进行通信，适用于本地 MCP 客户端。</sub>
</p>

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "command": "uvx",
      "args": [
        "agentskills-mcp",
        "config=default",
        "mcp.transport=stdio",
        "metadata.skill_dir=\"./skills\"",
      ],
      "env": {
        "FLOW_LLM_API_KEY": "xxx",
        "FLOW_LLM_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      }
    }
  }
}
```
</details>

<details>
<summary><strong>远程通信模式（SSE/HTTP 服务器）</strong></summary>

<p align="left">
  <sub>此模式将 AgentSkills MCP 启动为独立的 SSE/HTTP 服务器，可远程访问。</sub>
</p>

**- 步骤 1**：配置环境变量

复制 `.env.example` 到 `.env` 并填写您的 API 密钥：

```bash
cp .env.example .env
# 编辑 .env 文件并填入您的 API 密钥
```

**- 步骤 2**：启动服务器

使用 SSE 传输方式启动 AgentSkills MCP 服务器：

```bash
agentskills-mcp \
  config=default \
  mcp.transport=sse \
  mcp.host=0.0.0.0 \
  mcp.port=8001 \
  metadata.skill_dir="./skills"
```

服务将在以下地址可用：`http://0.0.0.0:8001/sse`

**- 步骤 3**：与 MCP 客户端连接

  - 在你的 MCP 客户端（Cursor、Gemini Code、Cline等）配置文件中添加以连接远程 SSE 服务器：

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "type": "sse",
      "url": "http://0.0.0.0:8001/sse"
    }
  }
}
```

  - 也可以使用 [FastMCP](https://gofastmcp.com/getting-started/welcome) 构建客户端Python直接访问服务器：

```python
import asyncio
from fastmcp import Client


async def main():
    async with Client("http://0.0.0.0:8001/sse") as client:
        tools = await client.list_tools()
        for tool in tools:
            print(tool)

        result = await client.call_tool(
            name="load_skill",
            arguments={
              "skill_name": "pdf"
            }
        )
        print(result)


asyncio.run(main())
```


#### 一键测试命令
<p align="left">
  <sub>该命令将自动启动服务器、通过 FastMCP 客户端连接，并测试所有可用工具。</sub>
</p>

```bash
python tests/run_project_sse.py <path/to/skills>
or
python tests/run_project_http.py <path/to/skills>
```

</details>

### 前端控制台

```bash
cd frontend
npm install
npm run dev
```

环境变量：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 示例Demo

当使用 SSE 传输方式启动 AgentSkills MCP 服务器后，可执行演示：
```bash
# 赋予Qwen模型Agent Skills功能
# 因为Qwen支持工具调用，可通过将AgentSkills MCP服务注册的MCP工具传入tools参数，来模拟Agent Skills功能
cd tests
python run_skill_agent.py
```


---
## 🔧 MCP 工具

本服务提供了四个用于处理 Agent Skills 的工具：
- **load_skill_metadata** - 用于启动时将所有 Skills 的名字和简短描述加载到 Agent 上下文中（始终调用）
- **load_skill** - 当判断需要某种技能时，基于其名字加载 SKILL.md 的正文（触发 Skill 时）
- **read_reference_file** - 从技能中检索特定文件，如运行脚本、参考文档等（按需）
- **run_shell_command** - 代码执行工具，用于 Shell 命令运行技能中的可执行脚本（按需）

详细参数和使用示例，请参阅[文档](docs/tools.md)。


## ⚙️ 服务器配置参数

| 参数                     | 描述                                                                                                                                                                                         | 示例                                              |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `config`                 | 要加载的配置文件（逗号分隔）。默认为：`default`（核心流程）                                        | `config=default`                              |
| `mcp.transport`          | 传输模式：`stdio`（标准输入/输出，适合本地）、`sse`（Server-Sent Events，适合在线应用）、`http`（RESTful，适合轻量远程调用）                                                                                               | `mcp.transport=stdio`                             |
| `mcp.host`               | 主机地址（仅用于 sse/http 传输）                                                                                                                                                             | `mcp.host=0.0.0.0`                                |
| `mcp.port`               | 端口号（仅用于 sse/http 传输）                                                                                                                                                               | `mcp.port=8001`                                   |
| `metadata.skill_dir`               | Skills的存放目录（必需） | `metadata.skill_dir=./skills`                                   |
<!-- | `llm.default.model_name` | 默认 LLM 模型名称（会覆盖配置文件中的设置）                                                                                                                                                  | `llm.default.model_name=qwen3-30b-a3b-thinking-2507` | -->


完整配置选项及默认值，请参阅 [default.yaml](./agentskills_mcp/config/default.yaml)。

#### 环境变量

| 变量名                   | 是否必需 | 描述                                     |
|--------------------------|----------|------------------------------------------|
| `FLOW_LLM_API_KEY`       | ✅ 是     | OpenAI 兼容 LLM 服务的 API 密钥          |
| `FLOW_LLM_BASE_URL`      | ✅ 是     | OpenAI 兼容 LLM 服务的基础 URL           |

---


## 🤝 贡献指南

我们欢迎社区贡献！开始贡献的步骤如下：

1. 以开发模式安装本项目：
```bash
pip install -e .
```

2. 提交 Pull Request。

---

## 📚 学习资料

- [Anthropic 官方Agent Skills文档](https://code.claude.com/docs/zh-CN/skills)
- [Anthropic 工程博客](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [从第一性原理深度拆解 Claude Agent Skill](https://baoyu.io/translations/claude-skills-deep-dive)
- [FlowLLM 学习文档](https://flowllm-ai.github.io/flowllm/)
- [MCP 文档](https://modelcontextprotocol.io/docs/getting-started/intro)

## ⚖️ 许可证

本项目采用 Apache License 2.0 许可证 —— 详情请参见 [LICENSE](./LICENSE) 文件。

---

## 📈 Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=zouyingcao/agentskills-mcp&type=Date)](https://www.star-history.com/#zouyingcao/agentskills-mcp&Date)
