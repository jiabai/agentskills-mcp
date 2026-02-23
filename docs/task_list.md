# AgentSkills MCP 多用户Web服务改造 - 任务列表

> 本文档定义了项目改造的详细任务分解，按阶段和优先级组织。

---

## Phase 1: 基础设施搭建

### 1.1 项目配置

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T1.1.1 | 创建配置模块 | 创建 `config/settings.py`，定义 Pydantic Settings | 无 | ⬜ |
| T1.1.2 | 更新依赖配置 | 更新 `pyproject.toml`，添加新依赖 (使用 PyJWT) | T1.1.1 | ⬜ |
| T1.1.3 | 创建环境变量模板 | 创建 `.env.example` 文件 | T1.1.1 | ⬜ |
| T1.1.4 | 扩展 default.yaml | 添加用户隔离相关配置 | T1.1.1 | ⬜ |
| T1.1.5 | 创建辅助脚本 | 创建 `scripts/checklist_stats.py` | 无 | ✅ |

### 1.2 数据库层

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T1.2.1 | 创建数据库会话模块 | 创建 `db/session.py`，配置异步引擎 | T1.1.1 | ⬜ |
| T1.2.2 | 创建基础模型 | 创建 `models/base.py`，定义 Base 和 Mixin | T1.2.1 | ⬜ |
| T1.2.3 | 创建 User 模型 | 创建 `models/user.py` | T1.2.2 | ⬜ |
| T1.2.4 | 创建 Skill 模型 | 创建 `models/skill.py` | T1.2.2 | ⬜ |
| T1.2.5 | 创建 APIToken 模型 | 创建 `models/token.py` | T1.2.2 | ⬜ |
| T1.2.6 | 创建模型导出 | 创建 `models/__init__.py` | T1.2.3-T1.2.5 | ⬜ |
| T1.2.7 | 配置 Alembic | 初始化数据库迁移 | T1.2.6 | ⬜ |
| T1.2.8 | 创建初始迁移 | 生成初始数据库表迁移脚本 | T1.2.7 | ⬜ |

### 1.3 Pydantic Schemas

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T1.3.1 | 创建通用响应 Schema | 创建 `schemas/response.py` | 无 | ⬜ |
| T1.3.2 | 创建 User Schema | 创建 `schemas/user.py` | T1.2.3 | ⬜ |
| T1.3.3 | 创建 Skill Schema | 创建 `schemas/skill.py` | T1.2.4 | ⬜ |
| T1.3.4 | 创建 Token Schema | 创建 `schemas/token.py` | T1.2.5 | ⬜ |
| T1.3.5 | 创建 Schema 导出 | 创建 `schemas/__init__.py` | T1.3.1-T1.3.4 | ⬜ |

---

## Phase 2: 安全与认证模块

### 2.1 安全工具

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T2.1.1 | 创建密码哈希模块 | 创建 `core/security/password.py` | 无 | ⬜ |
| T2.1.2 | 创建 JWT 工具 | 创建 `core/security/jwt.py` | T1.1.1 | ⬜ |
| T2.1.3 | 创建 API Token 工具 | 创建 `core/security/token.py` | 无 | ⬜ |
| T2.1.4 | 创建安全模块导出 | 创建 `core/security/__init__.py` | T2.1.1-T2.1.3 | ⬜ |

### 2.2 认证中间件

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T2.2.1 | 创建 JWT 认证中间件 | 创建 `core/middleware/auth.py` | T2.1.2 | ⬜ |
| T2.2.2 | 创建 MCP Token 认证 | 创建 `api/mcp/auth.py` | T2.1.3 | ⬜ |
| T2.2.3 | 创建限流中间件 | 创建 `core/middleware/rate_limit.py` | 无 | ⬜ |
| T2.2.4 | 创建中间件导出 | 创建 `core/middleware/__init__.py` | T2.2.1-T2.2.3 | ⬜ |

### 2.3 Repository 层

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T2.3.1 | 创建基础 Repository | 创建 `repositories/base.py` | T1.2.1 | ⬜ |
| T2.3.2 | 创建 User Repository | 创建 `repositories/user.py` | T2.3.1, T1.2.3 | ⬜ |
| T2.3.3 | 创建 Skill Repository | 创建 `repositories/skill.py` | T2.3.1, T1.2.4 | ⬜ |
| T2.3.4 | 创建 Token Repository | 创建 `repositories/token.py` | T2.3.1, T1.2.5 | ⬜ |
| T2.3.5 | 创建 Repository 导出 | 创建 `repositories/__init__.py` | T2.3.1-T2.3.4 | ⬜ |

### 2.4 Service 层

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T2.4.1 | 创建认证服务 | 创建 `services/auth.py` | T2.1.1, T2.1.2, T2.3.2 | ⬜ |
| T2.4.2 | 创建用户服务 | 创建 `services/user.py` | T2.3.2 | ⬜ |
| T2.4.3 | 创建 Token 服务 | 创建 `services/token.py` | T2.1.3, T2.3.4 | ⬜ |
| T2.4.4 | 创建 Skill 服务 | 创建 `services/skill.py` | T2.3.3 | ⬜ |
| T2.4.5 | 创建 Service 导出 | 创建 `services/__init__.py` | T2.4.1-T2.4.4 | ⬜ |

---

## Phase 3: API 接口实现

### 3.1 依赖注入

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T3.1.1 | 创建依赖注入模块 | 创建 `api/deps.py` | T2.2.1, T2.2.2 | ⬜ |

### 3.2 认证 API

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T3.2.1 | 实现注册接口 | POST /api/v1/auth/register | T2.4.1, T3.1.1 | ⬜ |
| T3.2.2 | 实现登录接口 | POST /api/v1/auth/login | T2.4.1, T3.1.1 | ⬜ |
| T3.2.3 | 实现刷新Token接口 | POST /api/v1/auth/refresh | T2.4.1, T3.1.1 | ⬜ |
| T3.2.4 | 创建认证路由 | 创建 `api/v1/auth.py` | T3.2.1-T3.2.3 | ⬜ |

### 3.3 用户 API

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T3.3.1 | 实现获取当前用户 | GET /api/v1/users/me | T2.4.2, T3.1.1 | ⬜ |
| T3.3.2 | 实现更新用户信息 | PUT /api/v1/users/me | T2.4.2, T3.1.1 | ⬜ |
| T3.3.3 | 实现删除账户 | DELETE /api/v1/users/me | T2.4.2, T3.1.1 | ⬜ |
| T3.3.4 | 实现修改密码 | PUT /api/v1/users/me/password | T2.4.2, T3.1.1 | ⬜ |
| T3.3.5 | 创建用户路由 | 创建 `api/v1/users.py` | T3.3.1-T3.3.4 | ⬜ |

### 3.4 Token API

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T3.4.1 | 实现列出Token | GET /api/v1/tokens | T2.4.3, T3.1.1 | ⬜ |
| T3.4.2 | 实现创建Token | POST /api/v1/tokens | T2.4.3, T3.1.1 | ⬜ |
| T3.4.3 | 实现删除Token | DELETE /api/v1/tokens/{token_id} | T2.4.3, T3.1.1 | ⬜ |
| T3.4.4 | 创建Token路由 | 创建 `api/v1/tokens.py` | T3.4.1-T3.4.3 | ⬜ |

### 3.5 Skill API

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T3.5.1 | 创建 Skill 存储工具 | 创建 `core/utils/skill_storage.py` | T1.1.1 | ⬜ |
| T3.5.2 | 实现列出Skills | GET /api/v1/skills | T2.4.4, T3.5.1, T3.1.1 | ⬜ |
| T3.5.3 | 实现创建Skill | POST /api/v1/skills | T2.4.4, T3.5.1, T3.1.1 | ⬜ |
| T3.5.4 | 实现获取Skill详情 | GET /api/v1/skills/{skill_id} | T2.4.4, T3.1.1 | ⬜ |
| T3.5.5 | 实现更新Skill | PUT /api/v1/skills/{skill_id} | T2.4.4, T3.1.1 | ⬜ |
| T3.5.6 | 实现删除Skill | DELETE /api/v1/skills/{skill_id} | T2.4.4, T3.1.1 | ⬜ |
| T3.5.7 | 实现上传Skill文件 | POST /api/v1/skills/upload | T2.4.4, T3.5.1, T3.1.1 | ⬜ |
| T3.5.8 | 实现列出Skill文件 | GET /api/v1/skills/{skill_id}/files | T2.4.4, T3.5.1, T3.1.1 | ⬜ |
| T3.5.9 | 创建Skill路由 | 创建 `api/v1/skills.py` | T3.5.2-T3.5.8 | ⬜ |

### 3.6 路由汇总

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T3.6.1 | 创建API路由汇总 | 创建 `api/router.py` | T3.2.4, T3.3.5, T3.4.4, T3.5.9 | ⬜ |
| T3.6.2 | 创建API模块导出 | 创建 `api/__init__.py` | T3.6.1 | ⬜ |
| T3.6.3 | 创建v1模块导出 | 创建 `api/v1/__init__.py` | T3.2.4, T3.3.5, T3.4.4, T3.5.9 | ⬜ |

---

## Phase 4: MCP 服务集成

### 4.1 MCP 工具改造

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T4.1.1 | 改造 LoadSkillOp | 支持用户隔离 | T1.1.1 | ⬜ |
| T4.1.2 | 改造 LoadSkillMetadataOp | 支持用户隔离 | T1.1.1 | ⬜ |
| T4.1.3 | 改造 ReadReferenceFileOp | 支持用户隔离 | T1.1.1 | ⬜ |
| T4.1.4 | 改造 RunShellCommandOp | 支持用户隔离 | T1.1.1 | ⬜ |

### 4.2 MCP 服务

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T4.2.1 | 创建 MCP 服务 | 创建 `services/mcp.py` | T4.1.1-T4.1.4 | ⬜ |
| T4.2.2 | 创建 HTTP MCP 处理器 | 创建 `api/mcp/http_handler.py` | T4.2.1, T2.2.2 | ⬜ |
| T4.2.3 | 创建 SSE MCP 处理器 | 创建 `api/mcp/sse_handler.py` | T4.2.1, T2.2.2 | ⬜ |
| T4.2.4 | 创建 MCP 模块导出 | 创建 `api/mcp/__init__.py` | T4.2.2, T4.2.3 | ⬜ |

---

## Phase 5: 应用入口与部署

### 5.1 FastAPI 应用

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T5.1.1 | 创建 FastAPI 应用入口 | 创建 `api_app.py`，包含应用工厂函数 `create_application()` | T3.6.1, T4.2.4 | ⬜ |
| T5.1.2 | 添加 CORS 中间件 | 配置跨域支持 | T5.1.1 | ⬜ |
| T5.1.3 | 添加健康检查端点 | GET /health | T5.1.1 | ⬜ |
| T5.1.4 | 更新包版本号 | 更新 `__init__.py` 中的版本号 | T5.1.1 | ⬜ |
| T5.1.5 | 更新 README | 添加多用户模式使用说明 | T5.1.1 | ⬜ |

> **注意**: 现有 `main.py`（FlowLLM 入口）保持不变，用于 stdio/SSE 模式。

### 5.2 部署配置

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T5.2.1 | 创建 Dockerfile | Docker 镜像构建配置 | T5.1.1 | ⬜ |
| T5.2.2 | 创建 docker-compose.yml | 完整部署配置 | T5.2.1 | ⬜ |
| T5.2.3 | 创建 .dockerignore | Docker 构建忽略文件 | T5.2.1 | ⬜ |
| T5.2.4 | 创建启动脚本 | 创建启动命令脚本 | T5.1.1 | ⬜ |

---

## Phase 6: 测试

### 6.1 测试配置

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T6.1.1 | 创建测试配置 | 创建 `tests/conftest.py` | T5.1.1 | ⬜ |
| T6.1.2 | 创建测试数据库配置 | 配置内存 SQLite | T6.1.1 | ⬜ |

### 6.2 单元测试

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T6.2.1 | 测试密码工具 | 测试 `core/security/password.py` | T2.1.1 | ⬜ |
| T6.2.2 | 测试 JWT 工具 | 测试 `core/security/jwt.py` | T2.1.2 | ⬜ |
| T6.2.3 | 测试 Token 工具 | 测试 `core/security/token.py` | T2.1.3 | ⬜ |
| T6.2.4 | 测试认证服务 | 测试 `services/auth.py` | T2.4.1 | ⬜ |
| T6.2.5 | 测试用户服务 | 测试 `services/user.py` | T2.4.2 | ⬜ |
| T6.2.6 | 测试 Skill 服务 | 测试 `services/skill.py` | T2.4.4 | ⬜ |

### 6.3 集成测试

| ID | 任务 | 描述 | 依赖 | 状态 |
|----|------|------|------|------|
| T6.3.1 | 测试认证 API | 测试 `/api/v1/auth/*` | T3.2.4 | ⬜ |
| T6.3.2 | 测试用户 API | 测试 `/api/v1/users/*` | T3.3.5 | ⬜ |
| T6.3.3 | 测试 Token API | 测试 `/api/v1/tokens/*` | T3.4.4 | ⬜ |
| T6.3.4 | 测试 Skill API | 测试 `/api/v1/skills/*` | T3.5.9 | ⬜ |
| T6.3.5 | 测试 MCP API | 测试 `/mcp` 和 `/sse` | T4.2.4 | ⬜ |

---

## 任务统计

| 阶段 | 任务数 | 描述 |
|------|--------|------|
| Phase 1 | 17 | 基础设施搭建 |
| Phase 2 | 18 | 安全与认证模块 |
| Phase 3 | 22 | API 接口实现 |
| Phase 4 | 8 | MCP 服务集成 |
| Phase 5 | 9 | 应用入口与部署 |
| Phase 6 | 13 | 测试 |
| **总计** | **87** | |

---

## 执行顺序建议

```
Phase 1 (基础设施)
    │
    ├── T1.1.x (配置) ──┬── T1.2.x (数据库)
    │                   │
    │                   └── T1.3.x (Schemas)
    │
Phase 2 (安全认证)
    │
    ├── T2.1.x (安全工具) ──┬── T2.2.x (中间件)
    │                       │
    │                       └── T2.3.x (Repository)
    │                                   │
    │                                   └── T2.4.x (Service，含 Skill Service)
    │
Phase 3 (API)
    │
    ├── T3.1.x (依赖注入)
    │       │
    │       ├── T3.2.x (认证API)
    │       ├── T3.3.x (用户API)
    │       ├── T3.4.x (TokenAPI)
    │       └── T3.5.x (Skill API，依赖 T2.4.4)
    │               │
    │               └── T3.6.x (路由汇总)
    │
Phase 4 (MCP集成)
    │
    ├── T4.1.x (工具改造)
    │       │
    │       └── T4.2.x (MCP服务)
    │
Phase 5 (部署)
    │
    ├── T5.1.x (FastAPI入口 api_app.py，保留 main.py)
    │       │
    │       └── T5.2.x (部署配置)
    │
Phase 6 (测试)
    │
    ├── T6.1.x (测试配置)
    │       │
    │       ├── T6.2.x (单元测试)
    │       └── T6.3.x (集成测试)
```

---

## 状态说明

| 状态 | 符号 | 描述 |
|------|------|------|
| 未开始 | ⬜ | 任务尚未开始 |
| 进行中 | 🔵 | 任务正在进行 |
| 已完成 | ✅ | 任务已完成 |
| 已验证 | ✔️ | 任务已完成并通过验证 |
| 阻塞 | 🔴 | 任务被阻塞 |
