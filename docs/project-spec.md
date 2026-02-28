# AgentSkills MCP 多用户Web服务改造规范

> 本文档定义了 AgentSkills MCP 多用户 Web 服务的技术规范。当前代码库已生成并集成后端 Python 侧的核心能力（多用户隔离、API Token 认证、私有 Skill 空间等），并已补齐前端控制台实现。
>
> 本文档中也包含少量“可选扩展/参考实现”的示例片段，未必在仓库中默认启用；如与实际实现不一致，以代码为准。

---

## 📖 文档阅读指南

> **本文档较长**，建议按以下方式阅读：

### 快速导航

| 章节 | 内容 | 适用场景 |
|------|------|---------|
| [1. 项目概述](#1-项目概述) | 改造目标、技术选型 | 了解项目背景 |
| [2. 系统架构](#2-系统架构) | 分层架构、用户隔离 | 理解整体设计 |
| [3. 数据模型](#3-数据模型) | User/Skill/APIToken 模型 | 实现数据库层 |
| [4. API 接口规范](#4-api-接口规范) | RESTful API 设计 | 实现接口层 |
| [5. 认证机制](#5-认证机制) | JWT/API Token 认证 | 实现安全模块 |
| [6. MCP工具改造](#6-mcp工具改造) | 工具改造方案 | 改造现有工具 |
| [7. 项目结构](#7-项目结构) | 目录结构、启动方式 | 创建项目骨架 |
| [8. 依赖清单](#8-依赖清单) | 第三方依赖 | 配置开发环境 |
| [9. 配置规范](#9-配置规范) | 环境变量、Settings | 配置管理 |
| [10. 安全要求](#10-安全要求) | 密码、Token、文件安全 | 安全加固 |
| [11. 错误处理](#11-错误处理) | 标准错误格式 | 统一错误处理 |
| [12. 测试要求](#12-测试要求) | 测试策略、覆盖率 | 编写测试 |
| [13. 部署要求](#13-部署要求) | Docker、迁移、监控 | 部署上线 |

### 代码示例说明

文档中包含大量代码示例，用于说明实现细节：

- 多数代码片段为“参考示例”，需要结合当前仓库结构与依赖调整
- 若某段实现属于“可选扩展/未来增强”，文中会明确注明“可选”或“当前仓库未实现”
- 与当前仓库实现一致的关键代码片段，以仓库源码为准

### 配套文档

| 文档 | 用途 |
|------|------|
| [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md) | 重构步骤和注意事项 |
| [task_list.md](./task_list.md) | 任务分解和执行顺序 |
| [checklist.md](./checklist.md) | 验证检查清单 |
| [tools.md](./tools.md) | MCP 工具文档 |

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
| 认证 | PyJWT + passlib | 最新版 |
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

> **路径风格说明**: 文档中的路径示例使用 Linux/POSIX 风格（正斜杠 `/`）。在 Windows 环境下开发时：
> - 配置文件中的路径可使用正斜杠或反斜杠
> - Python 的 `pathlib.Path` 会自动处理跨平台路径
> - 环境变量 `SKILL_STORAGE_PATH` 在 Windows 下可设置为 `C:\data\skills` 或 `D:\data\skills`

---

## 3. 数据模型

> **一致性说明**: 本章代码片段以“规范/推荐实现”为主，部分细节（例如 `ForeignKey(..., ondelete="CASCADE")` 的数据库级联删除）在当前仓库实现中未开启；当前实现主要依赖 ORM 关系的 `cascade="all, delete-orphan"` 行为来清理关联数据。若对数据库级联有硬性要求，请以仓库迁移脚本与模型定义为准并按需补齐。

### 3.1 User 模型

```python
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from mcp_agentskills.models.base import generate_uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系定义
    skills: Mapped[List["Skill"]] = relationship(
        "Skill",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    tokens: Mapped[List["APIToken"]] = relationship(
        "APIToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
```

### 3.2 Skill 模型

```python
from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from mcp_agentskills.models.base import generate_uuid

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")
    skill_dir: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系定义
    user: Mapped["User"] = relationship("User", back_populates="skills")

    # 表级约束
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uix_user_skill_name"),
    )
```

### 3.3 APIToken 模型

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from mcp_agentskills.models.base import generate_uuid

class APIToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系定义
    user: Mapped["User"] = relationship("User", back_populates="tokens")

    # 索引
    __table_args__ = (
        Index("ix_api_tokens_user_id", "user_id"),
    )
```

---

## 4. API 接口规范

### API 版本策略

- **版本标识**: 通过 URL 路径标识（`/api/v1/`）
- **版本升级规则**:
  - 重大变更（不兼容）时发布新版本（v2, v3...）
  - 旧版本保持至少 6 个月的兼容期
  - 小型变更（新增字段、新增接口）在当前版本迭代
- **弃用流程**:
  1. 在响应头添加 `Deprecation: true` 和 `Sunset` 日期
  2. 在文档中标注弃用时间
  3. 提前 3 个月通知用户迁移

#### API 版本弃用实现方案

> 本节为参考实现/可选扩展，当前仓库未实现 `core/middleware/deprecation.py`、`core/decorators/deprecation.py`、`services/notification.py` 等代码。若需要该能力，请按本文示例自行落地并以实际代码为准。

使用 FastAPI 中间件实现自动添加弃用响应头：

```python
# core/middleware/deprecation.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from typing import Dict, Set

# 弃用端点配置：路径 -> 完全移除日期
DEPRECATED_ENDPOINTS: Dict[str, str] = {
    "/api/v1/legacy/endpoint": "2025-06-01",
    "/api/v1/old/feature": "2025-09-01",
}

# 已弃用的整个版本前缀
DEPRECATED_VERSIONS: Set[str] = {
    # "/api/v1",  # 当 v1 整体弃用时启用
}


class DeprecationMiddleware(BaseHTTPMiddleware):
    """
    弃用中间件：为已弃用的端点自动添加 Deprecation 和 Sunset 响应头

    响应头说明：
    - Deprecation: true - 表示该端点已弃用
    - Sunset: <date> - 表示该端点将完全移除的日期（RFC 8594）
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path

        # 检查特定端点是否已弃用
        if path in DEPRECATED_ENDPOINTS:
            sunset_date = DEPRECATED_ENDPOINTS[path]
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = sunset_date

        # 检查整个版本是否已弃用
        for version_prefix in DEPRECATED_VERSIONS:
            if path.startswith(version_prefix):
                response.headers["Deprecation"] = "true"
                # 从配置或数据库获取具体日落日期
                response.headers["Sunset"] = "2025-12-31"
                break

        return response


# 在 api_app.py 中使用
from fastapi import FastAPI
from mcp_agentskills.core.middleware.deprecation import DeprecationMiddleware

def create_application() -> FastAPI:
    app = FastAPI()

    # 添加弃用中间件
    app.add_middleware(DeprecationMiddleware)

    # ... 其他配置

    return app
```

#### 端点级别的弃用装饰器（可选）

对于单个端点的弃用，可以使用装饰器：

```python
# core/decorators/deprecation.py
from functools import wraps
from fastapi import Response
from datetime import datetime
from typing import Optional

def deprecated(sunset_date: Optional[str] = None, alternative: Optional[str] = None):
    """
    标记端点为已弃用

    Args:
        sunset_date: 端点完全移除的日期（ISO 8601格式）
        alternative: 替代端点的路径
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取 response 对象（如果在 kwargs 中）
            response = kwargs.get('response')
            if response and isinstance(response, Response):
                response.headers["Deprecation"] = "true"
                if sunset_date:
                    response.headers["Sunset"] = sunset_date
                if alternative:
                    response.headers["Link"] = f'<{alternative}>; rel="successor-version"'

            return await func(*args, **kwargs)

        # 标记函数已弃用（用于文档生成）
        wrapper._deprecated = True
        wrapper._sunset_date = sunset_date
        wrapper._alternative = alternative

        return wrapper
    return decorator


# 使用示例
from fastapi import APIRouter, Response
from mcp_agentskills.core.decorators.deprecation import deprecated

router = APIRouter()

@router.get("/legacy/endpoint")
@deprecated(sunset_date="2025-06-01", alternative="/api/v1/new/endpoint")
async def legacy_endpoint(response: Response):
    '''
    已弃用的端点

    **弃用说明**: 该端点将于 2025-06-01 移除，请迁移到 `/api/v1/new/endpoint`
    '''
    return {"message": "This endpoint is deprecated"}
```

#### 版本弃用通知机制

```python
# services/notification.py
from datetime import datetime, timedelta
from typing import List

class DeprecationNotifier:
    """弃用通知服务"""

    async def notify_upcoming_deprecation(self):
        """
        提前通知即将弃用的端点
        建议在 CI/CD 或定时任务中执行
        """
        notifications = []

        for endpoint, sunset_date_str in DEPRECATED_ENDPOINTS.items():
            sunset_date = datetime.fromisoformat(sunset_date_str)
            days_until_removal = (sunset_date - datetime.now()).days

            # 提前 90 天、30 天、7 天发送通知
            if days_until_removal in [90, 30, 7]:
                notifications.append({
                    "endpoint": endpoint,
                    "sunset_date": sunset_date_str,
                    "days_remaining": days_until_removal,
                    "severity": "warning" if days_until_removal > 7 else "critical"
                })

        # 发送通知（邮件、Webhook 等）
        await self._send_notifications(notifications)

    async def _send_notifications(self, notifications: List[dict]):
        """实际发送通知"""
        # 实现通知逻辑（邮件、Slack、Webhook 等）
        pass
```

### 4.1 认证模块 `/api/v1/auth`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/register` | POST | 否 | 用户注册 |
| `/login` | POST | 否 | 用户登录，返回JWT |
| `/refresh` | POST | 否（需 refresh_token） | 刷新Access Token（请求体提供 refresh_token） |
| `/logout` | POST | 是 | 登出（可选能力，当前仓库未实现该端点；且未实现 Token 黑名单） |

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

- **格式**: `ask_live_{64字符十六进制串}`，总长度73字符
  - 前缀: `ask_live_`（9字符）
  - 随机部分: 32字节（256位）随机数，使用 `secrets.token_hex(32)` 生成64个十六进制字符
- **存储**: 仅存储SHA256哈希值
- **Header**: `Authorization: Bearer {api_token}`
- **过期**: 可选设置过期时间

### 5.3 Token生成示例

```python
import secrets

# API Token 生成
prefix = "ask_live_"
random_part = secrets.token_hex(32)  # 生成64个十六进制字符（32字节）
token = prefix + random_part
# 示例: ask_live_a1b2c3d4e5f67890...（共73字符：9 + 64）

# Token 哈希存储
import hashlib
token_hash = hashlib.sha256(token.encode()).hexdigest()
```

### 5.4 API Token 验证流程

#### 完整验证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP 请求验证流程                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 从请求头提取 Token                                            │
│     Header: Authorization: Bearer ask_live_xxx...                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 验证 Token 格式                                               │
│     - 检查前缀是否为 "ask_live_"                                   │
│     - 检查总长度是否为 73 字符                                     │
│     - 检查随机部分是否为有效的十六进制字符串                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 计算 Token 哈希                                               │
│     token_hash = SHA256(token)                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 数据库查询                                                    │
│     SELECT * FROM api_tokens WHERE token_hash = ? AND is_active  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. 检查 Token 状态                                               │
│     - is_active == True ?                                        │
│     - expires_at > now() ? (如果设置了过期时间)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. 更新最后使用时间                                               │
│     UPDATE api_tokens SET last_used_at = now()                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. 设置用户上下文                                                 │
│     set_current_user_id(user.id)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. 返回用户信息，继续处理请求                                       │
└─────────────────────────────────────────────────────────────────┘
```

#### 实现代码示例

```python
# mcp_agentskills/api/mcp/auth.py（FastMCP TokenVerifier 版本）
import re
from datetime import timezone

from mcp.server.auth.provider import AccessToken

from mcp_agentskills.core.utils.user_context import set_current_user_id
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.token import TokenRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.token import TokenService

_token_pattern = re.compile(r"^ask_live_[0-9a-f]{64}$")


class ApiTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if not _token_pattern.match(token):
            return None

        async for session in get_async_session():
            token_repo = TokenRepository(session)
            user_repo = UserRepository(session)
            service = TokenService(token_repo, user_repo)

            try:
                api_token = await service.validate_token(token)
            except ValueError:
                return None

            user = await user_repo.get_by_id(api_token.user_id)
            if not user or not user.is_active:
                return None

            set_current_user_id(str(user.id))

            expires_at = None
            if api_token.expires_at:
                expires_at = int(api_token.expires_at.replace(tzinfo=timezone.utc).timestamp())

            return AccessToken(token=token, client_id=str(user.id), scopes=[], expires_at=expires_at)
```

#### 错误响应

| 错误码 | 描述 | HTTP 状态码 |
|--------|------|------------|
| `INVALID_TOKEN_FORMAT` | Token 格式不正确 | 401 |
| `TOKEN_NOT_FOUND` | Token 不存在 | 401 |
| `TOKEN_REVOKED` | Token 已被撤销 | 401 |
| `TOKEN_EXPIRED` | Token 已过期 | 401 |

---

## 6. MCP工具改造

### 6.1 改造原则

现有MCP工具需要支持用户隔离，核心改动：

1. 从上下文获取 `user_id`
2. 根据用户ID构建Skill路径
3. 保持向后兼容（仅用于 stdio/SSE 模式，无用户认证时使用全局路径）

> **重要说明**: 向后兼容仅适用于 **stdio 模式** 或 **单用户 SSE 模式**。在 HTTP API 模式下，MCP 端点强制要求 API Token 认证，不允许无用户身份的访问。这是为了确保多用户环境下的数据隔离和安全性。

### 6.2 并发安全机制

> **重要**: FlowLLM 的 `C` 是全局上下文对象，在多用户并发场景下需要特殊处理以确保用户隔离的安全性。

#### 实现方案

使用 `contextvars` 实现请求级别的用户上下文隔离：

```python
# core/utils/user_context.py
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# 定义请求级别的用户上下文变量
_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)

def set_current_user_id(user_id: Optional[str]) -> None:
    """设置当前请求的用户ID"""
    _current_user_id.set(user_id)

def get_current_user_id() -> Optional[str]:
    """获取当前请求的用户ID"""
    return _current_user_id.get()
```

#### MCP 工具中的使用方式

```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

async def async_execute(self):
    user_id = get_current_user_id()  # 从请求级上下文获取
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

    if user_id:
        skill_path = skill_dir / user_id / skill_name / "SKILL.md"
    else:
        skill_path = skill_dir / skill_name / "SKILL.md"
```

#### MCP 认证中间件中的注入

```python
# api/mcp/auth.py
from mcp_agentskills.core.utils.user_context import set_current_user_id

async def get_current_user_from_token(token: str) -> User:
    """从 API Token 获取用户并设置上下文"""
    user = await validate_api_token(token)
    set_current_user_id(str(user.id))  # 设置请求级用户ID
    return user
```

#### 为什么这样设计？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **contextvars** (推荐) | 线程安全、协程安全、无需修改 FlowLLM | 需要在中间件中显式设置 |
| 修改 C.service_config | 简单直接 | 全局状态，并发不安全 |
| 传递 user_id 参数 | 最安全 | 需要修改所有工具签名 |

### 6.3 LoadSkillOp 改造

```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

async def async_execute(self):
    skill_name = self.input_dict["skill_name"]
    user_id = get_current_user_id()  # 使用请求级上下文
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

    if user_id:
        # HTTP API 模式：使用用户私有目录
        skill_path = skill_dir / user_id / skill_name / "SKILL.md"
    else:
        # stdio/SSE 单用户模式：使用全局目录（向后兼容）
        skill_path = skill_dir / skill_name / "SKILL.md"

    # ... 其余逻辑不变
```

### 6.4 LoadSkillMetadataOp 改造

```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

async def async_execute(self):
    user_id = get_current_user_id()  # 使用请求级上下文
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

    if user_id:
        search_dir = skill_dir / user_id
    else:
        search_dir = skill_dir

    # ... 其余逻辑不变
```

### 6.5 ReadReferenceFileOp 改造

```python
from mcp_agentskills.core.utils.user_context import get_current_user_id

async def async_execute(self):
    skill_name = self.input_dict["skill_name"]
    file_name = self.input_dict["file_name"]
    user_id = get_current_user_id()  # 使用请求级上下文
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

    if user_id:
        file_path = skill_dir / user_id / skill_name / file_name
    else:
        file_path = skill_dir / skill_name / file_name

    # ... 其余逻辑不变
```

### 6.6 RunShellCommandOp 改造

```python
from mcp_agentskills.core.utils.user_context import get_current_user_id
from mcp_agentskills.core.utils.command_whitelist import validate_command
from mcp_agentskills.core.utils.skill_storage import tool_error_payload

async def async_execute(self):
    skill_name = self.input_dict["skill_name"]
    command = self.input_dict["command"]
    user_id = get_current_user_id()  # 使用请求级上下文
    skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()

    # 安全检查：验证命令是否在白名单中
    is_valid, error_msg = validate_command(command)
    if not is_valid:
        return tool_error_payload(error_msg, "COMMAND_BLOCKED")

    if user_id:
        work_dir = skill_dir / user_id / skill_name
    else:
        work_dir = skill_dir / skill_name

    # ... 其余逻辑不变
```

---

## 7. 项目结构

> **说明**: 项目根目录为 `agentskills-mcp/`，Python 包名为 `mcp_agentskills`。
>
> **注意**: 以下结构为当前仓库后端与前端控制台的实际结构。`core/security/`、`core/middleware/`、`models/`、`schemas/`、`repositories/`、`services/`、`api/`、`db/` 等目录为多用户改造引入的模块，已在仓库中创建。现有 `core/tools/` 和 `core/utils/` 目录将保留并扩展。

### 7.1 双模式架构

项目同时支持两种运行模式：

| 模式 | 入口 | 用途 | 传输方式 |
|------|------|------|---------|
| **FlowLLM 模式** | `main.py` (现有) | MCP 服务 | stdio/SSE |
| **FastAPI 模式** | `api_app.py` (新增) | Web API + MCP | HTTP/SSE |

```
agentskills-mcp/                  # 项目根目录
├── mcp_agentskills/              # Python 包目录
│   ├── __init__.py
│   ├── main.py                   # FlowLLM 应用入口（保留，用于 stdio/SSE）
│   ├── api_app.py                # FastAPI 应用入口（新增，用于 HTTP API / SSE）
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_parser.py      # 配置解析器（保留）
│   │   ├── default.yaml          # 默认配置（扩展）
│   │   └── settings.py           # Pydantic Settings
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── jwt_utils.py      # JWT工具
│   │   │   ├── password.py       # 密码哈希
│   │   │   └── token.py          # API Token生成
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 认证中间件
│   │   │   └── rate_limit.py     # 限流中间件
│   │   ├── tools/                # MCP工具（改造）
│   │   │   ├── __init__.py
│   │   │   ├── load_skill_metadata_op.py
│   │   │   ├── load_skill_op.py
│   │   │   ├── read_reference_file_op.py
│   │   │   └── run_shell_command_op.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── service_runner.py
│   │       ├── user_context.py    # 用户上下文管理（并发安全）
│   │       └── skill_storage.py  # Skill存储工具
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── skill.py
│   │   └── token.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── skill.py
│   │   ├── token.py
│   │   └── response.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── skill.py
│   │   └── token.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── skill.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── router.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── skills.py
│   │   │   └── tokens.py
│   │   └── mcp/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── http_handler.py
│   │       └── sse_handler.py
│   └── db/
│       ├── __init__.py
│       ├── session.py
│       └── migrations/
├── tests/
├── frontend/
├── docs/
├── pyproject.toml
└── README.md
```

### 7.2 启动方式

```bash
# FlowLLM 模式（stdio/SSE，无用户认证）
agentskills-mcp
# 或直接指定模块入口
python -m mcp_agentskills.main

# FastAPI 模式（HTTP API，多用户认证）
uvicorn mcp_agentskills.api_app:app --host 0.0.0.0 --port 8000
```

### 7.3 入口文件说明

#### main.py（保留）

```python
# 现有 FlowLLM 应用入口，用于 stdio/SSE 模式
# 无需修改，保持向后兼容

from flowllm.core.application import Application

class AgentSkillsMcpApp(Application):
    # ... 现有代码保留
```

#### api_app.py（新增）

```python
# FastAPI 应用入口，用于 HTTP API 模式
# 提供用户认证、Skill 管理、MCP 服务

from contextlib import asynccontextmanager
from fastapi import FastAPI

from mcp_agentskills.api.mcp import McpAppProxy, ensure_mcp_initialized, get_http_app, get_sse_app
from mcp_agentskills.api.router import api_router
from mcp_agentskills.db.session import init_db

@asynccontextmanager
async def lifespan(_application: FastAPI):
    await init_db()
    await ensure_mcp_initialized()
    yield

def create_application() -> FastAPI:
    app = FastAPI(lifespan=lifespan, redirect_slashes=False)
    app.include_router(api_router, prefix="/api/v1")
    app.mount("/mcp", McpAppProxy(get_http_app))
    app.mount("/sse", McpAppProxy(get_sse_app))
    return app

app = create_application()
```

---

### 7.4 前端控制台

前端控制台位于 `frontend/`，使用 Next.js App Router + Tailwind + shadcn/ui，提供登录、注册、Dashboard、Skills、Tokens、Profile、Security 等页面，并与后端 API 进行联调。

启动方式：

```bash
cd frontend
npm install
npm run dev
```

环境变量：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 8. 依赖清单

### 8.1 核心依赖

| 依赖包 | 版本要求 | 用途 |
|--------|---------|------|
| `fastapi` | >=0.109.0 | Web 框架 |
| `uvicorn[standard]` | >=0.27.0 | ASGI 服务器 |
| `sqlalchemy[asyncio]` | >=2.0.0 | ORM |
| `asyncpg` | >=0.29.0 | PostgreSQL 异步驱动 |
| `alembic` | >=1.13.0 | 数据库迁移 |
| `pydantic` | >=2.5.0 | 数据验证 |
| `pydantic-settings` | >=2.1.0 | 配置管理 |
| `PyJWT` | >=2.8.0 | JWT 处理 |
| `passlib[bcrypt]` | >=1.7.4 | 密码哈希 |
| `python-multipart` | >=0.0.6 | 文件上传 |
| `flowllm` | >=0.2.0.7 | MCP 框架 |
| `loguru` | >=0.7.0 | 日志 |
| `httpx` | >=0.26.0 | HTTP 客户端 |
| `psutil` | >=5.9.0 | 系统监控 |

### 8.2 开发依赖

| 依赖包 | 版本要求 | 用途 |
|--------|---------|------|
| `pytest` | >=8.0.0 | 测试框架 |
| `pytest-asyncio` | >=0.23.0 | 异步测试支持 |
| `pytest-cov` | >=4.1.0 | 测试覆盖率 |
| `aiosqlite` | >=0.19.0 | SQLite 异步驱动（测试用） |
| `pre-commit` | >=3.6.0 | Git 钩子 |
| `ruff` | >=0.1.0 | 代码格式化 |
| `mypy` | >=1.8.0 | 类型检查 |

### 8.3 pyproject.toml 示例

```toml
[project]
name = "mcp-agentskills"
version = "1.0.0"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "PyJWT>=2.8.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "flowllm>=0.2.0.7",
    "loguru>=0.7.0",
    "httpx>=0.26.0",
    "psutil>=5.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "aiosqlite>=0.19.0",
    "pre-commit>=3.6.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]
```

---

## 9. 配置规范

### 9.1 环境变量

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentskills
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/agentskills/app.log

# 存储
SKILL_STORAGE_PATH=/data/skills

# 限流配置
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# LLM（可选：仅在需要调用 LLM Provider 时配置）
FLOW_LLM_API_KEY=your-api-key
FLOW_LLM_BASE_URL=https://api.openai.com/v1
```

### 9.2 Settings类

```python
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator, ValidationInfo


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 应用
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = []

    # 时区配置（用于统一处理时间戳）
    # 建议使用 UTC 时区，确保 datetime.now(timezone.utc) 调用的一致性
    TIMEZONE: str = "UTC"

    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/var/log/agentskills/app.log"

    # 存储
    SKILL_STORAGE_PATH: str = "/data/skills"

    # 限流配置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # LLM
    FLOW_LLM_API_KEY: str = ""
    FLOW_LLM_BASE_URL: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    import json

                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_cors_origins(self):
        # 生产环境 CORS 安全配置
        if not self.DEBUG and (not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS):
            raise ValueError(
                "生产环境 CORS_ORIGINS 必须显式配置且不能包含通配符 '*'"
            )
        return self

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY 长度必须至少 32 字符")
        return v

    @field_validator("DATABASE_POOL_SIZE", "DATABASE_MAX_OVERFLOW")
    @classmethod
    def validate_pool_settings(cls, v, info: ValidationInfo):
        field_name = info.field_name
        if v < 1:
            raise ValueError(f"{field_name} 必须至少为 1")
        if v > 100:
            raise ValueError(f"{field_name} 不能超过 100")
        return v

    @field_validator("DATABASE_POOL_TIMEOUT", "DATABASE_POOL_RECYCLE")
    @classmethod
    def validate_timeout_settings(cls, v, info: ValidationInfo):
        field_name = info.field_name
        if v < 1:
            raise ValueError(f"{field_name} 必须至少为 1 秒")
        if v > 3600:
            raise ValueError(f"{field_name} 不能超过 3600 秒")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
```

# 数据库连接池配置示例（db/session.py）
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 创建异步引擎，使用连接池配置
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,          # 连接池大小
    max_overflow=settings.DATABASE_MAX_OVERFLOW,    # 超出池大小的额外连接数
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,    # 获取连接的超时时间（秒）
    pool_recycle=settings.DATABASE_POOL_RECYCLE,    # 连接回收时间（秒）
    pool_pre_ping=True,                             # 使用前检测连接是否有效
    echo=settings.DEBUG,                            # 调试模式下打印SQL
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    '''获取数据库会话的依赖函数'''
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    '''初始化数据库（创建所有表）'''
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""
```

---

## 10. 安全要求

### 10.1 密码安全

- 使用bcrypt进行密码哈希
- 最小密码长度8位
- 建议包含大小写字母、数字、特殊字符

### 10.2 Token安全

- API Token仅在创建时显示一次
- 存储SHA256哈希值而非明文
- 支持Token过期和撤销

### 10.3 文件上传安全

- **文件类型验证**: 仅允许以下扩展名
  - `.md` - Markdown 文档
  - `.py` - Python 脚本
  - `.js` - JavaScript 脚本
  - `.sh` - Shell 脚本
  - `.txt` - 纯文本
  - `.json` - JSON 文件
  - `.yaml`, `.yml` - YAML 配置文件
- **大小限制**:
  - 单文件大小: 10MB
  - 总上传大小: 100MB
  - 单个 Skill 文件总数: 50个
- **路径安全**:
  - 禁止 `..` 路径遍历
  - 禁止绝对路径
  - 文件名仅允许字母、数字、下划线、连字符和点

#### 路径遍历防护实现

```python
# core/utils/skill_storage.py
import re
from pathlib import Path
from typing import Optional

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {".md", ".py", ".js", ".sh", ".txt", ".json", ".yaml", ".yml"}

# 文件名安全正则：仅允许字母、数字、下划线、连字符和点
SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """验证文件路径安全性

    Args:
        file_path: 待验证的文件路径

    Returns:
        tuple[bool, str]: (是否安全, 错误信息)
    """
    # 1. 检查空路径
    if not file_path or not file_path.strip():
        return False, "File path cannot be empty"

    # 2. 检查路径遍历攻击
    if ".." in file_path:
        return False, "Path traversal detected: '..' is not allowed"

    # 3. 检查绝对路径
    if file_path.startswith("/") or (len(file_path) > 1 and file_path[1] == ":"):
        return False, "Absolute paths are not allowed"

    # 4. 检查路径分隔符（仅允许正斜杠）
    if "\\" in file_path:
        return False, "Backslashes are not allowed in file path"

    # 5. 检查每个路径组件
    parts = file_path.split("/")
    for part in parts:
        if not part:
            continue
        if not SAFE_FILENAME_PATTERN.match(part):
            return False, f"Invalid filename component: '{part}'"

    # 6. 检查文件扩展名
    ext = Path(file_path).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not allowed"

    return True, "OK"


def get_safe_skill_path(base_dir: Path, user_id: str, skill_name: str, file_path: str) -> Optional[Path]:
    """获取安全的 Skill 文件路径

    Args:
        base_dir: 基础目录
        user_id: 用户 ID
        skill_name: Skill 名称
        file_path: 相对文件路径

    Returns:
        Optional[Path]: 安全的完整路径，如果验证失败则返回 None
    """
    # 验证文件路径
    is_valid, error = validate_file_path(file_path)
    if not is_valid:
        return None

    # 验证 skill_name
    is_valid, _ = validate_file_path(skill_name)
    if not is_valid:
        return None

    # 构建完整路径
    full_path = base_dir / user_id / skill_name / file_path

    # 解析并验证最终路径仍在允许的目录内
    try:
        full_path = full_path.resolve()
        base_path = (base_dir / user_id).resolve()

        if not str(full_path).startswith(str(base_path)):
            return None  # 路径逃逸

        return full_path
    except Exception:
        return None


def validate_filename(filename: str) -> tuple[bool, str]:
    """验证文件名安全性

    Args:
        filename: 待验证的文件名

    Returns:
        tuple[bool, str]: (是否安全, 错误信息)
    """
    if not filename or not filename.strip():
        return False, "Filename cannot be empty"

    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"

    if not SAFE_FILENAME_PATTERN.match(filename):
        return False, "Filename contains invalid characters"

    ext = Path(filename).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not allowed"

    return True, "OK"
```

#### 使用示例

```python
# 在 API 端点中使用
from mcp_agentskills.core.utils.skill_storage import get_safe_skill_path, validate_filename
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.services.skill import SkillService

@app.post("/api/v1/skills/upload")
async def upload_skill_file(
    skill_id: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session=Depends(get_async_session),
):
    # 验证文件名
    is_valid, error = validate_filename(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # skill_id 是数据库记录 ID；目录名使用 skill.name（与 /data/skills/{user_id}/{skill_name}/ 结构一致）
    service = SkillService(SkillRepository(session))
    skill = await service.get_skill(current_user, skill_id)

    # 获取安全路径
    safe_path = get_safe_skill_path(
        base_dir=Path(settings.SKILL_STORAGE_PATH),
        user_id=str(current_user.id),
        skill_name=skill.name,
        file_path=file.filename,
    )

    if not safe_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # 写入文件
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    safe_path.write_bytes(content)
```

### 10.4 API安全

- 所有用户API需要JWT认证
- MCP API需要API Token认证
- 实现请求限流

---

## 11. 错误处理

### 11.1 标准错误响应格式

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### 11.2 HTTP状态码规范

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

## 12. 测试要求

### 12.1 测试覆盖率

- 单元测试覆盖率 >= 80%
- 核心业务逻辑覆盖率 >= 90%

### 12.2 测试类型

- 单元测试：Services、Repositories
- 集成测试：API端点
- E2E测试：完整用户流程

### 12.3 测试数据库

使用内存SQLite进行测试：
```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

> **兼容性注意事项**: PostgreSQL 和 SQLite 在某些 SQL 语法上有差异：
> - **UUID 类型**: PostgreSQL 原生支持 UUID 类型，SQLite 使用 TEXT 存储。SQLAlchemy 会自动处理，但原生 SQL 需要注意。
> - **JSON 操作**: PostgreSQL 支持丰富的 JSON 操作符，SQLite 支持有限。
> - **自增主键**: PostgreSQL 使用 SERIAL/IDENTITY，SQLite 使用 AUTOINCREMENT。
> - **布尔类型**: PostgreSQL 有原生 BOOLEAN，SQLite 使用 0/1 整数。
>
> **建议**:
> - 优先使用 SQLAlchemy ORM 方法，避免原生 SQL
> - 当前仓库主键 UUID 由应用层生成（uuid4），迁移脚本不依赖 PostgreSQL 的 gen_random_uuid()
> - 如需使用 PostgreSQL 特有特性，建议在测试环境中使用 `pytest-postgresql` 启动真实 PostgreSQL 实例
> - 或者在代码中使用条件判断兼容两种数据库

---

## 13. 部署要求

### 13.1 Docker支持

- 提供Dockerfile
- 提供docker-compose.yml（包含PostgreSQL）

### 13.2 数据库迁移

- 使用Alembic进行数据库迁移
- 提供初始化迁移脚本

#### Alembic 异步配置

由于使用 SQLAlchemy 2.0 + asyncpg，需要特殊配置异步支持：

**env.py 配置示例**:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from mcp_agentskills.db.session import Base
from mcp_agentskills.config.settings import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**迁移命令**:

```bash
# 初始化 Alembic（如果尚未初始化）
alembic init mcp_agentskills/db/migrations

# 创建新迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 13.3 健康检查

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
