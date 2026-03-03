# 登录优先访问流程 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 访问控制台时未登录先进入登录页，避免未认证调用触发前端错误，并将流程写入文档。

**Architecture:** 前端在 App Shell 层进行鉴权门控，检测本地 token；未登录用户被重定向到 `/login`，登录/注册页保持可访问。文档先明确流程，再按流程修复与验证。

**Tech Stack:** Next.js App Router, React, Vitest, FastAPI

---

### Task 1: 更新文档说明登录优先流程

**Files:**
- Modify: `D:/Github/agentskills-mcp/docs/project-spec.md`

**Step 1: 写入流程说明**

在“前端控制台”段落补充访问流程与鉴权要求，明确：
- 未登录访问任意控制台页面时自动进入 `/login`
- 登录/注册页无需鉴权
- 登录成功后再进入 Dashboard/Skills/Profile/Security 等页面

**Step 2: 验证文档内容**

Run: `python -m pip --version`  
Expected: Command succeeds with version output.

**Step 3: Skip commit**

No commit unless user requests.

---

### Task 2: 复现未登录直接进入控制台导致的错误

**Files:**
- Inspect: `D:/Github/agentskills-mcp/frontend/src/components/app/app-shell.tsx`
- Inspect: `D:/Github/agentskills-mcp/frontend/src/lib/api.ts`
- Inspect: `D:/Github/agentskills-mcp/frontend/src/app/profile/page.tsx`

**Step 1: 记录复现步骤**

- 清空 localStorage 中 `agentskills.tokens`
- 直接访问 `/profile`
- 记录错误堆栈与请求返回状态

**Step 2: 验证鉴权缺失位置**

确认页面加载前是否存在路由级鉴权或 App Shell 鉴权。

**Step 3: Skip commit**

No commit unless user requests.

---

### Task 3: 添加前端鉴权门控并验证

**Files:**
- Modify: `D:/Github/agentskills-mcp/frontend/src/components/app/app-shell.tsx`
- Modify: `D:/Github/agentskills-mcp/frontend/src/lib/api.ts` (only if needed by guard)
- Test: `D:/Github/agentskills-mcp/frontend/src/__tests__/app-shell-auth.test.tsx`

**Step 1: 写失败测试**

```ts
import { describe, it, expect, vi } from "vitest"
import { render } from "@testing-library/react"

import { AppShell } from "@/components/app/app-shell"

vi.mock("next/navigation", () => ({
  usePathname: () => "/profile"
}))

describe("AppShell auth guard", () => {
  it("redirects to login when not authenticated", () => {
    const assign = vi.fn()
    Object.defineProperty(window, "location", {
      value: { href: "", assign },
      writable: true
    })
    window.localStorage.removeItem("agentskills.tokens")
    render(<AppShell>content</AppShell>)
    expect(assign).toHaveBeenCalledWith("/login")
  })
})
```

**Step 2: 运行测试并确认失败**

Run: `npm run test -- --run frontend/src/__tests__/app-shell-auth.test.tsx`  
Expected: FAIL because redirect not implemented.

**Step 3: 实现最小鉴权门控**

在 AppShell 中增加客户端鉴权检测：
- 非 `/login` 与 `/register` 页面，且本地没有 token 时，重定向到 `/login`
- 保持现有布局逻辑

**Step 4: 运行测试并确认通过**

Run: `npm run test -- --run frontend/src/__tests__/app-shell-auth.test.tsx`  
Expected: PASS.

**Step 5: 运行 lint**

Run: `npm run lint` (cwd: `frontend`)  
Expected: PASS.

**Step 6: Skip commit**

No commit unless user requests.
