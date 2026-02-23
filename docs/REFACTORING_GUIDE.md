# AgentSkills MCP 多用户Web服务改造指南

> 本文档专注于重构步骤和注意事项，详细技术规范请参考 [project-spec.md](./project-spec.md)。

---

## 文档关系说明

| 文档 | 职责 |
|------|------|
| **project-spec.md** | 权威技术规范（数据模型、API设计、认证机制等） |
| **task_list.md** | 任务分解与执行顺序 |
| **checklist.md** | 验证检查清单 |
| **本文档** | 重构步骤、注意事项、最佳实践 |

---

## 1. 重构概述

### 1.1 改造目标

将现有的单用户MCP服务改造为支持多用户的Web服务平台：
- 用户账户管理（注册、登录、认证、账户删除）
- 私有Skill空间（每个用户独立管理）
- MCP服务认证（通过私有Token访问）

### 1.2 核心改动点

| 改动类型 | 描述 | 影响范围 |
|---------|------|---------|
| **新增模块** | 用户系统、认证系统、API层 | 大量新代码 |
| **改造模块** | MCP工具支持用户隔离 | 4个Op文件 |
| **保留模块** | FlowLLM框架、配置解析 | 无改动 |
| **扩展模块** | 配置系统、存储系统 | 小量改动 |

---

## 2. 重构步骤

### Phase 1: 基础设施搭建（Week 1）

#### 步骤 1.1: 创建配置模块

```bash
# 创建文件
touch mcp_agentskills/config/settings.py
```

**注意事项**:
- 使用 Pydantic Settings 管理环境变量
- 敏感信息（SECRET_KEY, DATABASE_URL）必须通过环境变量配置
- 开发环境使用 `.env` 文件，生产环境使用真实环境变量

#### 步骤 1.2: 创建数据库模型

```bash
# 创建目录结构
mkdir -p mcp_agentskills/models
touch mcp_agentskills/models/{__init__,base,user,skill,token}.py
```

**注意事项**:
- 使用 SQLAlchemy 2.0 的声明式语法
- 所有模型继承自 `Base` 和 `TimestampMixin`
- 外键关系使用 `relationship` 定义，设置 `cascade="all, delete-orphan"`

#### 步骤 1.3: 配置数据库迁移

```bash
# 初始化 Alembic
alembic init mcp_agentskills/db/migrations

# 编辑 alembic.ini 和 env.py

# 创建初始迁移
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**注意事项**:
- `env.py` 需要配置异步支持
- 迁移文件纳入版本控制

### Phase 2: 安全与认证模块（Week 1-2）

#### 步骤 2.1: 创建安全工具

```bash
mkdir -p mcp_agentskills/core/security
touch mcp_agentskills/core/security/{__init__,password,jwt,token}.py
```

**注意事项**:
- 密码使用 bcrypt 哈希，cost factor 建议 12
- JWT 密钥至少 32 字符，生产环境必须更换
- API Token 格式: `ask_live_{64位hex}`，仅存储 SHA256 哈希

#### 步骤 2.2: 创建认证中间件

```bash
mkdir -p mcp_agentskills/core/middleware
touch mcp_agentskills/core/middleware/{__init__,auth}.py
```

**注意事项**:
- JWT 认证用于 Web API
- API Token 认证用于 MCP 服务
- 两种认证方式使用不同的依赖函数

### Phase 3: API 接口实现（Week 2）

#### 步骤 3.1: 创建 Repository 层

```bash
mkdir -p mcp_agentskills/repositories
touch mcp_agentskills/repositories/{__init__,base,user,skill,token}.py
```

**注意事项**:
- 所有数据库操作使用异步方法
- 使用 `async with` 管理事务

#### 步骤 3.2: 创建 Service 层

```bash
mkdir -p mcp_agentskills/services
touch mcp_agentskills/services/{__init__,auth,user,skill,token,mcp}.py
```

**注意事项**:
- 业务逻辑集中在 Service 层
- Repository 仅负责数据访问

#### 步骤 3.3: 创建 API 路由

```bash
mkdir -p mcp_agentskills/api/v1
mkdir -p mcp_agentskills/api/mcp
touch mcp_agentskills/api/{__init__,deps,router}.py
touch mcp_agentskills/api/v1/{__init__,auth,users,skills,tokens}.py
touch mcp_agentskills/api/mcp/{__init__,auth,http_handler,sse_handler}.py
```

**注意事项**:
- 使用依赖注入获取当前用户
- 统一错误响应格式
- API 版本化（/api/v1/）

### Phase 4: MCP 服务集成（Week 3）

#### 步骤 4.1: 改造 MCP 工具

**改造原则**:
1. 使用 `contextvars` 实现请求级用户隔离（并发安全）
2. 从请求级上下文获取 `user_id`
3. 根据 `user_id` 构建用户隔离的 Skill 路径
4. 保持向后兼容（无 `user_id` 时使用全局路径）

> **重要**: FlowLLM 的 `C` 是全局上下文对象，在多用户并发场景下直接修改 `C.service_config.metadata` 会导致数据混乱。必须使用 `contextvars` 实现请求级隔离。

**改造示例**:

```python
# 改造前
skill_path = skill_dir / skill_name / "SKILL.md"

# 改造后（使用 contextvars，并发安全）
from mcp_agentskills.core.utils.user_context import get_current_user_id

user_id = get_current_user_id()  # 从请求级上下文获取
if user_id:
    skill_path = skill_dir / user_id / skill_name / "SKILL.md"
else:
    skill_path = skill_dir / skill_name / "SKILL.md"
```

**注意事项**:
- 改造所有 4 个 MCP 工具
- 测试向后兼容性
- 更新工具文档
- 确保 MCP 认证中间件正确注入 `user_id` 到上下文

#### 步骤 4.2: 创建 MCP 服务

```bash
touch mcp_agentskills/services/mcp.py
touch mcp_agentskills/api/mcp/{http_handler,sse_handler}.py
```

**注意事项**:
- MCP 服务使用 API Token 认证
- 认证成功后通过 `contextvars` 设置请求级用户上下文
- 支持 HTTP 和 SSE 两种传输模式

### Phase 5: 应用入口与部署（Week 4）

#### 步骤 5.1: 创建 FastAPI 入口

> **重要**: 现有 `main.py`（FlowLLM 入口）保持不变，用于 stdio/SSE 模式。新增 `api_app.py` 用于 HTTP API 模式。

```python
# api_app.py 新建文件
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_agentskills.db.session import init_db
from mcp_agentskills.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # 初始化数据库
    yield

def create_application() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(api_router, prefix="/api/v1")
    return app
```

#### 步骤 5.2: 创建部署配置

```bash
touch Dockerfile docker-compose.yml .dockerignore
```

**注意事项**:
- 使用多阶段构建减小镜像大小
- 敏感信息通过环境变量注入
- 数据卷持久化数据库和 Skill 文件

---

## 3. 关键注意事项

### 3.1 安全注意事项

| 风险 | 防护措施 |
|------|---------|
| 密码泄露 | 使用 bcrypt 哈希，不存储明文 |
| JWT 被破解 | 使用强密钥（>=32字符），设置合理过期时间 |
| API Token 泄露 | 仅创建时显示一次，存储哈希值 |
| 文件上传攻击 | 验证文件类型、限制大小、防止路径遍历 |
| SQL 注入 | 使用 SQLAlchemy ORM，避免原生 SQL |
| CORS 攻击 | 生产环境配置具体允许域名 |

#### 3.1.1 RunShellCommandOp 安全增强

> **重要**: 多用户环境下，`RunShellCommandOp` 存在严重安全风险，需要额外的安全措施。

#### 风险分析

| 风险类型 | 描述 | 严重程度 |
|---------|------|---------|
| 跨用户访问 | 用户 A 可能通过命令访问用户 B 的文件 | 高 |
| 系统命令注入 | 恶意命令可能影响服务器安全 | 高 |
| 资源耗尽 | 恶意脚本可能消耗大量 CPU/内存 | 中 |
| 敏感信息泄露 | 命令可能读取环境变量、配置文件 | 中 |

#### 安全增强方案

**方案一：命令白名单（推荐用于生产环境）**

```python
# core/utils/command_whitelist.py
from typing import Set
import re

ALLOWED_COMMANDS: Set[str] = {
    "python", "python3",
    "node", "npm",
    "bash", "sh",
}

BLOCKED_PATTERNS: list = [
    r"rm\s+-rf",           # 禁止递归删除
    r"sudo",               # 禁止提权
    r">\s*/etc/",          # 禁止修改系统配置
    r"curl.*\|.*bash",     # 禁止远程脚本执行
    r"wget.*\|.*sh",       # 禁止远程脚本执行
    r"\.\./",              # 禁止路径遍历
]

def validate_command(command: str) -> tuple[bool, str]:
    """验证命令是否安全"""
    # 检查命令是否在白名单中
    cmd_parts = command.split()
    if not cmd_parts:
        return False, "Empty command"
    
    base_cmd = cmd_parts[0].split("/")[-1]  # 获取命令名
    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{base_cmd}' is not allowed"
    
    # 检查是否匹配危险模式
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains blocked pattern: {pattern}"
    
    return True, "OK"
```

**方案二：资源限制**

```python
# 在 RunShellCommandOp 中添加资源限制
import resource

def set_resource_limits():
    """设置进程资源限制"""
    # CPU 时间限制：30秒
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    # 内存限制：512MB
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    # 文件大小限制：100MB
    resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))
```

**方案三：沙箱隔离（最安全）**

使用 Docker 容器或 Firecracker microVM 隔离执行环境：

```python
# 使用 Docker 执行命令
import docker

client = docker.from_env()

def run_in_sandbox(skill_dir: Path, command: str, user_id: str) -> str:
    """在 Docker 容器中执行命令"""
    container = client.containers.run(
        image="agentskills-runner:latest",
        command=f"cd /skill && {command}",
        volumes={
            str(skill_dir / user_id): {"bind": "/skill", "mode": "rw"}
        },
        mem_limit="512m",
        cpu_period=100000,
        cpu_quota=50000,  # 50% CPU
        network_disabled=True,  # 禁用网络
        remove=True,
        timeout=60,
    )
    return container.decode("utf-8")
```

#### 推荐配置

| 环境 | 推荐方案 | 说明 |
|------|---------|------|
| 开发环境 | 无限制 | 方便调试 |
| 测试环境 | 命令白名单 | 基本安全 |
| 生产环境 | 命令白名单 + 资源限制 + 沙箱 | 完整安全 |

#### 配置示例

在 `config/settings.py` 中添加安全配置：

```python
class Settings(BaseSettings):
    # ... 其他配置 ...
    
    # 命令安全级别: "disabled" | "whitelist" | "strict"
    # - disabled: 无限制（仅开发环境）
    # - whitelist: 命令白名单（推荐生产环境）
    # - strict: 白名单 + 资源限制 + 沙箱（最高安全）
    COMMAND_SECURITY_LEVEL: str = "whitelist"  # 默认为白名单模式
    
    # 命令执行超时（秒）
    COMMAND_TIMEOUT: int = 60
    
    # 资源限制（仅 strict 模式）
    COMMAND_MAX_MEMORY_MB: int = 512
    COMMAND_MAX_CPU_PERCENT: int = 50
```

在环境变量中配置：

```env
# 生产环境建议配置
COMMAND_SECURITY_LEVEL=strict
COMMAND_TIMEOUT=60
COMMAND_MAX_MEMORY_MB=512
COMMAND_MAX_CPU_PERCENT=50
```

### 3.2 性能注意事项

| 场景 | 优化建议 |
|------|---------|
| 数据库查询 | 使用索引、避免 N+1 查询、使用分页 |
| 文件存储 | 大文件使用对象存储（MinIO/S3） |
| 并发处理 | 使用异步 I/O、连接池 |
| 缓存 | 考虑引入 Redis 缓存热点数据 |

### 3.3 兼容性注意事项

| 场景 | 处理方式 |
|------|---------|
| 现有 Skill 格式 | 完全兼容，无需修改 |
| stdio 传输模式 | 保持支持，无用户隔离 |
| HTTP/SSE 传输模式 | 新增认证，支持用户隔离 |
| 现有配置文件 | 扩展而非替换 |
| 跨平台路径 | 使用 `pathlib.Path` 自动处理 |

---

## 4. 测试策略

### 4.1 测试类型

| 类型 | 覆盖范围 | 工具 |
|------|---------|------|
| 单元测试 | Services, Repositories | pytest |
| 集成测试 | API 端点 | pytest + httpx |
| E2E 测试 | 完整用户流程 | pytest |

### 4.2 测试数据库

```python
# 使用内存 SQLite 进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

### 4.3 测试覆盖率要求

- 单元测试覆盖率 >= 80%
- 核心业务逻辑覆盖率 >= 90%

---

## 5. 部署清单

### 5.1 环境变量检查

```bash
# 必需变量
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=...  # 至少32字符
FLOW_LLM_API_KEY=...

# 可选变量
CORS_ORIGINS=["https://your-domain.com"]
SKILL_STORAGE_PATH=/data/skills
```

### 5.2 数据库准备

```bash
# 创建数据库
createdb agentskills

# 执行迁移
alembic upgrade head
```

### 5.3 文件存储准备

```bash
# 创建 Skill 存储目录
mkdir -p /data/skills
chmod 755 /data/skills
```

### 5.4 服务启动

```bash
# FlowLLM 模式（stdio/SSE，无用户认证）
python -m mcp_agentskills

# FastAPI 开发环境
uvicorn mcp_agentskills.api_app:app --reload

# FastAPI 生产环境
uvicorn mcp_agentskills.api_app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5.5 备份策略

#### 数据库备份

**Linux/macOS:**

```bash
# 手动备份
pg_dump agentskills > backup/agentskills_$(date +%Y%m%d).sql

# 定时备份（crontab）
# 每天凌晨 2 点执行
0 2 * * * pg_dump agentskills > /backup/agentskills_$(date +\%Y\%m\%d).sql

# 保留最近 7 天的备份
find /backup -name "agentskills_*.sql" -mtime +7 -delete
```

**Windows (PowerShell):**

```powershell
# 手动备份
# 注意：请确保 pg_dump.exe 所在目录（如 C:\Program Files\PostgreSQL\16\bin）已添加到系统 PATH
$backupPath = "C:\backup\agentskills_$(Get-Date -Format 'yyyyMMdd').sql"
pg_dump agentskills > $backupPath

# 定时备份（任务计划程序）
# 创建计划任务，每天凌晨 2 点执行以下脚本：
$backupPath = "C:\backup\agentskills_$(Get-Date -Format 'yyyyMMdd').sql"
pg_dump agentskills > $backupPath

# 清理 7 天前的备份
Get-ChildItem "C:\backup\agentskills_*.sql" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
```

#### Skill 文件备份

**Linux/macOS:**

```bash
# 手动备份
tar -czf backup/skills_$(date +%Y%m%d).tar.gz /data/skills

# 定时备份（crontab）
# 每天凌晨 3 点执行
0 3 * * * tar -czf /backup/skills_$(date +\%Y\%m\%d).tar.gz /data/skills

# 保留最近 7 天的备份
find /backup -name "skills_*.tar.gz" -mtime +7 -delete
```

**Windows (PowerShell):**

```powershell
# 手动备份
$backupPath = "C:\backup\skills_$(Get-Date -Format 'yyyyMMdd').zip"
Compress-Archive -Path "C:\data\skills" -DestinationPath $backupPath

# 定时备份（任务计划程序）
# 创建计划任务，每天凌晨 3 点执行以下脚本：
$backupPath = "C:\backup\skills_$(Get-Date -Format 'yyyyMMdd').zip"
Compress-Archive -Path "C:\data\skills" -DestinationPath $backupPath -Force

# 清理 7 天前的备份
Get-ChildItem "C:\backup\skills_*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
```

#### 跨平台备份脚本（推荐）

使用 Python 脚本实现跨平台兼容：

```python
# scripts/backup.py
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def backup_database(backup_dir: Path, db_name: str = "agentskills", keep_days: int = 7):
    """备份数据库"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_file = backup_dir / f"{db_name}_{timestamp}.sql"
    
    # 执行 pg_dump
    with open(backup_file, "w") as f:
        subprocess.run(["pg_dump", db_name], stdout=f, check=True)
    print(f"Database backup created: {backup_file}")
    
    # 清理旧备份
    cleanup_old_backups(backup_dir, f"{db_name}_*.sql", keep_days)

def backup_skills(backup_dir: Path, skills_path: Path, keep_days: int = 7):
    """备份 Skill 文件"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_file = backup_dir / f"skills_{timestamp}"
    
    # 使用 shutil 制作压缩包（跨平台）
    shutil.make_archive(str(backup_file), "zip", skills_path)
    print(f"Skills backup created: {backup_file}.zip")
    
    # 清理旧备份
    cleanup_old_backups(backup_dir, "skills_*.zip", keep_days)

def cleanup_old_backups(backup_dir: Path, pattern: str, keep_days: int):
    """清理旧备份文件"""
    cutoff = datetime.now() - timedelta(days=keep_days)
    for file in backup_dir.glob(pattern):
        if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
            file.unlink()
            print(f"Deleted old backup: {file}")

if __name__ == "__main__":
    backup_dir = Path(os.getenv("BACKUP_DIR", "/backup"))
    skills_path = Path(os.getenv("SKILL_STORAGE_PATH", "/data/skills"))
    
    backup_database(backup_dir)
    backup_skills(backup_dir, skills_path)
```

### 5.6 监控配置

#### 健康检查端点

```python
# api_app.py 添加健康检查
from fastapi import Response
from sqlalchemy import text
import psutil
import shutil


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    # 数据库连接检查
    db_connected = await check_db_connection()
    
    # 磁盘使用率
    disk_usage = shutil.disk_usage("/data/skills")
    disk_percent = disk_usage.used / disk_usage.total * 100
    
    # 内存使用率
    memory = psutil.virtual_memory()
    
    return {
        "db_connected": db_connected,
        "disk_usage_percent": round(disk_percent, 2),
        "memory_usage_percent": memory.percent,
        "cpu_usage_percent": psutil.cpu_percent(),
    }


async def check_db_connection() -> bool:
    try:
        from mcp_agentskills.db.session import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

#### 建议监控项

| 监控项 | 描述 | 告警阈值 |
|--------|------|---------|
| API 响应时间 | P99 响应时间 | > 1s |
| 数据库连接状态 | 连接池健康检查 | 连接失败 |
| 磁盘使用率 | Skill 文件存储 | > 80% |
| 内存使用率 | 应用内存占用 | > 85% |
| 错误率统计 | HTTP 5xx 错误 | > 1% |
| Token 使用量 | API Token 调用频率 | 异常峰值 |

#### Prometheus 集成（可选）

```python
# 安装: pip install prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

## 6. 常见问题

### Q1: 如何处理现有用户的迁移？

**A**: 现有系统没有用户概念，改造后：
- 现有 Skills 可保留在全局目录
- 新用户注册后创建私有目录
- 可提供迁移工具将全局 Skills 复制到用户目录

### Q2: 如何实现 Token 黑名单？

**A**: 可选方案：
1. **Redis 方案**: 存储 revoked token ID，检查时查询
2. **数据库方案**: 添加 revoked_at 字段
3. **短期方案**: 缩短 Token 有效期

### Q3: 如何扩展为分布式部署？

**A**: 需要考虑：
1. **数据库**: 使用托管 PostgreSQL（如 RDS）
2. **文件存储**: 使用对象存储（如 S3）
3. **缓存**: 使用 Redis
4. **负载均衡**: 使用 Nginx 或云负载均衡器

---

## 7. 参考文档

- [project-spec.md](./project-spec.md) - 详细技术规范
- [task_list.md](./task_list.md) - 任务分解
- [checklist.md](./checklist.md) - 验证检查清单
- [tools.md](./tools.md) - MCP 工具文档
- [FlowLLM 文档](https://flowllm-ai.github.io/flowllm/)
- [MCP 协议文档](https://modelcontextprotocol.io/)
