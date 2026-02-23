# Tool Documentation

> **当前版本**: v2.0（多用户版本）
>
> 本文档描述支持用户隔离的 MCP 工具接口。与单用户版本相比，主要区别在于支持用户隔离的 Skill 路径。

---

## 版本历史

| 版本 | 描述 | 主要变更 |
|------|------|---------|
| **v2.0** (当前) | 多用户版本 | 支持用户隔离、API Token 认证、私有 Skill 空间 |
| v1.0 | 单用户版本 | 原始版本，无用户隔离 |

---

## 版本差异

| 特性 | 单用户版本 | 多用户版本 |
|------|-----------|-----------|
| Skill路径 | `{skill_dir}/{skill_name}/` | `{skill_dir}/{user_id}/{skill_name}/` |
| 用户隔离 | 无 | 每个用户独立的Skill空间 |
| 认证方式 | 无 | API Token认证 |
| 向后兼容 | - | 支持（无user_id时使用全局路径） |

---

AgentSkills MCP utilizes four tools to load Agent Skills, following the descriptions in [Anthropic's Agent Skills Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) to implement *Progressive Disclosure* architecture.

---

## Tool 1: load_skill_metadata_op

<p align="left">
  <em>Load metadata from all available skills (always call at task start).</em>
</p>

### Description

This tool scans the skills directory recursively for SKILL.md files and extracts their metadata (name and description) from YAML frontmatter.

**多用户版本**: 当存在 `user_id` 时，仅扫描该用户的私有Skill目录；否则扫描全局Skill目录。

### Key Operation Flow

- Gets the skills directory path from the context
- **多用户**: 从请求级上下文获取 `user_id`（通过 `contextvars`）
- **多用户**: 根据用户ID确定搜索目录: `{skill_dir}/{user_id}/` 或 `{skill_dir}/`
- Recursively searches for all SKILL.md files
- Parses each file's frontmatter to extract metadata
- Builds a dictionary with skill names as keys
- Sets the output with the complete metadata dictionary

### Input Parameters

This tool requires no input parameters.

**多用户版本内部逻辑**:
```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

user_id = get_current_user_id()  # 从请求级上下文获取
skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

if user_id:
    search_dir = skill_dir / user_id  # 用户私有目录
else:
    search_dir = skill_dir            # 全局目录（向后兼容）
```

> **注意**: `user_id` 是在 MCP 认证中间件中通过 `contextvars` 注入到请求级上下文的。每个 HTTP 请求会根据 API Token 自动识别用户身份，确保多用户并发访问时的安全隔离。详见 [project-spec.md](./project-spec.md#62-并发安全机制)。

### Returns

str: A string containing the skill metadata in the format:
```
Available skills (each line is "- <skill_name>: <skill_description>"):
- skill_name_1: Skill description 1
- skill_name_2: Skill description 2
...
```

### Test Demo

```bash
python tests/test_load_skill_metadata_op.py <path/to/skills>
```

---

## Tool 2: `load_skill_op`

<p align="left">
  <em>Load a specific skill's instructions (i.e., SKILL.md).</em>
</p>

### Description

This tool loads the content of a SKILL.md file for a given skill name.

**多用户版本**: 根据用户ID构建正确的Skill路径。

### Key Operation Flow

- Takes a skill_name as input
- **多用户**: 从上下文获取 `user_id`
- **多用户**: 构建路径: `{skill_dir}/{user_id}/{skill_name}/SKILL.md` 或 `{skill_dir}/{skill_name}/SKILL.md`
- Reads the SKILL.md file from that directory
- Returns the file content

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_name` | string | Yes | - | Name of the skill |

**多用户版本内部逻辑**:
```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

skill_name = self.input_dict["skill_name"]
user_id = get_current_user_id()  # 从请求级上下文获取
skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

if user_id:
    skill_path = skill_dir / user_id / skill_name / "SKILL.md"
else:
    skill_path = skill_dir / skill_name / "SKILL.md"
```

### Returns

str: The skill instructions content. If the SKILL.md file exists, returns the file content. Otherwise, returns an error message string.

> [!TIP]
> You can ref to [official Anthropic documentation](https://code.claude.com/docs/en/skills) on the Skills format.

### Test Demo

```bash
python tests/test_load_skill_op.py <path/to/skills> <skill_name>
```

---

## Tool 3: read_reference_file_op

<p align="left">
  <em>Read reference files from a skill directory.</em>
</p>

### Description

This tool allows reading reference files like forms.md, reference.md, or ooxml.md from a specific skill's directory.

**多用户版本**: 根据用户ID构建正确的文件路径。

### Key Operation Flow

- Takes a skill_name and file_name as input
- **多用户**: 从上下文获取 `user_id`
- **多用户**: 构建路径: `{skill_dir}/{user_id}/{skill_name}/{file_name}` 或 `{skill_dir}/{skill_name}/{file_name}`
- Reads the file content if it exists
- Returns the file content or an error message if not found

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_name` | string | Yes | - | Name of the skill |
| `file_name` | string | Yes | - | The reference file name or file path relative to the skill directory |

**多用户版本内部逻辑**:
```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

skill_name = self.input_dict["skill_name"]
file_name = self.input_dict["file_name"]
user_id = get_current_user_id()  # 从请求级上下文获取
skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

if user_id:
    file_path = skill_dir / user_id / skill_name / file_name
else:
    file_path = skill_dir / skill_name / file_name
```

### Returns

str: The content of the reference file read from the skill directory. If the file is not found, returns an error message string indicating that the file was not found in the specified skill.

### Test Demo

```bash
python tests/test_reference_file_op.py <path/to/skills> <skill_name> <file_name>
```

---

## Tool 4: run_shell_command_op

<p align="left">
  <em>Execute shell commands to run scripts within skill directories.</em>
</p>

### Description

This tool executes shell commands and can automatically detect and install dependencies for script files (Python, JavaScript, Shell). The command is executed in the skill's directory context, allowing scripts to access skill-specific files and resources.

**多用户版本**: 在用户私有的Skill目录中执行命令。

### Key Operation Flow

- Extract skill_name and command from input
- **多用户**: 从上下文获取 `user_id`
- **多用户**: 确定工作目录: `{skill_dir}/{user_id}/{skill_name}/` 或 `{skill_dir}/{skill_name}/`
- For Python commands, automatically detect and install dependencies using pipreqs (if available and auto_install_deps parameter is enabled)
- Execute the command in a subprocess and capture stdout/stderr
- Return the combined output (stdout + stderr)

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_name` | string | Yes | - | Name of the skill |
| `command` | string | Yes | - | The shell command to execute |

**多用户版本内部逻辑**:
```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

skill_name = self.input_dict["skill_name"]
command = self.input_dict["command"]
user_id = get_current_user_id()  # 从请求级上下文获取
skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

if user_id:
    work_dir = skill_dir / user_id / skill_name
else:
    work_dir = skill_dir / skill_name
```

### Returns

str: The combined stdout and stderr output from the command execution. The output is decoded as UTF-8 and formatted as: "{stdout}\n{stderr}".

> [!NOTE]
> Dependency auto-installation only occurs for commands containing "py" and when the auto_install_deps parameter is enabled.
> The command runs in the skill's directory, allowing access to skill-specific files and resources.

### Test Demo

```bash
python tests/test_run_shell_command_op.py <path/to/skills> <skill_name> <command>
```

---

## 多用户版本使用示例

### MCP客户端配置

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "type": "http",
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer ask_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### 认证流程

1. 用户通过 `/api/v1/auth/login` 获取 JWT Token
2. 通过 `/api/v1/tokens` 创建 API Token
3. 使用 API Token 访问 MCP 服务
4. MCP 服务自动识别用户身份，访问其私有 Skill 空间

> **并发安全**: API Token 验证成功后，用户 ID 会通过 `contextvars` 注入到请求级上下文。这意味着每个并发请求都能正确识别自己的用户身份，不会相互干扰。详见 [project-spec.md](./project-spec.md#62-并发安全机制)。

### Skill 隔离机制

```
/data/skills/
├── {user_id_1}/
│   ├── pdf/
│   │   ├── SKILL.md
│   │   └── reference.md
│   └── xlsx/
│       └── SKILL.md
├── {user_id_2}/
│   └── pdf/
│       └── SKILL.md
└── ...
```

每个用户只能访问自己目录下的 Skills，确保数据隔离和安全性。
