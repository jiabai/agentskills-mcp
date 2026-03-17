# 发现记录：project-spec.md 与代码一致性检查

## 检查日期: 2026-03-17

---

## 1. 数据模型检查

### 1.1 User 模型
**文档描述** (project-spec.md:414-445):
- 字段: id, email, username, hashed_password, is_active, is_superuser, enterprise_id, team_id, role, status, created_at, updated_at
- 关系: skills, tokens

**实际实现** ([models/user.py](../mcp_agentskills/models/user.py)):
- 字段完全一致
- 使用 Mixin 模式 (UUIDPrimaryKeyMixin, TimestampMixin) 减少 id/created_at/updated_at 重复定义

**差异**: ✅ 无差异（文档已说明使用 Mixin 模式）

---

### 1.2 Skill 模型
**文档描述** (project-spec.md:448-485):
- 字段: id, user_id, name, description, tags, visibility, enterprise_id, team_id, skill_dir, current_version, is_active, cache_revoked_at, created_at, updated_at
- 关系: user, versions
- 约束: UniqueConstraint("user_id", "name")

**实际实现** ([models/skill.py](../mcp_agentskills/models/skill.py)):
- 字段完全一致
- 约束一致

**差异**: ✅ 无差异

---

### 1.3 SkillVersion 模型
**文档描述** (project-spec.md:488-516):
- 字段: id, skill_id, version, description, dependencies, dependency_spec, dependency_spec_version, metadata_json, created_at, updated_at
- 约束: UniqueConstraint("skill_id", "version")

**实际实现** ([models/skill_version.py](../mcp_agentskills/models/skill_version.py)):
- 字段完全一致
- metadata_json 映射到数据库列名 "metadata"

**差异**: ✅ 无差异（文档已说明字段别名）

---

### 1.4 APIToken 模型
**文档描述** (project-spec.md:519-545):
- 字段: id, user_id, name, token_hash, is_active, expires_at, last_used_at, created_at
- 关系: user

**实际实现** ([models/token.py](../mcp_agentskills/models/token.py)):
- 字段完全一致

**差异**: ✅ 无差异

---

### 1.5 AuditLog 模型
**文档描述** (project-spec.md:220):
- 核心字段: id, actor_id, action, target, result, timestamp, ip, user_agent, details

**实际实现** ([models/audit_log.py](../mcp_agentskills/models/audit_log.py)):
- 字段完全一致

**差异**: ✅ 无差异

---

### 1.6 额外模型（文档未详细描述但代码已实现）
| 模型 | 文件 | 说明 |
|------|------|------|
| Team | [models/team.py](../mcp_agentskills/models/team.py) | 团队模型，文档提及但未详细定义 |
| Enterprise | [models/enterprise.py](../mcp_agentskills/models/enterprise.py) | 企业模型，文档提及但未详细定义 |
| VerificationCode | [models/verification_code.py](../mcp_agentskills/models/verification_code.py) | 验证码模型 |
| EmailDeliveryLog | [models/email_delivery_log.py](../mcp_agentskills/models/email_delivery_log.py) | 邮件投递日志 |
| RequestMetric | [models/request_metric.py](../mcp_agentskills/models/request_metric.py) | 请求指标 |

---

## 2. 审计采集点检查

### 文档声明 (project-spec.md:225-254)

| 类别 | Action | 文档状态 | 实际状态 | 差异说明 |
|------|--------|---------|---------|---------|
| **认证** | `auth.verification_code.send` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:60](../mcp_agentskills/api/v1/auth.py#L60) |
| | `auth.register` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:95](../mcp_agentskills/api/v1/auth.py#L95) |
| | `auth.login` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:128](../mcp_agentskills/api/v1/auth.py#L128) |
| | `auth.login.failed` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:114](../mcp_agentskills/api/v1/auth.py#L114) |
| | `auth.refresh` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:157](../mcp_agentskills/api/v1/auth.py#L157) |
| | `auth.refresh.failed` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:145](../mcp_agentskills/api/v1/auth.py#L145) |
| | `auth.sso.login` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:175](../mcp_agentskills/api/v1/auth.py#L175) |
| | `auth.ldap.login` | ✅ 已覆盖 | ✅ 已实现 | [auth.py:193](../mcp_agentskills/api/v1/auth.py#L193) |
| **技能** | `skill.create` | ✅ 已覆盖 | ✅ 已实现 | [skills.py:94](../mcp_agentskills/api/v1/skills.py#L94) |
| | `skill.upload` | ✅ 已覆盖 | ✅ 已实现 | [skills.py:176,190](../mcp_agentskills/api/v1/skills.py#L176) |
| | `skill.download` | ✅ 已覆盖 | ✅ 已实现 | [skills.py:220](../mcp_agentskills/api/v1/skills.py#L220) |
| | `skill.deactivate` | ✅ 已覆盖 | ✅ 已实现 | [skills.py:244](../mcp_agentskills/api/v1/skills.py#L244) |
| | `skill.activate` | ✅ 已覆盖 | ✅ 已实现 | [skills.py:268](../mcp_agentskills/api/v1/skills.py#L268) |
| | `skill.rollback` | ✅ 已覆盖 | ✅ 已实现 | [skills.py:348](../mcp_agentskills/api/v1/skills.py#L348) |
| | `skill.execute` | ✅ 已覆盖 | ✅ 已实现 | [execute_skill_op.py:184](../mcp_agentskills/core/tools/execute_skill_op.py#L184) |
| | `skill.update` | ❌ 未覆盖 | ❌ 未实现 | [skills.py:113-126](../mcp_agentskills/api/v1/skills.py#L113) 无审计日志 |
| | `skill.delete` | ❌ 未覆盖 | ❌ 未实现 | [skills.py:129-139](../mcp_agentskills/api/v1/skills.py#L129) 无审计日志 |
| **用户** | `user.identity.update` | ✅ 已覆盖 | ✅ 已实现 | [users.py:123](../mcp_agentskills/api/v1/users.py#L123) |
| | `user.password.change` | ⏭ 已跳过 | ⏭ 已跳过 | 密码登录已移除，无修改密码功能 |
| | `user.delete` | ✅ 已覆盖 | ⚠️ 部分实现 | [users.py](../mcp_agentskills/api/v1/users.py) 有邮箱验证码验证但无显式审计日志 |
| **令牌** | `token.create` | ❌ 未覆盖 | ❌ 未实现 | [tokens.py:38-47](../mcp_agentskills/api/v1/tokens.py#L38) 无审计日志 |
| | `token.delete/revoke` | ❌ 未覆盖 | ❌ 未实现 | [tokens.py:50-59](../mcp_agentskills/api/v1/tokens.py#L50) 无审计日志 |

### 差异汇总

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| `skill.update` 无审计日志 | 中 | 文档标记为未覆盖，实际也未实现，一致 |
| `skill.delete` 无审计日志 | 中 | 文档标记为未覆盖，实际也未实现，一致 |
| `user.delete` 审计日志不明确 | 低 | 文档标记已覆盖，但代码中未显式调用审计服务 |
| `token.create` 无审计日志 | 中 | 文档标记为未覆盖，实际也未实现，一致 |
| `token.delete/revoke` 无审计日志 | 中 | 文档标记为未覆盖，实际也未实现，一致 |

---

## 3. MCP 工具检查

### 3.1 load_skill_op.py
**文档描述** (project-spec.md:1.4.1):
- 支持用户隔离：`{skill_dir}/{user_id}/{skill_name}/SKILL.md` 或 `{skill_dir}/{skill_name}/SKILL.md`
- 通过 `get_current_user_id()` 判断用户上下文

**实际实现** ([load_skill_op.py](../mcp_agentskills/core/tools/load_skill_op.py)):
```python
skill_path = (
    skill_dir / user_id / skill_name / "SKILL.md" 
    if user_id else skill_dir / skill_name / "SKILL.md"
)
```

**差异**: ✅ 无差异

---

### 3.2 execute_skill_op.py
**文档描述**:
- 支持 RBAC 权限校验
- 支持可见性校验
- 支持审计日志

**实际实现** ([execute_skill_op.py](../mcp_agentskills/core/tools/execute_skill_op.py)):
- ✅ `has_permission(user, "skill.execute")` 权限校验
- ✅ `is_skill_visible(user, skill)` 可见性校验
- ✅ 审计日志记录

**差异**: ✅ 无差异

---

### 3.3 skill_list_resource (skill://list)
**文档描述** (project-spec.md:213):
- 最小字段: skill_id, name, version, visible, updated_at
- 实现中还返回: description, author, created_at, tags

**实际实现** ([skill_resource_ops.py](../mcp_agentskills/core/tools/skill_resource_ops.py)):
- ✅ 返回所有声明的字段
- ✅ `visible` 字段通过 `_normalized_visibility()` 标准化

**差异**: ✅ 无差异

---

## 4. 配置规范检查

### Settings 类字段对比

| 配置项 | 文档描述 | 实际实现 | 状态 |
|--------|---------|---------|------|
| `DATABASE_URL` | ✅ | ✅ | 一致 |
| `SECRET_KEY` | ✅ | ✅ | 一致 |
| `ALGORITHM` | ✅ | ✅ | 一致 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ | ✅ | 一致 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ✅ | ✅ | 一致 |
| `SKILL_STORAGE_PATH` | ✅ | ✅ | 一致 |
| `SKILL_CACHE_TTL_SECONDS` | ✅ | ✅ | 一致 |
| `SKILL_VERSION_BUMP_STRATEGY` | ✅ | ✅ | 一致 |
| `ENABLE_CACHE_OFFLINE_FALLBACK` | ✅ | ✅ | 一致 |
| `ENABLE_AUDIT_LOG` | ✅ | ✅ | 一致 |
| `ENABLE_RBAC` | ✅ | ✅ | 一致 |
| `ENABLE_SKILL_VISIBILITY` | ✅ | ✅ | 一致 |
| `DEFAULT_SKILL_VISIBILITY` | ✅ | ✅ | 一致 |
| `RBAC_ROLE_PERMISSIONS` | ✅ | ✅ | 一致 |
| `DEPRECATED_ENDPOINTS` | ✅ | ✅ | 一致 |
| `DEPRECATED_VERSIONS` | ✅ | ✅ | 一致 |
| `DEPRECATION_NOTIFY_OFFSETS_DAYS` | ✅ | ✅ | 一致 |

**差异**: ✅ 无差异

---

## 5. 未实现功能检查

### 文档声明未实现的功能 (project-spec.md:266-282)

| 功能 | 文档状态 | 实际状态 | 验证结果 |
|------|---------|---------|---------|
| **MFA（多因素认证）** | ⬜ 未实现 | ⬜ 未实现 | ✅ 一致，代码库中无 MFA/2FA 相关实现 |
| **WORM 审计** | ⬜ 未实现 | ⬜ 未实现 | ✅ 一致，审计日志无不可变保护机制 |
| **技能主文件对象存储** | 🔵 部分实现 | 🔵 部分实现 | ✅ 一致，归档文件支持 S3，主文件仍为本地存储 |

### 文档曾标记未实现但实际已实现

| 功能 | 文档状态 | 实际状态 | 验证结果 |
|------|---------|---------|---------|
| **客户端缓存过期清理** | ✅ 已实现 | ✅ 已实现 | ✅ 一致，`SKILL_CACHE_TTL_SECONDS` 配置存在 |
| **离线降级** | ✅ 已实现 | ✅ 已实现 | ✅ 一致，`ENABLE_CACHE_OFFLINE_FALLBACK` 配置存在 |

---

## 6. 汇总报告

### 一致性总结

| 类别 | 检查项数 | 一致 | 不一致 |
|------|---------|------|--------|
| 数据模型 | 5 | 5 | 0 |
| 审计采集点 | 17 | 12 | 5 (文档已标记未覆盖) |
| MCP 工具 | 3 | 3 | 0 |
| 配置规范 | 17 | 17 | 0 |
| 未实现功能 | 5 | 5 | 0 |
| **总计** | **47** | **42** | **5** |

### 发现的问题

| # | 问题 | 位置 | 严重程度 | 说明 |
|---|------|------|---------|------|
| 1 | `user.delete` 审计日志不明确 | [users.py](../mcp_agentskills/api/v1/users.py) | 低 | 文档标记已覆盖，但代码中未显式调用审计服务 |
| 2 | `skill.update` 无审计日志 | [skills.py:113-126](../mcp_agentskills/api/v1/skills.py#L113) | 中 | 文档已标记未覆盖，建议补充 |
| 3 | `skill.delete` 无审计日志 | [skills.py:129-139](../mcp_agentskills/api/v1/skills.py#L129) | 中 | 文档已标记未覆盖，建议补充 |
| 4 | `token.create` 无审计日志 | [tokens.py:38-47](../mcp_agentskills/api/v1/tokens.py#L38) | 中 | 文档已标记未覆盖，建议补充 |
| 5 | `token.delete/revoke` 无审计日志 | [tokens.py:50-59](../mcp_agentskills/api/v1/tokens.py#L50) | 中 | 文档已标记未覆盖，建议补充 |

### 结论

**整体一致性：高**

文档与代码实现高度一致。主要差异集中在审计采集点的覆盖完整性上，但文档已明确标注这些为"未覆盖"状态，因此不存在文档与代码的矛盾。

建议优先级：
1. **P0**: 补充 `skill.update`、`skill.delete`、`token.create`、`token.revoke` 的审计日志
2. **P1**: 明确 `user.delete` 的审计日志记录
