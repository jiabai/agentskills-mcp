# 公网版 vs 私有化版：配置矩阵与功能开关清单

本文档给出一套代码下的公网版与企业私有化版配置矩阵与功能开关建议，用于指导部署与产品能力收敛。配置项名称为建议命名，可按实际 Settings 结构调整。

> 口径说明：本文“公网版默认/私有化版默认”指部署推荐默认组合，不等同于 `Settings` 内建默认值。代码层默认值以 `mcp_agentskills/config/settings.py` 为准，私有化能力请通过环境变量显式开启。

## 配置矩阵

| 领域 | 公网版（默认） | 私有化版（默认） | 说明 |
|------|----------------|-----------------|------|
| 账户注册 | 开放注册 | 关闭注册 | 私有化版通常仅企业身份源接入 |
| 认证入口 | 邮箱验证码/JWT | SSO/LDAP + JWT | 私有化版以企业身份源为主 |
| 组织模型 | 可选 | 必需 | 私有化版需组织/团队映射 |
| 权限控制 | 基础权限 | RBAC 全量 | 私有化版需细粒度可见性 |
| 审计日志 | 基础日志 | 采集 + 查询 + 导出 | 私有化版需合规审计 |
| 技能可见性 | 个人 | 企业/团队/个人 | 私有化版需多级可见性 |
| 版本策略 | 手动指定 | 自动递增 | 私有化版需避免版本冲突 |
| MCP 接入 | 公网地址 | 内网/VPC | 私有化版常内网部署 |
| 运行隔离 | 基础限制 | 沙箱 + 资源配额 | 私有化版建议更严格 |
| 数据存储 | 公共云对象存储 | 私有化 MinIO/S3 | 私有化版需内网可控 |
| 邮件服务 | SMTP/第三方 | 企业邮件网关 | 私有化版对接企业邮件 |
| 监控告警 | 基础指标 | 指标 + 告警 | 私有化版需对接企业监控 |
| 备份策略 | 轻量备份 | 定期全量 + 增量 | 私有化版需灾备策略 |

## 功能开关清单

| 开关 | 作用 | 公网版推荐 | 私有化版推荐 | 关联模块 |
|------|------|-------------|---------------|----------|
| ENABLE_PUBLIC_SIGNUP | 是否允许公开注册 | true | false | 认证/用户 |
| ENABLE_EMAIL_OTP_LOGIN | 是否启用邮箱验证码登录 | true | 可选 | 认证/邮件 |
| ENABLE_SSO | 是否启用企业 SSO | false | true | 认证/企业目录 |
| ENABLE_LDAP | 是否启用 LDAP/AD | false | true | 认证/企业目录 |
| ENABLE_ORG_MODEL | 是否启用组织/团队模型 | false | true | 用户/组织 |
| ENABLE_RBAC | 是否启用 RBAC 权限 | false | true | 权限/可见性 |
| ENABLE_SKILL_VISIBILITY | 是否启用企业/团队/个人可见性 | false | true | 技能/权限 |
| ENABLE_AUDIT_LOG | 是否启用审计日志 | false | true | 审计/合规 |
| ENABLE_AUDIT_EXPORT | 是否允许审计导出 | false | true | 审计/合规 |
| ENABLE_SKILL_DOWNLOAD_ENCRYPTION | 技能下载加密传输 | 可选 | true | 技能/安全 |
| ENABLE_LOCAL_CACHE_ENCRYPTION | 客户端缓存加密 | 可选 | true | 缓存/安全 |
| ENABLE_CACHE_OFFLINE_FALLBACK | 远端不可用时启用本地缓存回退 | 可选 | true | 缓存/可用性 |
| ENABLE_SANDBOX_EXECUTION | 技能执行沙箱 | 可选 | true | 运行隔离 |
| ENABLE_RESOURCE_QUOTA | CPU/内存/磁盘配额 | 可选 | true | 运行隔离 |
| ENABLE_NETWORK_EGRESS_CONTROL | 外网访问控制 | 可选 | true | 运行隔离 |
| ENABLE_RATE_LIMIT | API 限流 | true | true | API 网关 |
| ENABLE_METRICS | 指标采集 | true | true | 监控 |

## 部署建议

- 公网版：开放注册 + 基础权限 + 轻量审计，突出可用性与增长
- 私有化版：SSO/LDAP + RBAC + 审计全量，突出安全与合规
- 统一代码：通过环境变量与配置中心启用不同能力组合
