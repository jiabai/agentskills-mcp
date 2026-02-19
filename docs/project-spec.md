# AgentSkills MCP 多用户Web服务改造规范

> 本文档定义了将 AgentSkills MCP 从单用户服务改造为多用户Web服务的完整技术规范。

---

## 1. 项目概述

### 1.1 改造目标

将现有的单用户MCP服务改造为支持多用户的Web服务平台，实现以下核心功能：

| 功能模块 | 描述 | 优先级 |
|---------|------|--------|
| 用户账户管理 | 注册、登录、认证、账户删除 | P0 |
| 私有Skill空间 | 每个用户独立管理自己的Agent Skills | P0 |
| MCP服务认证 | 通过私有Token访问MCP服务 | P0 |

### 1.2 技术选型

| 层级 | 技术栈 | 版本要求 |
|------|--------|---------|
| Web框架 | FastAPI | >=0.109.0 |
| ORM | SQLAlchemy 2.0 | >=2.0.0 |
| 数据库 | PostgreSQL | >=14.0 |
| 认证 | python-jose + passlib | 最新版 |
| 文件存储 | 本地文件系统 | - |
| MCP框架 | FlowLLM | >=0.2.0.7 |
| 异步支持 | asyncio + asyncpg | 最新版 |

### 1.3 兼容性要求

- 保持现有MCP工具核心逻辑不变
- 保持对现有Skill格式的完全兼容
- 支持stdio/SSE/HTTP三种传输模式

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│  FastAPI + Middleware (CORS, Auth, Rate Limit, Logging)     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  AuthService | UserService | SkillService | MCPService      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│  SQLAlchemy ORM + Async Engine + Repositories               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│  PostgreSQL (Metadata) + File System (Skill Files)          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 用户Skill隔离

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

---

## 3. 数据模型

### 3.1 User 模型

```python
class User:
    id: UUID              # 主键
    email: str            # 唯一，用于登录
    username: str         # 唯一，显示名称
    hashed_password: str  # bcrypt哈希密码
    is_active: bool       # 账户状态
    is_superuser: bool    # 超级管理员标识
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
```

### 3.2 Skill 模型

```python
class Skill:
    id: UUID              # 主键
    user_id: UUID         # 外键，关联User
    name: str             # Skill名称
    description: str      # Skill描述
    skill_dir: str        # 文件存储路径
    is_active: bool       # 状态
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
    
    # 唯一约束: (user_id, name)
```

### 3.3 APIToken 模型

```python
class APIToken:
    id: UUID              # 主键
    user_id: UUID         # 外键，关联User
    name: str             # Token名称
    token_hash: str       # Token的SHA256哈希
    is_active: bool       # 状态
    expires_at: datetime  # 过期时间（可选）
    last_used_at: datetime # 最后使用时间
    created_at: datetime  # 创建时间
```

---

## 4. API 接口规范

### 4.1 认证模块 `/api/v1/auth`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/register` | POST | 否 | 用户注册 |
| `/login` | POST | 否 | 用户登录，返回JWT |
| `/refresh` | POST | 是 | 刷新Access Token |
| `/logout` | POST | 是 | 登出（可选实现Token黑名单） |

### 4.2 用户模块 `/api/v1/users`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/me` | GET | 是 | 获取当前用户信息 |
| `/me` | PUT | 是 | 更新用户信息 |
| `/me` | DELETE | 是 | 删除账户（需密码确认） |
| `/me/password` | PUT | 是 | 修改密码 |

### 4.3 Token模块 `/api/v1/tokens`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | 是 | 列出用户的所有API Token |
| `/` | POST | 是 | 创建新的API Token |
| `/{token_id}` | DELETE | 是 | 删除指定API Token |

### 4.4 Skill模块 `/api/v1/skills`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | 是 | 列出用户的Skills（分页） |
| `/` | POST | 是 | 创建新Skill |
| `/{skill_id}` | GET | 是 | 获取Skill详情 |
| `/{skill_id}` | PUT | 是 | 更新Skill信息 |
| `/{skill_id}` | DELETE | 是 | 删除Skill |
| `/upload` | POST | 是 | 上传Skill文件（multipart） |
| `/{skill_id}/files` | GET | 是 | 列出Skill文件 |

### 4.5 MCP模块

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/mcp` | POST | API Token | HTTP MCP端点 |
| `/sse` | GET | API Token | SSE MCP端点 |

---

## 5. 认证机制

### 5.1 JWT认证（Web API）

- **Access Token**: 有效期30分钟，用于API访问
- **Refresh Token**: 有效期7天，用于刷新Access Token
- **算法**: HS256
- **Header**: `Authorization: Bearer {access_token}`

### 5.2 API Token认证（MCP服务）

- **格式**: `ask_live_{64位随机hex}`
- **存储**: 仅存储SHA256哈希值
- **Header**: `Authorization: Bearer {api_token}`
- **过期**: 可选设置过期时间

### 5.3 Token生成示例

```python
# API Token格式
token = "ask_live_" + secrets.token_hex(32)
# 示例: ask_live_a1b2c3d4e5f6...（共72字符）
```

---

## 6. MCP工具改造

### 6.1 改造原则

现有MCP工具需要支持用户隔离，核心改动：

1. 从上下文获取 `user_id`
2. 根据用户ID构建Skill路径
3. 保持向后兼容（无user_id时使用全局路径）

### 6.2 LoadSkillOp 改造

```python
async def async_execute(self):
    skill_name = self.input_dict["skill_name"]
    user_id = C.service_config.metadata.get("user_id")
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()
    
    if user_id:
        skill_path = skill_dir / user_id / skill_name / "SKILL.md"
    else:
        skill_path = skill_dir / skill_name / "SKILL.md"
    
    # ... 其余逻辑不变
```

### 6.3 LoadSkillMetadataOp 改造

```python
async def async_execute(self):
    user_id = C.service_config.metadata.get("user_id")
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()
    
    if user_id:
        search_dir = skill_dir / user_id
    else:
        search_dir = skill_dir
    
    # ... 其余逻辑不变
```

### 6.4 ReadReferenceFileOp 改造

```python
async def async_execute(self):
    skill_name = self.input_dict["skill_name"]
    file_name = self.input_dict["file_name"]
    user_id = C.service_config.metadata.get("user_id")
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()
    
    if user_id:
        file_path = skill_dir / user_id / skill_name / file_name
    else:
        file_path = skill_dir / skill_name / file_name
    
    # ... 其余逻辑不变
```

### 6.5 RunShellCommandOp 改造

```python
async def async_execute(self):
    skill_name = self.input_dict["skill_name"]
    command = self.input_dict["command"]
    user_id = C.service_config.metadata.get("user_id")
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()
    
    if user_id:
        work_dir = skill_dir / user_id / skill_name
    else:
        work_dir = skill_dir / skill_name
    
    # ... 其余逻辑不变
```

---

## 7. 项目结构

```
mcp_agentskills/
├── __init__.py
├── main.py                      # FastAPI应用入口
├── config/
│   ├── __init__.py
│   ├── config_parser.py         # 配置解析器（保留）
│   ├── default.yaml             # 默认配置（扩展）
│   └── settings.py              # Pydantic Settings
├── core/
│   ├── __init__.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── jwt.py               # JWT工具
│   │   ├── password.py          # 密码哈希
│   │   └── token.py             # API Token生成
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证中间件
│   │   └── rate_limit.py        # 限流中间件
│   ├── tools/                   # MCP工具（改造）
│   │   ├── __init__.py
│   │   ├── load_skill_metadata_op.py
│   │   ├── load_skill_op.py
│   │   ├── read_reference_file_op.py
│   │   └── run_shell_command_op.py
│   └── utils/
│       ├── __init__.py
│       ├── service_runner.py
│       └── skill_storage.py     # Skill存储工具
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── skill.py
│   └── token.py
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   ├── skill.py
│   ├── token.py
│   └── response.py
├── repositories/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── skill.py
│   └── token.py
├── services/
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── skill.py
│   └── mcp.py
├── api/
│   ├── __init__.py
│   ├── deps.py
│   ├── router.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── skills.py
│   │   └── tokens.py
│   └── mcp/
│       ├── __init__.py
│       ├── auth.py
│       ├── http_handler.py
│       └── sse_handler.py
└── db/
    ├── __init__.py
    ├── session.py
    └── migrations/
```

---

## 8. 配置规范

### 8.1 环境变量

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentskills

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]

# 存储
SKILL_STORAGE_PATH=/data/skills

# LLM
FLOW_LLM_API_KEY=your-api-key
FLOW_LLM_BASE_URL=https://api.openai.com/v1
```

### 8.2 Settings类

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["*"]
    SKILL_STORAGE_PATH: str = "/data/skills"
    FLOW_LLM_API_KEY: str = ""
    FLOW_LLM_BASE_URL: str = ""
```

---

## 9. 安全要求

### 9.1 密码安全

- 使用bcrypt进行密码哈希
- 最小密码长度8位
- 建议包含大小写字母、数字、特殊字符

### 9.2 Token安全

- API Token仅在创建时显示一次
- 存储SHA256哈希值而非明文
- 支持Token过期和撤销

### 9.3 文件上传安全

- 验证文件类型
- 限制单文件大小（建议10MB）
- 限制总上传大小（建议100MB）
- 防止路径遍历攻击

### 9.4 API安全

- 所有用户API需要JWT认证
- MCP API需要API Token认证
- 实现请求限流

---

## 10. 错误处理

### 10.1 标准错误响应格式

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### 10.2 HTTP状态码规范

| 状态码 | 场景 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无返回内容） |
| 400 | 请求参数错误 |
| 401 | 未认证或Token无效 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如邮箱已存在） |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |

---

## 11. 测试要求

### 11.1 测试覆盖率

- 单元测试覆盖率 >= 80%
- 核心业务逻辑覆盖率 >= 90%

### 11.2 测试类型

- 单元测试：Services、Repositories
- 集成测试：API端点
- E2E测试：完整用户流程

### 11.3 测试数据库

使用内存SQLite进行测试：
```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

---

## 12. 部署要求

### 12.1 Docker支持

- 提供Dockerfile
- 提供docker-compose.yml（包含PostgreSQL）

### 12.2 数据库迁移

- 使用Alembic进行数据库迁移
- 提供初始化迁移脚本

### 12.3 健康检查

- 提供 `/health` 端点
- 检查数据库连接状态

---

## 附录

### A. MCP客户端配置示例

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "type": "http",
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer ask_live_xxx..."
      }
    }
  }
}
```

### B. 文件命名规范

- 模型文件：`models/{name}.py`
- Schema文件：`schemas/{name}.py`
- Repository文件：`repositories/{name}.py`
- Service文件：`services/{name}.py`
- API文件：`api/v1/{name}.py`

### C. 代码风格

- 使用ruff进行代码格式化
- 使用mypy进行类型检查
- 行长度限制：100字符
