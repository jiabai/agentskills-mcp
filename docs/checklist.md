# AgentSkills MCP 多用户Web服务改造 - 检查清单

> 本文档用于验证项目改造的完整性和正确性，按模块组织。
>
> **状态**: 后端与前端控制台已完成实现；当前勾选状态用于保留一次验收结果。若需要重新验收或在新分支上使用，建议复制一份清单再逐项勾选。

---

## 如何使用本检查清单

### 使用步骤

1. **按阶段检查**: 按照任务列表（task_list.md）的阶段顺序，完成一个阶段后检查对应模块
2. **逐项勾选**: 完成一项检查后，将 `- [ ]` 改为 `- [x]`
3. **记录问题**: 发现问题时在对应项下方添加备注
4. **统计结果**: 可运行 `python scripts/checklist_stats.py` 统计进度（可选）

### 状态标记说明

| 标记 | 含义 |
|------|------|
| `- [ ]` | 未检查或未通过（可在行尾追加“（需确认）”作为备注） |
| `- [x]` | 已检查且通过 |

> 说明：`（需确认）` 仅作为备注，不是独立标记；统计脚本会将其按 `- [ ]` 计入未通过/未完成。

### 统计表格说明

本文件不维护“当前状态”的静态统计表，避免与实际勾选状态不一致。
如需统计进度，可运行 `python scripts/checklist_stats.py` 输出实时统计结果，或使用下方模板自行维护统计表。

### 与其他文档的关系

| 文档 | 使用时机 |
|------|---------|
| project-spec.md | 检查时参考技术规范 |
| task_list.md | 完成任务后进行对应检查 |
| REFACTORING_GUIDE.md | 遇到问题时参考注意事项 |

---

## 1. 项目配置检查

### 1.1 依赖配置

- [x] `pyproject.toml` 包含所有必需依赖
  - [x] FastAPI >= 0.109.0
  - [x] uvicorn[standard] >= 0.27.0
  - [x] SQLAlchemy[asyncio] >= 2.0.0
  - [x] asyncpg >= 0.29.0
  - [x] pydantic >= 2.5.0
  - [x] PyJWT
  - [x] passlib[bcrypt]
  - [x] pydantic-settings
  - [x] python-multipart
  - [x] flowllm >= 0.2.0.7
  - [x] loguru >= 0.7.0
  - [x] psutil >= 5.9.0
  - [x] pipreqs
  - [x] alembic
  - [x] httpx

### 1.2 环境配置

- [x] `.env.example` 文件存在（包含 `Settings` 所需的环境变量示例）

### 1.3 Settings 配置

- [x] `mcp_agentskills/config/settings.py` 正确定义 Settings 类
- [x] 所有环境变量已映射到 Settings 属性
- [x] 默认值设置合理
- [x] 包含 `.env` 文件加载配置

### 1.4 测试环境配置

- [x] 测试使用独立的测试数据库配置
- [x] 使用内存 SQLite (`sqlite+aiosqlite:///:memory:`) 进行单元测试
- [x] 测试配置与生产配置分离（通过环境变量或配置项区分）
- [x] 确保 SQLite 测试与 PostgreSQL 生产环境的 SQL 语法兼容性
- [x] 确保主键 UUID 由应用层生成（uuid4），迁移脚本不依赖 gen_random_uuid()

> **说明**: 项目同时支持 PostgreSQL（生产环境）和 SQLite（测试环境）。测试环境使用 SQLite 是为了简化测试执行，无需启动外部数据库服务。详见 [project-spec.md](./project-spec.md) 和 [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md)。

> **兼容性注意事项**:
> - PostgreSQL 和 SQLite 在某些 SQL 语法上有差异，如 `UUID` 类型、`JSON` 操作等
> - 测试时应避免使用 PostgreSQL 特有特性，或使用条件判断兼容两种数据库
> - 如果使用 PostgreSQL 特有特性（如 `uuid-ossp` 扩展），建议在测试环境中使用 `pytest-postgresql` 等工具启动真实 PostgreSQL 实例

---

## 2. 数据库模型检查

### 2.1 User 模型

- [x] `mcp_agentskills/models/user.py` 文件存在
- [x] User 类继承自 Base
- [x] 包含所有必需字段：
  - [x] id (UUID, 主键)
  - [x] email (唯一, 索引)
  - [x] username (唯一, 索引)
  - [x] hashed_password
  - [x] is_active
  - [x] is_superuser
  - [x] created_at
  - [x] updated_at
- [x] 正确定义与 Skill 的关系
- [x] 正确定义与 APIToken 的关系

### 2.2 Skill 模型

- [x] `mcp_agentskills/models/skill.py` 文件存在
- [x] Skill 类继承自 Base
- [x] 包含所有必需字段：
  - [x] id (UUID, 主键)
  - [x] user_id (外键)
  - [x] name
  - [x] description
  - [x] skill_dir
  - [x] is_active
  - [x] created_at
  - [x] updated_at
- [x] (user_id, name) 唯一约束已定义
- [x] 正确定义与 User 的关系

### 2.3 APIToken 模型

- [x] `mcp_agentskills/models/token.py` 文件存在
- [x] APIToken 类继承自 Base
- [x] 包含所有必需字段：
  - [x] id (UUID, 主键)
  - [x] user_id (外键)
  - [x] name
  - [x] token_hash (唯一, 索引)
  - [x] is_active
  - [x] expires_at
  - [x] last_used_at
  - [x] created_at
- [x] 正确定义与 User 的关系

### 2.4 数据库迁移

- [x] Alembic 已正确配置
- [x] 初始迁移脚本已创建
- [x] `alembic upgrade head` 执行成功
- [x] 数据库表结构正确创建

---

## 3. Pydantic Schemas 检查

### 3.1 User Schemas

- [x] `mcp_agentskills/schemas/user.py` 文件存在
- [x] UserCreate schema 定义正确
  - [x] email 验证
  - [x] username 验证
  - [x] password 最小长度验证
- [x] UserUpdate schema 定义正确
- [x] UserResponse schema 定义正确
- [x] UserInDB schema 定义正确（包含 hashed_password）

### 3.2 Skill Schemas

- [x] `mcp_agentskills/schemas/skill.py` 文件存在
- [x] SkillCreate schema 定义正确
- [x] SkillUpdate schema 定义正确
- [x] SkillResponse schema 定义正确
- [x] SkillListResponse schema 定义正确（分页）

### 3.3 Token Schemas

- [x] `mcp_agentskills/schemas/token.py` 文件存在
- [x] TokenCreate schema 定义正确
- [x] TokenResponse schema 定义正确
  - [x] token 字段仅在创建时返回
- [x] TokenListResponse schema 定义正确

### 3.4 通用响应 Schemas

- [x] `mcp_agentskills/schemas/response.py` 文件存在
- [x] 通用错误响应格式定义
- [x] 分页响应格式定义

---

## 4. 安全模块检查

### 4.1 密码安全

- [x] `mcp_agentskills/core/security/password.py` 文件存在
- [x] `verify_password()` 函数正确实现
- [x] `get_password_hash()` 函数正确实现
- [x] 使用 bcrypt 算法

### 4.2 JWT 认证

- [x] `mcp_agentskills/core/security/jwt_utils.py` 文件存在
- [x] `create_access_token()` 函数正确实现 (使用 PyJWT)
- [x] `create_refresh_token()` 函数正确实现
- [x] `decode_token()` 函数正确实现
- [x] Token 类型区分（access/refresh）

### 4.3 API Token

- [x] `mcp_agentskills/core/security/token.py` 文件存在
- [x] `generate_api_token()` 函数正确实现
  - [x] 格式: `ask_live_{64位hex}`
- [x] `hash_token()` 函数正确实现
- [x] `verify_token_hash()` 函数正确实现

---

## 5. Repository 层检查

### 5.1 Base Repository

- [x] `mcp_agentskills/repositories/base.py` 文件存在
- [x] 定义通用 CRUD 方法
  - [x] get()
  - [x] get_multi()
  - [x] create()
  - [x] update()
  - [x] delete()

### 5.2 User Repository

- [x] `mcp_agentskills/repositories/user.py` 文件存在
- [x] `get_by_email()` 方法
- [x] `get_by_username()` 方法
- [x] `create()` 方法正确哈希密码

### 5.3 Skill Repository

- [x] `mcp_agentskills/repositories/skill.py` 文件存在
- [x] `get_by_user_and_name()` 方法
- [x] `get_multi_by_user()` 方法（分页）

### 5.4 Token Repository

- [x] `mcp_agentskills/repositories/token.py` 文件存在
- [x] `get_by_hash()` 方法
- [x] `list_by_user()` 方法
- [x] `count_by_user()` 方法
- [x] `mark_used()` 方法
- [x] `revoke()` 方法

---

## 6. Service 层检查

### 6.1 Auth Service

- [x] `mcp_agentskills/services/auth.py` 文件存在
- [x] `register()` 方法
  - [x] 检查邮箱唯一性
  - [x] 检查用户名唯一性
  - [x] 哈希密码
- [x] `login()` 方法
  - [x] 验证邮箱存在
  - [x] 验证密码正确
  - [x] 生成 JWT Token
- [x] `refresh_token()` 方法

### 6.2 User Service

- [x] `mcp_agentskills/services/user.py` 文件存在
- [x] `update_user()` 方法
- [x] `delete_user()` 方法
  - [x] 验证密码
  - [x] 删除关联数据
- [x] `change_password()` 方法

### 6.3 Token Service

- [x] `mcp_agentskills/services/token.py` 文件存在
- [x] `create_token()` 方法
  - [x] 生成 Token
  - [x] 存储哈希值
  - [x] 返回明文 Token（仅一次）
- [x] `list_tokens()` 方法
- [x] `revoke_token()` 方法
- [x] `validate_token()` 方法

### 6.4 Skill Service

- [x] `mcp_agentskills/services/skill.py` 文件存在
- [x] `create_skill()` 方法
- [x] `get_skill()` 方法
- [x] `list_skills()` 方法（分页）
- [x] `update_skill()` 方法
- [x] `delete_skill()` 方法
- [x] `upload_file()` 方法
- [x] `list_skill_files()` 方法

---

## 7. API 接口检查

### 7.1 认证接口

- [x] POST `/api/v1/auth/register`
  - [x] 返回 201 Created
  - [x] 返回用户信息（不含密码）
  - [x] 邮箱重复返回 409
- [x] POST `/api/v1/auth/login`
  - [x] 返回 access_token 和 refresh_token
  - [x] 错误凭据返回 401
- [x] POST `/api/v1/auth/refresh`
  - [x] 验证 refresh_token
  - [x] 返回新 access_token

### 7.2 用户接口

- [x] GET `/api/v1/users/me`
  - [x] 需要 JWT 认证
  - [x] 返回当前用户信息
- [x] PUT `/api/v1/users/me`
  - [x] 更新用户信息
- [x] DELETE `/api/v1/users/me`
  - [x] 需要密码确认
  - [x] 删除用户及关联数据
- [x] PUT `/api/v1/users/me/password`
  - [x] 验证旧密码
  - [x] 更新新密码

### 7.3 Token 接口

- [x] GET `/api/v1/tokens`
  - [x] 返回 Token 列表（不含明文 Token）
- [x] POST `/api/v1/tokens`
  - [x] 返回明文 Token（仅此一次）
  - [x] 支持设置过期时间
- [x] DELETE `/api/v1/tokens/{token_id}`
  - [x] 撤销 Token

### 7.4 Skill 接口

- [x] GET `/api/v1/skills`
  - [x] 支持分页
  - [x] 支持搜索
- [x] POST `/api/v1/skills`
  - [x] 创建 Skill 目录
- [x] GET `/api/v1/skills/{skill_id}`
  - [x] 返回 Skill 详情
- [x] PUT `/api/v1/skills/{skill_id}`
  - [x] 更新 Skill 信息
- [x] DELETE `/api/v1/skills/{skill_id}`
  - [x] 删除 Skill 及文件
- [x] POST `/api/v1/skills/upload`
  - [x] 支持 multipart 上传
  - [x] 文件大小限制
  - [x] 文件类型验证
- [x] GET `/api/v1/skills/{skill_id}/files`
  - [x] 返回文件列表

### 7.5 MCP 接口

- [x] POST `/mcp`
  - [x] 需要 API Token 认证
  - [x] 支持 MCP 协议
  - [x] 用户隔离正确
- [x] GET `/sse`
  - [x] 需要 API Token 认证
  - [x] SSE 连接正确
  - [x] 用户隔离正确

---

## 8. MCP 工具改造检查

### 8.1 LoadSkillOp

- [x] 支持从上下文获取 user_id
- [x] 根据 user_id 构建正确路径
- [x] 向后兼容（无 user_id 时使用全局路径）
- [x] 错误处理正确

### 8.2 LoadSkillMetadataOp

- [x] 支持从上下文获取 user_id
- [x] 仅搜索用户私有目录
- [x] 向后兼容
- [x] 空目录处理正确

### 8.3 ReadReferenceFileOp

- [x] 支持从上下文获取 user_id
- [x] 正确构建文件路径
- [x] 向后兼容
- [x] 文件不存在处理正确

### 8.4 RunShellCommandOp

- [x] 支持从上下文获取 user_id
- [x] 在正确目录执行命令
- [x] 向后兼容
- [x] 安全限制正确

---

## 9. 中间件检查

### 9.1 JWT 认证中间件

- [x] `mcp_agentskills/core/middleware/auth.py` 文件存在
- [x] `get_current_user()` 依赖正确
- [x] `get_current_active_user()` 依赖正确
- [x] Token 过期处理正确
- [x] 用户不存在处理正确
- [x] 用户禁用处理正确

### 9.2 MCP Token 认证

- [x] `mcp_agentskills/api/mcp/auth.py` 文件存在
- [x] Token 验证正确
- [x] Token 过期检查
- [x] Token 撤销检查
- [x] 更新 last_used_at

---

## 10. 文件存储检查

### 10.1 Skill 存储工具

- [x] `mcp_agentskills/core/utils/skill_storage.py` 文件存在
- [x] `get_user_skill_dir()` 方法
- [x] `create_skill_dir()` 方法
- [x] `delete_skill_dir()` 方法
- [x] `save_file()` 方法
- [x] `list_files()` 方法
- [x] `skill_exists()` 方法

### 10.2 存储路径

- [x] 用户隔离目录结构正确
- [x] 路径格式: `/data/skills/{user_id}/{skill_name}/`
- [x] 目录权限正确

---

## 11. FastAPI 应用检查

### 11.1 应用入口

- [x] `mcp_agentskills/api_app.py` 文件存在
- [x] `create_application()` 工厂函数
- [x] CORS 中间件配置
- [x] 路由注册正确
- [x] 生命周期管理（数据库初始化）

### 11.2 健康检查

- [x] GET `/health` 端点存在
  - [x] 返回服务状态 `{"status": "healthy"}`
- [x] GET `/metrics` 端点存在（可选）
  - [x] 返回数据库连接状态
  - [x] 返回磁盘使用率
  - [x] 返回内存使用率
  - [x] 返回 CPU 使用率

### 11.3 API 文档

- [x] GET `/docs` Swagger UI 可访问
- [x] GET `/redoc` ReDoc 可访问
- [x] OpenAPI schema 正确

---

## 12. 部署配置检查

### 12.1 Docker

- [x] `Dockerfile` 文件存在
- [x] 基础镜像正确（Python 3.11+）
- [x] 依赖安装正确
- [x] 工作目录正确
- [x] 暴露端口正确
- [x] 启动命令正确

### 12.2 Docker Compose

- [x] `docker-compose.yml` 文件存在
- [x] API 服务配置正确
- [x] PostgreSQL 服务配置正确
- [x] 数据卷配置正确
- [x] 网络配置正确
- [x] 环境变量传递正确

### 12.3 启动命令

- [x] `Dockerfile` 包含可用启动命令（uvicorn）
- [x] 启动前自动执行数据库迁移（`alembic upgrade head`）
- [x] 迁移失败会阻止服务启动（避免静默忽略）

---

## 13. 测试检查

### 13.1 测试配置

- [x] `tests/conftest.py` 文件存在
- [x] 测试数据库配置正确（内存 SQLite）
- [x] 测试客户端 fixture 正确
- [x] 测试用户 fixture 正确

### 13.2 单元测试

- [x] 密码工具测试通过
- [x] JWT 工具测试通过
- [x] Token 工具测试通过
- [x] 认证服务测试通过
- [x] 用户服务测试通过
- [x] Skill 服务测试通过

### 13.3 集成测试

- [x] 认证 API 测试通过
- [x] 用户 API 测试通过
- [x] Token API 测试通过
- [x] Skill API 测试通过
- [x] MCP API 测试通过

### 13.4 测试覆盖率

- [x] 单元测试覆盖率 >= 80%
- [x] 核心业务逻辑覆盖率 >= 90%

---

## 14. 安全检查

### 14.1 密码安全

- [x] 密码使用 bcrypt 哈希
- [x] 密码最小长度 >= 8
- [x] 密码不在响应中返回

### 14.2 Token 安全

- [x] API Token 仅在创建时返回一次
- [x] 存储 SHA256 哈希值
- [x] 支持过期时间
- [x] 支持撤销

### 14.3 文件上传安全

- [x] 文件类型验证
- [x] 单文件大小限制
- [x] 总上传大小限制
- [x] 路径遍历防护

### 14.4 API 安全

- [x] 所有用户 API 需要 JWT 认证
- [x] MCP API 需要 API Token 认证
- [x] 敏感操作需要密码确认
- [x] CORS 配置正确

---

## 15. 文档检查

### 15.1 API 文档

- [x] OpenAPI schema 完整
- [x] 所有端点有描述
- [x] 所有参数有描述
- [x] 所有响应有描述

### 15.2 项目文档

- [x] README 更新
- [x] 环境变量说明
- [x] 部署说明
- [x] 使用示例

---

## 16. 前端控制台 UI（Next.js + shadcn/ui）

> 本模块用于生成前端控制台代码时的验证清单。
>
> 前端界面规范已补充至 [project-spec.md](./project-spec.md)。

### 16.1 工程与依赖

- [x] Next.js App Router 项目已初始化
- [x] Tailwind 已启用并使用 4px 网格间距类
- [x] shadcn/ui 已初始化并生成基础组件
- [x] 深色模式已启用并随主题自动适配

### 16.2 组件导入与样式规则

- [x] 组件导入仅来自 `@/components/ui/*`
- [x] 未使用任何像素值类（如 `px-20`）与内联样式像素值
- [x] 布局优先使用 Flex/Grid，避免 `float` 与 `position: absolute`
- [x] 容器宽度使用 `container mx-auto max-w-screen-xl`
- [x] 字体仅使用 Tailwind 排版类（如 `text-base`、`font-medium`、`leading-relaxed`）
- [x] 颜色仅使用语义化类（如 `bg-primary`、`text-destructive`、`border-border`）
- [x] 圆角仅使用 `rounded-lg` 或 `rounded-[var(--radius)]`

### 16.3 页面与路由

- [x] /login 页面存在且使用 Card 表单布局
- [x] /register 页面存在且使用 Card 表单布局
- [x] /dashboard 页面存在且包含概览卡片与入口操作
- [x] /skills 页面存在且包含搜索与列表布局
- [x] /skills/new 页面存在且包含创建 Skill 表单
- [x] /skills/[skillId] 页面存在且包含 Tabs（概览/文件/设置）
- [x] /tokens 页面存在且包含创建与撤销流程
- [x] /profile 与 /security 页面存在且表单提交有状态反馈

### 16.4 状态与交互

- [x] 列表页包含加载态、空态与错误态
- [x] 危险操作（删除/撤销）具备二次确认对话框
- [x] Token 创建后仅展示一次明文并提供复制入口

---

## 检查结果汇总

### 统计方法

你可以选择以下任一方式统计进度：

**方式一：运行统计脚本（推荐）**

- 运行 `python scripts/checklist_stats.py` 输出实时统计结果
- 注意：统计脚本仅统计 `- [x]` 与 `- [ ]`；行尾附加 `（需确认）` 仍按 `- [ ]` 计数

**方式二：维护统计表（可选）**

每完成一个模块检查后，手动更新对应数值：

1. **总项**: 统计该模块的检查项总数
2. **通过**: 将 `- [x]` 的数量填入
3. **未通过**: 将 `- [ ]` 的数量填入
4. **通过率**: 计算 `通过 / 总项 * 100%`

**示例**（假设模块1已完成检查）:

| 模块 | 总项 | 通过 | 未通过 | 通过率 |
|------|------|------|--------|--------|
| 1. 项目配置 | 12 | 12 | 0 | 100% |
| 2. 数据库模型 | 15 | 14 | 1 | 93% |
| 3. Pydantic Schemas | 10 | 8 | 2 | 80% |
| ... | ... | ... | ... | ... |

### 统计工具脚本（推荐）

统计脚本以仓库中的 `scripts/checklist_stats.py` 为准。

使用方法：
```bash
python scripts/checklist_stats.py
```

### 当前状态（统计结果）

- 本节不维护静态统计表，避免与实际勾选状态不一致。
- 请运行 `python scripts/checklist_stats.py` 生成实时统计结果。
- 注意：统计脚本仅统计 `- [x]` 与 `- [ ]`；`- [ ]（需确认）` 仍按 `- [ ]` 统计。

### 初始状态模板（供复制）

> **重要说明**:
> - 以下表格是**静态模板**，显示初始状态（所有模块未开始检查）
> - 表格不会自动更新，需要**手动更新**或**运行统计脚本**生成最新结果
> - 推荐运行 `python scripts/checklist_stats.py` 自动生成实时统计结果

| 模块 | 总项 | 通过 | 未通过 | 通过率 |
|------|------|------|--------|--------|
| 1. 项目配置 | 26 | 0 | 26 | 0% |
| 2. 数据库模型 | 42 | 0 | 42 | 0% |
| 3. Pydantic Schemas | 21 | 0 | 21 | 0% |
| 4. 安全模块 | 14 | 0 | 14 | 0% |
| 5. Repository 层 | 20 | 0 | 20 | 0% |
| 6. Service 层 | 32 | 0 | 32 | 0% |
| 7. API 接口 | 53 | 0 | 53 | 0% |
| 8. MCP 工具改造 | 16 | 0 | 16 | 0% |
| 9. 中间件 | 11 | 0 | 11 | 0% |
| 10. 文件存储 | 10 | 0 | 10 | 0% |
| 11. FastAPI 应用 | 15 | 0 | 15 | 0% |
| 12. 部署配置 | 15 | 0 | 15 | 0% |
| 13. 测试 | 17 | 0 | 17 | 0% |
| 14. 安全 | 15 | 0 | 15 | 0% |
| 15. 文档 | 8 | 0 | 8 | 0% |
| 16. 前端控制台 UI（Next.js + shadcn/ui） | 22 | 0 | 22 | 0% |
| **总计** | **337** | **0** | **337** | **0%** |

> **💡 提示**: 运行 `python scripts/checklist_stats.py` 可自动生成包含实际数据的统计表格。

---

## 验收标准

项目改造完成需满足以下条件：

1. **功能完整性**: 所有非可选检查项 100% 通过（可选模块按需忽略）
2. **测试覆盖率**: 单元测试 >= 80%，核心逻辑 >= 90%
3. **安全合规**: 所有安全检查项通过
4. **文档完整**: API 文档和项目文档完整
5. **部署就绪**: Docker 部署配置完整可用
