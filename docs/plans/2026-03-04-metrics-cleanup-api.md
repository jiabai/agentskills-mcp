# 调用统计清理接口化方案（补充记录）

## 现状补充记录
已完成请求统计持久化与按天清理的基础实现：新增 request_metrics 表与聚合查询；中间件写入统计并按天执行清理；新增清理仓库方法与测试覆盖；新增 METRICS_RETENTION_DAYS 配置项用于保留周期。这些实现此前未在文档中明确记录，现统一补充在本文件中。

## 目标
将清理逻辑从“隐式后台行为”改为“可配置、可触发的接口”。清理周期仍由配置控制，但需要一个受控 API 触发清理，并支持在请求中覆盖默认保留天数，满足运维与审计场景下的可操作性与可追溯性。落地时移除中间件按天清理逻辑，仅保留接口触发。

## 接口设计
新增接口：`POST /api/v1/dashboard/metrics/cleanup`
- 认证：JWT，且仅允许 is_superuser 用户调用
- 请求体：`retention_days` 可选；为空时使用 `METRICS_RETENTION_DAYS`
- 返回：`removed`、`cutoff`（UTC ISO 时间字符串）、`retention_days`
- 行为：删除 `bucket_start < now - retention_days` 的记录

## 规则与异常处理
- retention_days 校验范围：1–3650
- 非管理员调用返回 403
- 清理失败不影响服务健康，但返回 500 并记录日志

## 测试与验收
- 非管理员访问返回 403
- 管理员可触发清理并返回正确删除数
- retention_days 缺省时使用配置值

## 前端入口设计
- 入口位置：Dashboard 顶部操作区，靠近“创建 Skill / 管理 Token”
- 展示条件：仅管理员可见
- 交互：按钮文案为“清理历史统计”；弹窗输入 retention_days（可选），确认后调用清理接口并提示 removed/cutoff
- 备注：若需要“清零过去 24h 指标”，使用单独的 reset-24h 接口与入口，避免混淆
