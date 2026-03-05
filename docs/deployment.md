# 部署指南

本文档提供 AgentSkills MCP 的本地开发与生产部署说明，涵盖 FastAPI 模式与 FlowLLM 模式。

## 部署模式

### FastAPI 模式（HTTP API + MCP）
- 适用：多用户 Web API、MCP HTTP/SSE 访问
- 入口：`mcp_agentskills.api_app:app`
- MCP 端点：`/mcp`、`/sse`

### FlowLLM 模式（stdio/SSE）
- 适用：本地单用户、CLI 集成
- 入口：`mcp_agentskills.main`

## 前置条件

- Python 3.10+
- PostgreSQL 14+（生产环境）
- Node.js 18+（前端控制台）
- 可选：Docker / Docker Compose

## 环境变量配置

复制 `.env.example` 并按需修改：

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentskills
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/agentskills/app.log
SKILL_STORAGE_PATH=/data/skills
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
FLOW_LLM_API_KEY=your-api-key
FLOW_LLM_BASE_URL=https://api.openai.com/v1
POSTGRES_USER=agentskills
POSTGRES_PASSWORD=agentskills
POSTGRES_DB=agentskills
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=your-sender@example.com
SMTP_USE_TLS=true
ALIYUN_DM_ACCESS_KEY_ID=your-aliyun-access-key-id
ALIYUN_DM_ACCESS_KEY_SECRET=your-aliyun-access-key-secret
ALIYUN_DM_ACCOUNT_NAME=sender@your-domain.com
ALIYUN_DM_FROM_ALIAS=AgentSkills
ALIYUN_DM_REPLY_TO_ADDRESS=true
ALIYUN_DM_ENDPOINT=https://dm.aliyuncs.com/
```

## 邮件与验证码运行要求

### 发送通道策略
- DEBUG=true：使用 SMTP 备选方案（自建邮箱/业务邮箱）
- DEBUG=false：使用阿里云邮件推送服务

### 异步任务与持久化
- 邮件发送建议通过任务队列或后台任务执行，避免阻塞 API 请求
- 生产环境验证码存储建议使用 Redis 或数据库，保证多实例与重启一致性

### 模板与内容管理
- 模板需包含验证码、有效期与重发间隔提示
- 建议提供中英模板与品牌文案配置

### 监控与审计
- 监控投递成功率、失败原因分布与重试次数
- 发送失败需触发告警并写入审计日志

## 本地开发部署

### 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. 启动 FastAPI 服务

```bash
uvicorn mcp_agentskills.api_app:app --host 0.0.0.0 --port 8000
```

### 3. 启动前端控制台

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 生产部署（Docker Compose，Ubuntu）

### 1. 准备环境变量

- 生产环境必须设置 `SECRET_KEY`、`CORS_ORIGINS`，且 `DEBUG=false`
- `.env` 用于存放敏感信息与生产配置

### 2. 启动服务（包含迁移）

```bash
docker compose --env-file .env up -d --build
```

`migrate` 服务会在 `db` 就绪后执行迁移并退出，`api` 会在迁移完成后启动。

### 3. 单独执行迁移（可选）

```bash
docker compose run --rm migrate
```

## 运行 FlowLLM 模式（可选）

```bash
agentskills-mcp
```

## 健康检查

```bash
GET /health
```

返回示例：

```json
{
  "status": "healthy",
  "db_connected": true
}
```

## MCP 接入示例

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

## 常见问题

### 1. CORS 报错
- 生产环境必须显式设置 `CORS_ORIGINS`，且不能包含 `*`

### 2. MCP 认证失败
- 确认 `Authorization` 头使用 `Bearer ask_live_xxx...`
- 确认 Token 未过期或撤销
