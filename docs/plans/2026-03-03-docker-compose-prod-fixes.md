# Docker Compose Production Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden docker-compose deployment for production reliability and security.

**Architecture:** Split database migration into a one-off service, add health checks and restart policies, and externalize sensitive configuration to environment files. Keep application runtime unchanged while improving orchestration reliability.

**Tech Stack:** Docker Compose, Postgres, FastAPI (uvicorn), Alembic

---

### Task 1: Update docker-compose for production reliability

**Files:**
- Modify: `D:/Github/agentskills-mcp/docker-compose.yml`

**Step 1: Adjust database service healthcheck and restart policy**

```yaml
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: agentskills
      POSTGRES_PASSWORD: agentskills
      POSTGRES_DB: agentskills
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentskills -d agentskills"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped
```

**Step 2: Add one-off migrate service**

```yaml
  migrate:
    build: .
    command: sh -c "alembic upgrade head"
    environment:
      DATABASE_URL: postgresql+asyncpg://agentskills:agentskills@db:5432/agentskills
    depends_on:
      db:
        condition: service_healthy
    restart: "no"
```

**Step 3: Harden api service**

```yaml
  api:
    build: .
    command: sh -c "uvicorn mcp_agentskills.api_app:app --host 0.0.0.0 --port 8000"
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://agentskills:agentskills@db:5432/agentskills
      DEBUG: "false"
      LOG_FILE: ""
      SKILL_STORAGE_PATH: /data/skills
    volumes:
      - skills:/data/skills
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    restart: unless-stopped
```

**Step 4: Run config validation**

Run: `docker compose config`
Expected: Successful render of merged config with no errors.

**Step 5: Skip commit**

No commit per user instruction.

---

### Task 2: Align deployment documentation with production compose changes

**Files:**
- Modify: `D:/Github/agentskills-mcp/docs/deployment.md`

**Step 1: Update production deployment section**

Add or revise to note:
- migrations run via `migrate` service
- `.env` used for secrets in production
- `DEBUG=false` required

**Step 2: Validate docs**

Run: `python -m pip --version`
Expected: Command succeeds; no repository changes beyond docs.

**Step 3: Skip commit**

No commit per user instruction.
