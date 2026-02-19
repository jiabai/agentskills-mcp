# AgentSkills MCP 多用户Web服务改造文档

> 本文档为Claude Code提供完整的项目改造指南，可直接读取并生成完整无误的项目代码。

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构设计](#2-技术架构设计)
3. [项目结构](#3-项目结构)
4. [数据库设计](#4-数据库设计)
5. [API接口设计](#5-api接口设计)
6. [核心模块实现规范](#6-核心模块实现规范)
7. [配置文件规范](#7-配置文件规范)
8. [依赖清单](#8-依赖清单)
9. [部署说明](#9-部署说明)

---

## 1. 项目概述

### 1.1 改造目标

将现有的单用户MCP服务改造为支持多用户的Web服务平台，实现以下核心功能：

| 功能模块 | 描述 |
|---------|------|
| 用户账户管理 | 注册、登录、认证、账户删除 |
| 私有Skill空间 | 每个用户独立管理自己的Agent Skills |
| MCP服务认证 | 通过私有Token访问MCP服务 |

### 1.2 技术选型

| 层级 | 技术栈 | 版本要求 |
|------|--------|---------|
| Web框架 | FastAPI | >=0.109.0 |
| ORM | SQLAlchemy | >=2.0.0 |
| 数据库 | PostgreSQL | >=14.0 |
| 认证 | python-jose[cryptography] + passlib | 最新版 |
| 文件存储 | 本地文件系统（可扩展MinIO/S3） | - |
| MCP框架 | FlowLLM | >=0.2.0.7 |
| 异步支持 | asyncio + asyncpg | 最新版 |

### 1.3 兼容性要求

- 保持现有MCP工具（load_skill_metadata, load_skill, read_reference_file, run_shell_command）的核心逻辑
- 保持对现有Skill格式的完全兼容
- 支持stdio/SSE/HTTP三种传输模式

---

## 2. 技术架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Web Client  │  │  MCP Client  │  │  CLI Client  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                          │  │
│  │  - CORS Middleware                                            │  │
│  │  - Authentication Middleware (JWT)                            │  │
│  │  - Rate Limiting Middleware                                   │  │
│  │  - Request Logging Middleware                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Service Layer                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ AuthService │  │ UserService │  │ SkillService│  │MCPService │  │
│  │ - 注册      │  │ - CRUD      │  │ - CRUD      │  │ - Tool调用│  │
│  │ - 登录      │  │ - 配置      │  │ - 隔离      │  │ - 上下文  │  │
│  │ - Token管理 │  │             │  │ - 导入导出  │  │           │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Access Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  SQLAlchemy ORM + Async Engine                                │  │
│  │  - User Repository                                            │  │
│  │  - Skill Repository                                           │  │
│  │  - Token Repository                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage Layer                                   │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐  │
│  │  PostgreSQL         │  │  File Storage (User Skills)         │  │
│  │  - users            │  │  /data/skills/{user_id}/{skill_name}│  │
│  │  - skills           │  │                                     │  │
│  │  - api_tokens       │  │                                     │  │
│  └─────────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 认证流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  /auth/login│────▶│  JWT Token  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Validate   │     │  API Token  │
                    │  Credentials│     │  (for MCP)  │
                    └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  MCP Access │
                                        │  with Token │
                                        └─────────────┘
```

### 2.3 用户Skill隔离机制

```
/data/skills/
├── {user_id_1}/
│   ├── pdf/
│   │   ├── SKILL.md
│   │   ├── reference.md
│   │   └── scripts/
│   └── xlsx/
│       └── SKILL.md
├── {user_id_2}/
│   └── pdf/
│       └── SKILL.md
└── ...
```

---

## 3. 项目结构

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
│   ├── tools/                   # MCP工具（保留并改造）
│   │   ├── __init__.py
│   │   ├── load_skill_metadata_op.py
│   │   ├── load_skill_op.py
│   │   ├── read_reference_file_op.py
│   │   └── run_shell_command_op.py
│   └── utils/
│       ├── __init__.py
│       ├── service_runner.py    # 服务运行器（保留）
│       └── skill_storage.py     # Skill存储工具
├── models/
│   ├── __init__.py
│   ├── base.py                  # 基础模型
│   ├── user.py                  # 用户模型
│   ├── skill.py                 # Skill模型
│   └── token.py                 # API Token模型
├── schemas/
│   ├── __init__.py
│   ├── user.py                  # 用户Pydantic schemas
│   ├── skill.py                 # Skill Pydantic schemas
│   ├── token.py                 # Token Pydantic schemas
│   └── response.py              # 通用响应schemas
├── repositories/
│   ├── __init__.py
│   ├── base.py                  # 基础Repository
│   ├── user.py                  # 用户Repository
│   ├── skill.py                 # Skill Repository
│   └── token.py                 # Token Repository
├── services/
│   ├── __init__.py
│   ├── auth.py                  # 认证服务
│   ├── user.py                  # 用户服务
│   ├── skill.py                 # Skill服务
│   └── mcp.py                   # MCP服务
├── api/
│   ├── __init__.py
│   ├── deps.py                  # 依赖注入
│   ├── router.py                # 路由汇总
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证API
│   │   ├── users.py             # 用户API
│   │   ├── skills.py            # Skill管理API
│   │   └── mcp.py               # MCP服务API
│   └── mcp/
│       ├── __init__.py
│       ├── http_handler.py      # HTTP MCP处理器
│       └── sse_handler.py       # SSE MCP处理器
└── db/
    ├── __init__.py
    ├── session.py               # 数据库会话
    └── migrations/              # Alembic迁移
        └── versions/
```

---

## 4. 数据库设计

### 4.1 ER图

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      users       │       │      skills      │       │    api_tokens    │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │───┐   │ id (PK)          │   ┌───│ id (PK)          │
│ email            │   │   │ user_id (FK)     │───┘   │ user_id (FK)     │
│ hashed_password  │   │   │ name             │       │ token_hash       │
│ username         │   │   │ description      │       │ name             │
│ is_active        │   │   │ skill_dir        │       │ is_active        │
│ is_superuser     │   │   │ created_at       │       │ expires_at       │
│ created_at       │   │   │ updated_at       │       │ last_used_at     │
│ updated_at       │   │   │ is_active        │       │ created_at       │
└──────────────────┘   │   └──────────────────┘       └──────────────────┘
                       │
                       └──────────────────────────────────────┘
```

### 4.2 表结构定义

#### 4.2.1 users表

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

#### 4.2.2 skills表

```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    skill_dir VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

CREATE INDEX idx_skills_user_id ON skills(user_id);
CREATE INDEX idx_skills_name ON skills(name);
```

#### 4.2.3 api_tokens表

```sql
CREATE TABLE api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_tokens_user_id ON api_tokens(user_id);
CREATE INDEX idx_api_tokens_token_hash ON api_tokens(token_hash);
```

### 4.3 SQLAlchemy模型定义

#### models/base.py

```python
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
```

#### models/user.py

```python
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    api_tokens = relationship("APIToken", back_populates="user", cascade="all, delete-orphan")
```

#### models/skill.py

```python
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_dir: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="skills")

    __table_args__ = (
        {"unique_constraint": ("user_id", "name")},
    )
```

#### models/token.py

```python
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class APIToken(Base, TimestampMixin):
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", back_populates="api_tokens")
```

---

## 5. API接口设计

### 5.1 接口概览

| 模块 | 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|------|
| **认证** | /api/v1/auth/register | POST | 否 | 用户注册 |
| | /api/v1/auth/login | POST | 否 | 用户登录 |
| | /api/v1/auth/refresh | POST | 是 | 刷新Token |
| | /api/v1/auth/logout | POST | 是 | 登出 |
| **用户** | /api/v1/users/me | GET | 是 | 获取当前用户信息 |
| | /api/v1/users/me | PUT | 是 | 更新用户信息 |
| | /api/v1/users/me | DELETE | 是 | 删除账户 |
| | /api/v1/users/me/password | PUT | 是 | 修改密码 |
| **Token** | /api/v1/tokens | GET | 是 | 列出API Tokens |
| | /api/v1/tokens | POST | 是 | 创建API Token |
| | /api/v1/tokens/{token_id} | DELETE | 是 | 删除API Token |
| **Skill** | /api/v1/skills | GET | 是 | 列出Skills |
| | /api/v1/skills | POST | 是 | 创建Skill |
| | /api/v1/skills/{skill_id} | GET | 是 | 获取Skill详情 |
| | /api/v1/skills/{skill_id} | PUT | 是 | 更新Skill |
| | /api/v1/skills/{skill_id} | DELETE | 是 | 删除Skill |
| | /api/v1/skills/upload | POST | 是 | 上传Skill文件 |
| | /api/v1/skills/{skill_id}/files | GET | 是 | 列出Skill文件 |
| **MCP** | /mcp | POST | Token | HTTP MCP端点 |
| | /sse | GET | Token | SSE MCP端点 |

### 5.2 详细接口规范

#### 5.2.1 认证接口

##### POST /api/v1/auth/register

**请求体**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123!"
}
```

**响应** (201 Created):
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**错误响应**:
- 400: 邮箱/用户名已存在
- 422: 请求参数验证失败

##### POST /api/v1/auth/login

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**响应** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

##### POST /api/v1/auth/refresh

**请求头**:
```
Authorization: Bearer {refresh_token}
```

**响应** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 5.2.2 用户接口

##### GET /api/v1/users/me

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200 OK):
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "skill_count": 5,
  "token_count": 2
}
```

##### DELETE /api/v1/users/me

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "password": "SecurePassword123!",
  "confirm": "DELETE MY ACCOUNT"
}
```

**响应** (204 No Content)

#### 5.2.3 API Token接口

##### POST /api/v1/tokens

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "name": "My MCP Token",
  "expires_in_days": 365
}
```

**响应** (201 Created):
```json
{
  "id": "uuid-string",
  "name": "My MCP Token",
  "token": "ask_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "created_at": "2025-01-01T00:00:00Z",
  "expires_at": "2026-01-01T00:00:00Z"
}
```

**重要**: `token` 字段仅在创建时返回一次，后续无法再次获取。

##### GET /api/v1/tokens

**响应** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid-string",
      "name": "My MCP Token",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "expires_at": "2026-01-01T00:00:00Z",
      "last_used_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### 5.2.4 Skill接口

##### GET /api/v1/skills

**查询参数**:
- `skip`: int, 默认0
- `limit`: int, 默认20, 最大100
- `search`: string, 可选, 按名称搜索

**响应** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid-string",
      "name": "pdf",
      "description": "PDF处理技能",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "file_count": 3
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

##### POST /api/v1/skills

**请求体**:
```json
{
  "name": "pdf",
  "description": "PDF处理技能"
}
```

**响应** (201 Created):
```json
{
  "id": "uuid-string",
  "name": "pdf",
  "description": "PDF处理技能",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "skill_dir": "/data/skills/{user_id}/pdf"
}
```

##### POST /api/v1/skills/upload

**Content-Type**: multipart/form-data

**表单字段**:
- `skill_id`: string, 可选, 如果提供则更新现有Skill
- `skill_name`: string, 如果不提供skill_id则必填
- `description`: string, 可选
- `files`: file[], 必填, 上传的文件列表

**响应** (201 Created):
```json
{
  "id": "uuid-string",
  "name": "pdf",
  "description": "PDF处理技能",
  "uploaded_files": [
    "SKILL.md",
    "reference.md",
    "scripts/convert.py"
  ]
}
```

#### 5.2.5 MCP接口

##### POST /mcp

**请求头**:
```
Authorization: Bearer {api_token}
Content-Type: application/json
```

**请求体** (MCP协议格式):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "load_skill",
    "arguments": {
      "skill_name": "pdf"
    }
  }
}
```

**响应**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "# PDF Skill\n\nThis skill helps you work with PDF files..."
      }
    ]
  }
}
```

##### GET /sse

**请求头**:
```
Authorization: Bearer {api_token}
Accept: text/event-stream
```

**响应**: Server-Sent Events流

---

## 6. 核心模块实现规范

### 6.1 数据库会话管理

#### db/session.py

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from mcp_agentskills.config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 6.2 安全模块

#### core/security/password.py

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

#### core/security/jwt.py

```python
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from mcp_agentskills.config.settings import settings


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

#### core/security/token.py

```python
import hashlib
import secrets
from datetime import datetime, timedelta

from mcp_agentskills.config.settings import settings


def generate_api_token() -> str:
    random_bytes = secrets.token_bytes(32)
    token = "ask_live_" + secrets.token_hex(32)
    return token


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    return hash_token(token) == token_hash
```

### 6.3 认证中间件

#### core/middleware/auth.py

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_agentskills.core.security.jwt import decode_token
from mcp_agentskills.db.session import get_db
from mcp_agentskills.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user
```

### 6.4 MCP认证中间件

#### api/mcp/auth.py

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_agentskills.core.security.token import verify_token_hash
from mcp_agentskills.db.session import get_db
from mcp_agentskills.models.token import APIToken
from mcp_agentskills.models.user import User

security = HTTPBearer()


async def get_user_by_api_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    result = await db.execute(
        select(APIToken).where(APIToken.token_hash == token_hash)
    )
    api_token = result.scalar_one_or_none()
    
    if api_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
        )
    
    if not api_token.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token is inactive",
        )
    
    if api_token.expires_at and api_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token has expired",
        )
    
    api_token.last_used_at = datetime.utcnow()
    await db.commit()
    
    result = await db.execute(select(User).where(User.id == api_token.user_id))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user
```

### 6.5 Skill存储服务

#### core/utils/skill_storage.py

```python
import shutil
from pathlib import Path
from typing import BinaryIO

from mcp_agentskills.config.settings import settings


class SkillStorage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(settings.SKILL_STORAGE_PATH)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_user_skill_dir(self, user_id: str, skill_name: str) -> Path:
        return self.base_dir / user_id / skill_name
    
    def create_skill_dir(self, user_id: str, skill_name: str) -> Path:
        skill_dir = self.get_user_skill_dir(user_id, skill_name)
        skill_dir.mkdir(parents=True, exist_ok=True)
        return skill_dir
    
    def delete_skill_dir(self, user_id: str, skill_name: str) -> bool:
        skill_dir = self.get_user_skill_dir(user_id, skill_name)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            return True
        return False
    
    def save_file(self, user_id: str, skill_name: str, file_path: str, content: BinaryIO) -> Path:
        skill_dir = self.get_user_skill_dir(user_id, skill_name)
        full_path = skill_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            shutil.copyfileobj(content, f)
        
        return full_path
    
    def list_files(self, user_id: str, skill_name: str) -> list[str]:
        skill_dir = self.get_user_skill_dir(user_id, skill_name)
        if not skill_dir.exists():
            return []
        
        files = []
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(skill_dir)
                files.append(str(relative_path))
        
        return files
    
    def skill_exists(self, user_id: str, skill_name: str) -> bool:
        skill_dir = self.get_user_skill_dir(user_id, skill_name)
        return skill_dir.exists() and (skill_dir / "SKILL.md").exists()
```

### 6.6 改造后的MCP工具

#### core/tools/load_skill_op.py

```python
from pathlib import Path

from loguru import logger

from flowllm.core.context import C
from flowllm.core.op import BaseAsyncToolOp
from flowllm.core.schema import ToolCall


@C.register_op()
class LoadSkillOp(BaseAsyncToolOp):
    def build_tool_call(self) -> ToolCall:
        return ToolCall(
            **{
                "name": "load_skill",
                "description": "Load one skill's instructions from the SKILL.md.",
                "input_schema": {
                    "skill_name": {
                        "type": "string",
                        "description": "skill name",
                        "required": True,
                    },
                },
            },
        )

    async def async_execute(self):
        skill_name = self.input_dict["skill_name"]
        user_id = C.service_config.metadata.get("user_id")
        skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()
        
        if user_id:
            skill_path = skill_dir / user_id / skill_name / "SKILL.md"
        else:
            skill_path = skill_dir / skill_name / "SKILL.md"
        
        logger.info(f"Tool called: load_skill(skill_name='{skill_name}') path={skill_path}")
        
        if not skill_path.exists():
            content = f"Skill '{skill_name}' not found"
            logger.exception(content)
            self.set_output(content)
            return
        
        content: str = skill_path.read_text(encoding="utf-8")
        self.set_output(content)
        
        logger.info(f"Loaded skill: {skill_name} size={len(content)}")
```

#### core/tools/load_skill_metadata_op.py

```python
from pathlib import Path

from loguru import logger

from flowllm.core.context import C
from flowllm.core.op import BaseAsyncToolOp
from flowllm.core.schema import ToolCall


@C.register_op()
class LoadSkillMetadataOp(BaseAsyncToolOp):
    def build_tool_call(self) -> ToolCall:
        return ToolCall(
            **{
                "name": "load_skill_metadata",
                "description": "Load metadata for all available skills.",
                "input_schema": {},
            },
        )

    @staticmethod
    async def parse_skill_metadata(content: str, path: str) -> dict[str, str] | None:
        parts = content.split("---")
        if len(parts) < 3:
            logger.warning(f"No YAML frontmatter found in skill from {path}")
            return None
        
        frontmatter_text = parts[1].strip()
        name = None
        description = None
        
        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("description:"):
                description = line.split(":", 1)[1].strip().strip("\"'")
        
        if not name or not description:
            logger.warning(f"Missing name or description in skill from {path}")
            return None
        
        return {"name": name, "description": description}

    async def async_execute(self):
        user_id = C.service_config.metadata.get("user_id")
        skill_dir = Path(C.service_config.metadata["skill_dir"]).resolve()
        
        if user_id:
            search_dir = skill_dir / user_id
        else:
            search_dir = skill_dir
        
        logger.info(f"Tool called: load_skill_metadata(path={search_dir})")
        
        if not search_dir.exists():
            self.set_output("No skills available.")
            return
        
        skill_files = list(search_dir.rglob("SKILL.md"))
        
        if not skill_files:
            self.set_output("No skills available.")
            return
        
        skill_num = 0
        skill_metadata_context = 'Available skills (each line is "- <skill_name>: <skill_description>"):'
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding="utf-8")
            metadata = await self.parse_skill_metadata(content, str(skill_file))
            
            if metadata:
                skill_num += 1
                name = metadata["name"]
                description = metadata["description"]
                skill_metadata_context += f"\n- {name}: {description}"
                logger.info(f"Loaded skill {name} metadata")
        
        logger.info(f"Loaded {skill_num} skill metadata entries")
        self.set_output(skill_metadata_context)
```

### 6.7 FastAPI应用入口

#### main.py

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_agentskills.api.router import api_router
from mcp_agentskills.config.settings import settings
from mcp_agentskills.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_application() -> FastAPI:
    app = FastAPI(
        title="AgentSkills MCP API",
        description="Multi-user Agent Skills MCP Service",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_agentskills.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
```

### 6.8 API路由汇总

#### api/router.py

```python
from fastapi import APIRouter

from mcp_agentskills.api.v1 import auth, users, skills, tokens
from mcp_agentskills.api.mcp import http_handler, sse_handler

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(http_handler.router, prefix="/mcp", tags=["mcp"])
api_router.include_router(sse_handler.router, prefix="/sse", tags=["mcp"])
```

---

## 7. 配置文件规范

### 7.1 环境变量配置

#### .env.example

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/agentskills
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

DEBUG=false
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

SKILL_STORAGE_PATH=/data/skills

FLOW_LLM_API_KEY=your-llm-api-key
FLOW_LLM_BASE_URL=https://api.openai.com/v1
```

### 7.2 Pydantic Settings

#### config/settings.py

```python
from typing import List
from pydantic_settings import BaseSettings


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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### 7.3 扩展后的default.yaml

```yaml
backend: mcp
thread_pool_max_workers: 128

mcp:
  transport: http
  host: "0.0.0.0"
  port: 8001

http:
  host: "0.0.0.0"
  port: 8002

flow:
  load_skill_metadata:
    flow_content: LoadSkillMetadataOp()

  load_skill:
    flow_content: LoadSkillOp()

  read_reference_file:
    flow_content: ReadReferenceFileOp()

  run_shell_command:
    flow_content: RunShellCommandOp()

llm:
  default:
    backend: openai_compatible
    model_name: gpt-4

embedding_model:
  default:
    backend: openai_compatible
    model_name: text-embedding-3-small
    params:
      dimensions: 1024

metadata:
  skill_dir: "/data/skills"
  user_id: null
```

---

## 8. 依赖清单

### 8.1 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-agentskills"
version = "1.0.0"
description = "Multi-user Agent Skills MCP Service"
authors = [
    { name = "Your Name", email = "your@email.com" },
]
license = {text = "Apache-2.0"}
readme = "README.md"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "flowllm>=0.2.0.7",
    "loguru>=0.7.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
    "pre-commit>=3.6.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[project.scripts]
agentskills-mcp = "mcp_agentskills.main:main"
agentskills-api = "mcp_agentskills.main:run_api"

[tool.setuptools.packages.find]
where = ["."]
include = ["mcp_agentskills*"]
exclude = ["tests*"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
```

### 8.2 requirements.txt

```txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
flowllm>=0.2.0.7
loguru>=0.7.0
httpx>=0.26.0
```

---

## 9. 部署说明

### 9.1 Docker部署

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/skills

EXPOSE 8000

CMD ["uvicorn", "mcp_agentskills.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/agentskills
      - SECRET_KEY=${SECRET_KEY}
      - FLOW_LLM_API_KEY=${FLOW_LLM_API_KEY}
      - FLOW_LLM_BASE_URL=${FLOW_LLM_BASE_URL}
      - SKILL_STORAGE_PATH=/data/skills
    volumes:
      - skill_data:/data/skills
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=agentskills
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  skill_data:
```

### 9.2 数据库迁移

#### 初始化Alembic

```bash
alembic init mcp_agentskills/db/migrations
```

#### alembic.ini

```ini
[alembic]
script_location = mcp_agentskills/db/migrations
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### 创建迁移

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 9.3 启动命令

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/agentskills"
export SECRET_KEY="your-secret-key"
export FLOW_LLM_API_KEY="your-api-key"

alembic upgrade head

uvicorn mcp_agentskills.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 10. 实现优先级

### Phase 1: 核心基础设施 (Week 1)

1. 数据库模型与迁移
2. 用户认证系统（注册、登录、JWT）
3. API Token生成与验证

### Phase 2: 用户与Skill管理 (Week 2)

1. 用户CRUD接口
2. Skill CRUD接口
3. Skill文件上传与管理
4. Skill存储服务

### Phase 3: MCP服务集成 (Week 3)

1. MCP HTTP端点（带认证）
2. MCP SSE端点（带认证）
3. 改造现有MCP工具支持用户隔离
4. 集成测试

### Phase 4: 优化与部署 (Week 4)

1. 性能优化
2. 文档完善
3. Docker部署配置
4. CI/CD流程

---

## 11. 测试规范

### 11.1 测试结构

```
tests/
├── conftest.py              # 测试配置与fixtures
├── test_api/
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_skills.py
│   └── test_mcp.py
├── test_services/
│   ├── test_auth_service.py
│   └── test_skill_service.py
└── test_tools/
    ├── test_load_skill_op.py
    └── test_load_skill_metadata_op.py
```

### 11.2 测试配置

#### tests/conftest.py

```python
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from mcp_agentskills.db.session import Base, get_db
from mcp_agentskills.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

---

## 12. 安全注意事项

1. **密码存储**: 使用bcrypt进行密码哈希，不存储明文密码
2. **JWT安全**: 使用强密钥，设置合理的过期时间
3. **API Token**: 仅在创建时显示一次，存储哈希值
4. **文件上传**: 验证文件类型，限制文件大小，防止路径遍历
5. **SQL注入**: 使用SQLAlchemy ORM，避免原生SQL
6. **CORS**: 生产环境配置具体的允许域名
7. **Rate Limiting**: 实现API限流防止滥用

---

## 附录A: MCP客户端配置示例

### 使用API Token连接MCP服务

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

### SSE模式连接

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "type": "sse",
      "url": "https://your-domain.com/sse",
      "headers": {
        "Authorization": "Bearer ask_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

---

**文档版本**: 1.0.0  
**最后更新**: 2025-01-01  
**作者**: Claude Code Assistant
