# AgentSkills MCP 多用户Web服务改造 - 检查清单

> 本文档用于验证项目改造的完整性和正确性，按模块组织。

---

## 如何使用本检查清单

### 使用步骤

1. **按阶段检查**: 按照任务列表（task_list.md）的阶段顺序，完成一个阶段后检查对应模块
2. **逐项勾选**: 完成一项检查后，将 `- [ ]` 改为 `- [x]`
3. **记录问题**: 发现问题时在对应项下方添加备注
4. **统计结果**: 定期更新底部的统计表格

### 状态标记说明

| 标记 | 含义 |
|------|------|
| `- [ ]` | 未检查或未通过 |
| `- [x]` | 已检查且通过 |
| `- [?]` | 需要进一步确认 |

### 统计表格说明

底部的统计表格用于跟踪整体进度：
- **初始状态**: 所有数值为 0/0，表示尚未开始检查
- **检查过程**: 手动更新"通过"和"未通过"数量
- **完成标准**: 所有模块通过率达到 100%

### 与其他文档的关系

| 文档 | 使用时机 |
|------|---------|
| project-spec.md | 检查时参考技术规范 |
| task_list.md | 完成任务后进行对应检查 |
| REFACTORING_GUIDE.md | 遇到问题时参考注意事项 |

---

## 1. 项目配置检查

### 1.1 依赖配置

- [ ] `pyproject.toml` 包含所有必需依赖
  - [ ] FastAPI >= 0.109.0
  - [ ] SQLAlchemy[asyncio] >= 2.0.0
  - [ ] asyncpg >= 0.29.0
  - [ ] python-jose[cryptography]
  - [ ] passlib[bcrypt]
  - [ ] pydantic-settings
  - [ ] python-multipart
  - [ ] flowllm >= 0.2.0.7
  - [ ] alembic
  - [ ] httpx

### 1.2 环境配置

- [ ] `.env.example` 文件存在且包含所有必需变量
  - [ ] DATABASE_URL
  - [ ] SECRET_KEY
  - [ ] ALGORITHM
  - [ ] ACCESS_TOKEN_EXPIRE_MINUTES
  - [ ] REFRESH_TOKEN_EXPIRE_DAYS
  - [ ] DEBUG
  - [ ] CORS_ORIGINS
  - [ ] SKILL_STORAGE_PATH
  - [ ] FLOW_LLM_API_KEY
  - [ ] FLOW_LLM_BASE_URL

### 1.3 Settings 配置

- [ ] `config/settings.py` 正确定义 Settings 类
- [ ] 所有环境变量已映射到 Settings 属性
- [ ] 默认值设置合理
- [ ] 包含 `.env` 文件加载配置

### 1.4 测试环境配置

- [ ] 测试使用独立的测试数据库配置
- [ ] 使用内存 SQLite (`sqlite+aiosqlite:///:memory:`) 进行单元测试
- [ ] 测试配置与生产配置分离（通过环境变量或配置项区分）
- [ ] 确保 SQLite 测试与 PostgreSQL 生产环境的 SQL 语法兼容性

> **说明**: 项目同时支持 PostgreSQL（生产环境）和 SQLite（测试环境）。测试环境使用 SQLite 是为了简化测试执行，无需启动外部数据库服务。详见 [project-spec.md](./project-spec.md) 和 [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md)。

> **兼容性注意事项**:
> - PostgreSQL 和 SQLite 在某些 SQL 语法上有差异，如 `UUID` 类型、`JSON` 操作等
> - 测试时应避免使用 PostgreSQL 特有特性，或使用条件判断兼容两种数据库
> - 如果使用 PostgreSQL 特有特性（如 `uuid-ossp` 扩展），建议在测试环境中使用 `pytest-postgresql` 等工具启动真实 PostgreSQL 实例

---

## 2. 数据库模型检查

### 2.1 User 模型

- [ ] `models/user.py` 文件存在
- [ ] User 类继承自 Base
- [ ] 包含所有必需字段：
  - [ ] id (UUID, 主键)
  - [ ] email (唯一, 索引)
  - [ ] username (唯一, 索引)
  - [ ] hashed_password
  - [ ] is_active
  - [ ] is_superuser
  - [ ] created_at
  - [ ] updated_at
- [ ] 正确定义与 Skill 的关系
- [ ] 正确定义与 APIToken 的关系

### 2.2 Skill 模型

- [ ] `models/skill.py` 文件存在
- [ ] Skill 类继承自 Base
- [ ] 包含所有必需字段：
  - [ ] id (UUID, 主键)
  - [ ] user_id (外键)
  - [ ] name
  - [ ] description
  - [ ] skill_dir
  - [ ] is_active
  - [ ] created_at
  - [ ] updated_at
- [ ] (user_id, name) 唯一约束已定义
- [ ] 正确定义与 User 的关系

### 2.3 APIToken 模型

- [ ] `models/token.py` 文件存在
- [ ] APIToken 类继承自 Base
- [ ] 包含所有必需字段：
  - [ ] id (UUID, 主键)
  - [ ] user_id (外键)
  - [ ] name
  - [ ] token_hash (唯一, 索引)
  - [ ] is_active
  - [ ] expires_at
  - [ ] last_used_at
  - [ ] created_at
- [ ] 正确定义与 User 的关系

### 2.4 数据库迁移

- [ ] Alembic 已正确配置
- [ ] 初始迁移脚本已创建
- [ ] `alembic upgrade head` 执行成功
- [ ] 数据库表结构正确创建

---

## 3. Pydantic Schemas 检查

### 3.1 User Schemas

- [ ] `schemas/user.py` 文件存在
- [ ] UserCreate schema 定义正确
  - [ ] email 验证
  - [ ] username 验证
  - [ ] password 最小长度验证
- [ ] UserUpdate schema 定义正确
- [ ] UserResponse schema 定义正确
- [ ] UserInDB schema 定义正确（包含 hashed_password）

### 3.2 Skill Schemas

- [ ] `schemas/skill.py` 文件存在
- [ ] SkillCreate schema 定义正确
- [ ] SkillUpdate schema 定义正确
- [ ] SkillResponse schema 定义正确
- [ ] SkillListResponse schema 定义正确（分页）

### 3.3 Token Schemas

- [ ] `schemas/token.py` 文件存在
- [ ] TokenCreate schema 定义正确
- [ ] TokenResponse schema 定义正确
  - [ ] token 字段仅在创建时返回
- [ ] TokenListResponse schema 定义正确

### 3.4 通用响应 Schemas

- [ ] `schemas/response.py` 文件存在
- [ ] 通用错误响应格式定义
- [ ] 分页响应格式定义

---

## 4. 安全模块检查

### 4.1 密码安全

- [ ] `core/security/password.py` 文件存在
- [ ] `verify_password()` 函数正确实现
- [ ] `get_password_hash()` 函数正确实现
- [ ] 使用 bcrypt 算法

### 4.2 JWT 认证

- [ ] `core/security/jwt.py` 文件存在
- [ ] `create_access_token()` 函数正确实现
- [ ] `create_refresh_token()` 函数正确实现
- [ ] `decode_token()` 函数正确实现
- [ ] Token 类型区分（access/refresh）

### 4.3 API Token

- [ ] `core/security/token.py` 文件存在
- [ ] `generate_api_token()` 函数正确实现
  - [ ] 格式: `ask_live_{64位hex}`
- [ ] `hash_token()` 函数正确实现
- [ ] `verify_token_hash()` 函数正确实现

---

## 5. Repository 层检查

### 5.1 Base Repository

- [ ] `repositories/base.py` 文件存在
- [ ] 定义通用 CRUD 方法
  - [ ] get()
  - [ ] get_multi()
  - [ ] create()
  - [ ] update()
  - [ ] delete()

### 5.2 User Repository

- [ ] `repositories/user.py` 文件存在
- [ ] `get_by_email()` 方法
- [ ] `get_by_username()` 方法
- [ ] `create()` 方法正确哈希密码

### 5.3 Skill Repository

- [ ] `repositories/skill.py` 文件存在
- [ ] `get_by_user_and_name()` 方法
- [ ] `get_multi_by_user()` 方法（分页）

### 5.4 Token Repository

- [ ] `repositories/token.py` 文件存在
- [ ] `get_by_token_hash()` 方法
- [ ] `get_active_tokens_by_user()` 方法
- [ ] `update_last_used()` 方法

---

## 6. Service 层检查

### 6.1 Auth Service

- [ ] `services/auth.py` 文件存在
- [ ] `register()` 方法
  - [ ] 检查邮箱唯一性
  - [ ] 检查用户名唯一性
  - [ ] 哈希密码
- [ ] `login()` 方法
  - [ ] 验证邮箱存在
  - [ ] 验证密码正确
  - [ ] 生成 JWT Token
- [ ] `refresh_token()` 方法
- [ ] `logout()` 方法（可选）

### 6.2 User Service

- [ ] `services/user.py` 文件存在
- [ ] `get_current_user()` 方法
- [ ] `update_user()` 方法
- [ ] `delete_user()` 方法
  - [ ] 验证密码
  - [ ] 删除关联数据
- [ ] `change_password()` 方法

### 6.3 Token Service

- [ ] `services/token.py` 文件存在
- [ ] `create_token()` 方法
  - [ ] 生成 Token
  - [ ] 存储哈希值
  - [ ] 返回明文 Token（仅一次）
- [ ] `list_tokens()` 方法
- [ ] `revoke_token()` 方法
- [ ] `validate_token()` 方法

### 6.4 Skill Service

- [ ] `services/skill.py` 文件存在
- [ ] `create_skill()` 方法
- [ ] `get_skill()` 方法
- [ ] `list_skills()` 方法（分页）
- [ ] `update_skill()` 方法
- [ ] `delete_skill()` 方法
- [ ] `upload_files()` 方法
- [ ] `list_files()` 方法

---

## 7. API 接口检查

### 7.1 认证接口

- [ ] POST `/api/v1/auth/register`
  - [ ] 返回 201 Created
  - [ ] 返回用户信息（不含密码）
  - [ ] 邮箱重复返回 409
- [ ] POST `/api/v1/auth/login`
  - [ ] 返回 access_token 和 refresh_token
  - [ ] 错误凭据返回 401
- [ ] POST `/api/v1/auth/refresh`
  - [ ] 验证 refresh_token
  - [ ] 返回新 access_token

### 7.2 用户接口

- [ ] GET `/api/v1/users/me`
  - [ ] 需要 JWT 认证
  - [ ] 返回当前用户信息
- [ ] PUT `/api/v1/users/me`
  - [ ] 更新用户信息
- [ ] DELETE `/api/v1/users/me`
  - [ ] 需要密码确认
  - [ ] 删除用户及关联数据
- [ ] PUT `/api/v1/users/me/password`
  - [ ] 验证旧密码
  - [ ] 更新新密码

### 7.3 Token 接口

- [ ] GET `/api/v1/tokens`
  - [ ] 返回 Token 列表（不含明文 Token）
- [ ] POST `/api/v1/tokens`
  - [ ] 返回明文 Token（仅此一次）
  - [ ] 支持设置过期时间
- [ ] DELETE `/api/v1/tokens/{token_id}`
  - [ ] 撤销 Token

### 7.4 Skill 接口

- [ ] GET `/api/v1/skills`
  - [ ] 支持分页
  - [ ] 支持搜索
- [ ] POST `/api/v1/skills`
  - [ ] 创建 Skill 目录
- [ ] GET `/api/v1/skills/{skill_id}`
  - [ ] 返回 Skill 详情
- [ ] PUT `/api/v1/skills/{skill_id}`
  - [ ] 更新 Skill 信息
- [ ] DELETE `/api/v1/skills/{skill_id}`
  - [ ] 删除 Skill 及文件
- [ ] POST `/api/v1/skills/upload`
  - [ ] 支持 multipart 上传
  - [ ] 文件大小限制
  - [ ] 文件类型验证
- [ ] GET `/api/v1/skills/{skill_id}/files`
  - [ ] 返回文件列表

### 7.5 MCP 接口

- [ ] POST `/mcp`
  - [ ] 需要 API Token 认证
  - [ ] 支持 MCP 协议
  - [ ] 用户隔离正确
- [ ] GET `/sse`
  - [ ] 需要 API Token 认证
  - [ ] SSE 连接正确
  - [ ] 用户隔离正确

---

## 8. MCP 工具改造检查

### 8.1 LoadSkillOp

- [ ] 支持从上下文获取 user_id
- [ ] 根据 user_id 构建正确路径
- [ ] 向后兼容（无 user_id 时使用全局路径）
- [ ] 错误处理正确

### 8.2 LoadSkillMetadataOp

- [ ] 支持从上下文获取 user_id
- [ ] 仅搜索用户私有目录
- [ ] 向后兼容
- [ ] 空目录处理正确

### 8.3 ReadReferenceFileOp

- [ ] 支持从上下文获取 user_id
- [ ] 正确构建文件路径
- [ ] 向后兼容
- [ ] 文件不存在处理正确

### 8.4 RunShellCommandOp

- [ ] 支持从上下文获取 user_id
- [ ] 在正确目录执行命令
- [ ] 向后兼容
- [ ] 安全限制正确

---

## 9. 中间件检查

### 9.1 JWT 认证中间件

- [ ] `core/middleware/auth.py` 文件存在
- [ ] `get_current_user()` 依赖正确
- [ ] `get_current_active_user()` 依赖正确
- [ ] Token 过期处理正确
- [ ] 用户不存在处理正确
- [ ] 用户禁用处理正确

### 9.2 MCP Token 认证

- [ ] `api/mcp/auth.py` 文件存在
- [ ] Token 验证正确
- [ ] Token 过期检查
- [ ] Token 撤销检查
- [ ] 更新 last_used_at

---

## 10. 文件存储检查

### 10.1 Skill 存储工具

- [ ] `core/utils/skill_storage.py` 文件存在
- [ ] `get_user_skill_dir()` 方法
- [ ] `create_skill_dir()` 方法
- [ ] `delete_skill_dir()` 方法
- [ ] `save_file()` 方法
- [ ] `list_files()` 方法
- [ ] `skill_exists()` 方法

### 10.2 存储路径

- [ ] 用户隔离目录结构正确
- [ ] 路径格式: `/data/skills/{user_id}/{skill_name}/`
- [ ] 目录权限正确

---

## 11. FastAPI 应用检查

### 11.1 应用入口

- [ ] `api_app.py` 文件存在
- [ ] `create_application()` 工厂函数
- [ ] CORS 中间件配置
- [ ] 路由注册正确
- [ ] 生命周期管理（数据库初始化）

### 11.2 健康检查

- [ ] GET `/health` 端点存在
  - [ ] 返回服务状态 `{"status": "healthy"}`
- [ ] GET `/metrics` 端点存在（可选）
  - [ ] 返回数据库连接状态
  - [ ] 返回磁盘使用率
  - [ ] 返回内存使用率
  - [ ] 返回 CPU 使用率

### 11.3 API 文档

- [ ] GET `/docs` Swagger UI 可访问
- [ ] GET `/redoc` ReDoc 可访问
- [ ] OpenAPI schema 正确

---

## 12. 部署配置检查

### 12.1 Docker

- [ ] `Dockerfile` 文件存在
- [ ] 基础镜像正确（Python 3.11+）
- [ ] 依赖安装正确
- [ ] 工作目录正确
- [ ] 暴露端口正确
- [ ] 启动命令正确

### 12.2 Docker Compose

- [ ] `docker-compose.yml` 文件存在
- [ ] API 服务配置正确
- [ ] PostgreSQL 服务配置正确
- [ ] 数据卷配置正确
- [ ] 网络配置正确
- [ ] 环境变量传递正确

### 12.3 启动脚本

- [ ] 启动命令可用
- [ ] 数据库迁移自动执行
- [ ] 错误处理正确

---

## 13. 测试检查

### 13.1 测试配置

- [ ] `tests/conftest.py` 文件存在
- [ ] 测试数据库配置正确（内存 SQLite）
- [ ] 测试客户端 fixture 正确
- [ ] 测试用户 fixture 正确

### 13.2 单元测试

- [ ] 密码工具测试通过
- [ ] JWT 工具测试通过
- [ ] Token 工具测试通过
- [ ] 认证服务测试通过
- [ ] 用户服务测试通过
- [ ] Skill 服务测试通过

### 13.3 集成测试

- [ ] 认证 API 测试通过
- [ ] 用户 API 测试通过
- [ ] Token API 测试通过
- [ ] Skill API 测试通过
- [ ] MCP API 测试通过

### 13.4 测试覆盖率

- [ ] 单元测试覆盖率 >= 80%
- [ ] 核心业务逻辑覆盖率 >= 90%

---

## 14. 安全检查

### 14.1 密码安全

- [ ] 密码使用 bcrypt 哈希
- [ ] 密码最小长度 >= 8
- [ ] 密码不在响应中返回

### 14.2 Token 安全

- [ ] API Token 仅在创建时返回一次
- [ ] 存储 SHA256 哈希值
- [ ] 支持过期时间
- [ ] 支持撤销

### 14.3 文件上传安全

- [ ] 文件类型验证
- [ ] 单文件大小限制
- [ ] 总上传大小限制
- [ ] 路径遍历防护

### 14.4 API 安全

- [ ] 所有用户 API 需要 JWT 认证
- [ ] MCP API 需要 API Token 认证
- [ ] 敏感操作需要密码确认
- [ ] CORS 配置正确

---

## 15. 文档检查

### 15.1 API 文档

- [ ] OpenAPI schema 完整
- [ ] 所有端点有描述
- [ ] 所有参数有描述
- [ ] 所有响应有描述

### 15.2 项目文档

- [ ] README 更新
- [ ] 环境变量说明
- [ ] 部署说明
- [ ] 使用示例

---

## 检查结果汇总

### 统计表格更新方法

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

可以使用以下 Python 脚本自动统计检查清单进度：

```python
#!/usr/bin/env python3
"""自动统计 checklist.md 中的检查项进度"""

import re
from pathlib import Path

def count_checklist_items(content: str) -> dict:
    """统计检查清单中的项目数"""
    # 匹配模块标题
    module_pattern = r'##\s+\d+\.\s+(.+?)\n'
    modules = re.findall(module_pattern, content)
    
    stats = []
    total_checked = 0
    total_unchecked = 0
    
    # 按模块分割内容
    sections = re.split(r'##\s+\d+\.\s+', content)[1:]
    
    for i, section in enumerate(sections):
        lines = section.split('\n')
        module_name = modules[i] if i < len(modules) else f"模块{i+1}"
        
        checked = len(re.findall(r'- \[x\]', section, re.IGNORECASE))
        unchecked = len(re.findall(r'- \[ \]', section))
        total = checked + unchecked
        
        if total > 0:
            percentage = round(checked / total * 100, 1)
            stats.append({
                'name': module_name,
                'total': total,
                'checked': checked,
                'unchecked': unchecked,
                'percentage': percentage
            })
            total_checked += checked
            total_unchecked += unchecked
    
    return {
        'modules': stats,
        'total_checked': total_checked,
        'total_unchecked': total_unchecked,
        'total': total_checked + total_unchecked,
        'overall_percentage': round(total_checked / (total_checked + total_unchecked) * 100, 1) if (total_checked + total_unchecked) > 0 else 0
    }

def print_stats(stats: dict):
    """打印统计结果"""
    print("\n" + "="*80)
    print("检查清单进度统计".center(80))
    print("="*80)
    print(f"\n{'模块':<30} {'总项':>8} {'通过':>8} {'未通过':>8} {'通过率':>10}")
    print("-"*80)
    
    for module in stats['modules']:
        print(f"{module['name']:<30} {module['total']:>8} {module['checked']:>8} {module['unchecked']:>8} {module['percentage']:>9}%")
    
    print("-"*80)
    print(f"{'总计':<30} {stats['total']:>8} {stats['total_checked']:>8} {stats['total_unchecked']:>8} {stats['overall_percentage']:>9}%")
    print("="*80)
    
    if stats['overall_percentage'] == 100:
        print("\n🎉 所有检查项已通过！")
    elif stats['overall_percentage'] >= 80:
        print(f"\n✅ 进度良好，还剩 {stats['total_unchecked']} 项待完成")
    else:
        print(f"\n⚠️  进度较慢，还有 {stats['total_unchecked']} 项待完成")

if __name__ == "__main__":
    checklist_path = Path("docs/checklist.md")
    if not checklist_path.exists():
        print(f"错误: 找不到文件 {checklist_path}")
        exit(1)
    
    content = checklist_path.read_text(encoding='utf-8')
    stats = count_checklist_items(content)
    print_stats(stats)
```

使用方法：
```bash
python scripts/checklist_stats.py
```

### 初始状态（模板）

> **重要说明**:
> - 以下表格是**静态模板**，显示初始状态（所有模块未开始检查）
> - 表格不会自动更新，需要**手动更新**或**运行统计脚本**生成最新结果
> - 推荐使用下方的 Python 脚本自动生成实时统计结果

| 模块 | 总项 | 通过 | 未通过 | 通过率 |
|------|------|------|--------|--------|
| 1. 项目配置 | - | - | - | - |
| 2. 数据库模型 | - | - | - | - |
| 3. Pydantic Schemas | - | - | - | - |
| 4. 安全模块 | - | - | - | - |
| 5. Repository 层 | - | - | - | - |
| 6. Service 层 | - | - | - | - |
| 7. API 接口 | - | - | - | - |
| 8. MCP 工具改造 | - | - | - | - |
| 9. 中间件 | - | - | - | - |
| 10. 文件存储 | - | - | - | - |
| 11. FastAPI 应用 | - | - | - | - |
| 12. 部署配置 | - | - | - | - |
| 13. 测试 | - | - | - | - |
| 14. 安全 | - | - | - | - |
| 15. 文档 | - | - | - | - |
| **总计** | **-** | **-** | **-** | **-** |

> **💡 提示**: 运行 `python scripts/checklist_stats.py` 可自动生成包含实际数据的统计表格。

---

## 验收标准

项目改造完成需满足以下条件：

1. **功能完整性**: 所有检查项 100% 通过
2. **测试覆盖率**: 单元测试 >= 80%，核心逻辑 >= 90%
3. **安全合规**: 所有安全检查项通过
4. **文档完整**: API 文档和项目文档完整
5. **部署就绪**: Docker 部署配置完整可用
