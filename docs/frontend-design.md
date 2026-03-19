# AgentSkills MCP 前端构建与设计文档

> 本文档描述 AgentSkills MCP 多用户控制台的前端架构、设计规范与实现细节，并基于当前仓库代码进行一致性校准。

---

## 目录

1. [文档状态与审阅结论](#1-文档状态与审阅结论)
2. [技术栈概览](#2-技术栈概览)
3. [设计系统](#3-设计系统)
4. [组件架构](#4-组件架构)
5. [页面结构](#5-页面结构)
6. [状态管理与数据流](#6-状态管理与数据流)
7. [认证与安全](#7-认证与安全)
8. [主题系统](#8-主题系统)
9. [API 集成](#9-api-集成)
10. [开发规范](#10-开发规范)
11. [部署配置](#11-部署配置)
12. [当前差异与修复优先级](#12-当前差异与修复优先级)
13. [待实现功能详细指导](#13-待实现功能详细指导)

---

## 1. 文档状态与审阅结论

### 1.1 审阅基线

本轮审阅基于以下内容：

- `docs/project-spec.md`（契约与目标）
- `frontend/src/**`（当前前端实现）
- `mcp_agentskills/api/v1/**` 与 `mcp_agentskills/schemas/**`（后端接口契约）

### 1.2 结论

`frontend-design.md` 已完成本轮修订，主要变更：

1. **类型定义对齐后端实际**：
   - `Skill` 类型：补齐 `visible`、`is_active`、`current_version`、`enterprise_id`、`team_id`、`skill_dir`、`cache_revoked_at` 字段
   - `Token` 类型：补齐 `is_active`、`last_used_at` 字段，移除不存在的 `revoked_at`
   - `User` 类型：补齐 `is_active`、`enterprise_id`、`team_id`、`role`、`status`、`created_at`、`updated_at` 字段
   - `SkillVersion` 类型：对齐后端 `SkillVersionResponse`，移除不存在的 `id`、`skill_id`、`updated_at`
   - `SkillVersionDiff` 类型：改为结构化响应（`added`/`removed`/`modified`），而非字符串 `diff`
   - `SkillInstallInstructions` 类型：对齐后端响应结构（`strategy`/`commands`/`requirements_text` 等）
   - `SkillDownloadResponse` 类型：对齐后端响应（`encrypted_code`/`checksum`/`expires_at`）
   - 新增 `VerificationCodeResponse`、`SkillCachePolicyResponse`、`SSOLoginRequest`、`LDAPLoginRequest`、`UserIdentityUpdate` 类型

2. **API 客户端扩展**：
   - 补充 SSO/LDAP 登录接口
   - 补充版本管理（versions/diff/rollback/install-instructions）、状态管理（activate/deactivate）
   - 补充用户管理（requestDeleteAccount/bindEmail/updateUserIdentity）
   - 补充缓存策略查询（getSkillCachePolicy）
   - 补充指标管理（cleanupMetrics/resetMetrics24h）

3. **前后端契约映射更新**：
   - 新增"前端当前实现差异"表格，明确标注前端实际代码与文档规范的差异
   - 标注 P0 级问题：安全页账户删除使用密码模式（应改为验证码模式）、修改密码功能调用不存在的 API

4. **版本对比 UI 重构**：
   - 更新版本对比对话框，展示结构化差异（新增/删除/修改文件列表）
   - 更新安装说明对话框，展示策略、命令、依赖文件等

**待前端实现的能力**（参见第 13 章详细说明）：
- 安全页账户删除流程（验证码模式）- P0
- 移除不存在的修改密码功能 - P0
- Skill 版本管理标签页 - P1
- Skill 激活/停用状态切换 - P1
- 邮箱绑定功能入口 - P1
- SSO/LDAP 登录支持（按配置启用）- P2

### 1.3 本次修订目标

- 对齐当前代码真实实现，避免“文档正确但代码不一致”
- 明确与 `project-spec.md` 的契约边界
- 增加可执行的差异修复优先级，供后续前端迭代使用

---

## 2. 技术栈概览

### 2.1 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.2.15 | React 全栈框架（App Router） |
| React | 18.3.1 | UI 组件库 |
| TypeScript | 5.6.3 | 类型安全 |

### 2.2 样式系统

| 技术 | 版本 | 用途 |
|------|------|------|
| Tailwind CSS | 3.4.14 | 原子化 CSS 框架 |
| shadcn/ui | - | 基于 Radix UI 的组件库 |
| class-variance-authority | 0.7.0 | 组件变体管理 |
| clsx + tailwind-merge | - | 类名合并工具 |

### 2.3 UI 原语与工具

| 技术 | 版本 | 用途 |
|------|------|------|
| @radix-ui/react-* | ^1.0.x | 无障碍 UI 原语 |
| lucide-react | 0.452.0 | 图标库 |
| next-themes | 0.3.0 | 主题切换 |

### 2.4 测试工具

| 技术 | 版本 | 用途 |
|------|------|------|
| Vitest | 2.1.3 | 测试运行器 |
| @testing-library/react | 16.0.1 | React 测试工具 |
| jsdom | 25.0.1 | DOM 模拟环境 |

---

## 3. 设计系统

### 3.1 字体系统

项目采用双字体系统，通过 Next.js 字体优化自动加载：

```typescript
// src/app/layout.tsx
import { Fraunces, IBM_Plex_Sans } from "next/font/google"

const displayFont = Fraunces({
  subsets: ["latin"],
  variable: "--font-display"
})

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-body"
})
```

| 字体角色 | 字体名称 | CSS 变量 | 用途 |
|---------|---------|---------|------|
| Display | Fraunces | `--font-display` | 标题、品牌文字 |
| Body | IBM Plex Sans | `--font-body` | 正文、UI 元素 |

**设计理念**：
- **Fraunces**：具有独特衬线风格的展示字体，传达专业与精致感
- **IBM Plex Sans**：清晰易读的无衬线字体，适合长时间阅读

### 3.2 色彩系统

采用语义化 CSS 变量，支持亮色/暗色双主题：

```css
/* src/app/globals.css */

:root {
  --background: 36 33% 98%;
  --foreground: 222 22% 12%;
  --card: 36 33% 99%;
  --card-foreground: 222 22% 12%;
  --popover: 36 33% 98%;
  --popover-foreground: 222 22% 12%;
  --primary: 222 70% 34%;
  --primary-foreground: 0 0% 100%;
  --secondary: 32 45% 92%;
  --secondary-foreground: 222 22% 16%;
  --muted: 30 30% 94%;
  --muted-foreground: 215 14% 42%;
  --accent: 188 65% 45%;
  --accent-foreground: 0 0% 100%;
  --destructive: 0 70% 50%;
  --destructive-foreground: 0 0% 100%;
  --border: 28 20% 88%;
  --input: 28 20% 86%;
  --ring: 222 70% 34%;
  --radius: 0.75rem;
}

.dark {
  --background: 222 22% 10%;
  --foreground: 36 30% 94%;
  --card: 222 22% 12%;
  --card-foreground: 36 30% 94%;
  --popover: 222 22% 12%;
  --popover-foreground: 36 30% 94%;
  --primary: 36 75% 65%;
  --primary-foreground: 222 22% 12%;
  --secondary: 222 18% 18%;
  --secondary-foreground: 36 30% 94%;
  --muted: 222 16% 20%;
  --muted-foreground: 30 12% 70%;
  --accent: 188 65% 52%;
  --accent-foreground: 222 22% 12%;
  --destructive: 0 62% 45%;
  --destructive-foreground: 0 0% 98%;
  --border: 222 16% 22%;
  --input: 222 16% 26%;
  --ring: 36 75% 65%;
}
```

**色彩语义**：

| 语义 Token | 用途 | 亮色值 | 暗色值 |
|-----------|------|--------|--------|
| `background` | 页面背景 | 暖白色 | 深蓝灰 |
| `foreground` | 主文字 | 深蓝灰 | 暖白色 |
| `primary` | 主要操作 | 深蓝色 | 金黄色 |
| `secondary` | 次要元素 | 暖米色 | 深蓝灰 |
| `muted` | 弱化元素 | 浅米色 | 中灰 |
| `accent` | 强调元素 | 青绿色 | 青绿色 |
| `destructive` | 危险操作 | 红色 | 红色 |

**设计理念**：
- 亮色主题采用暖色调，营造温馨专业感
- 暗色主题采用冷色调，减少视觉疲劳
- `accent` 色在两种主题下保持一致，确保品牌识别度

### 3.3 间距与圆角

```typescript
// tailwind.config.ts
theme: {
  container: {
    center: true,
    padding: "2rem",
    screens: {
      "2xl": "1400px"
    }
  },
  extend: {
    borderRadius: {
      lg: "var(--radius)",      // 0.75rem
      md: "calc(var(--radius) - 2px)",
      sm: "calc(var(--radius) - 4px)"
    }
  }
}
```

### 3.4 视觉层次

项目采用层次化背景设计：

```tsx
// src/components/app/app-shell.tsx
<div className="min-h-screen bg-[radial-gradient(circle_at_top,_hsl(var(--secondary)),_transparent_60%),_linear-gradient(to_bottom,_hsl(var(--muted)_/_0.8),_transparent)]">
```

**层次构成**：
1. 顶部径向渐变：从 `secondary` 色向透明过渡
2. 底部线性渐变：`muted` 色淡出
3. 创造深度感，避免纯色背景的单调

---

## 4. 组件架构

### 4.1 组件分类

```
src/components/
├── app/                    # 应用级组件
│   ├── app-shell.tsx       # 应用外壳（布局容器）
│   └── theme-toggle.tsx    # 主题切换
├── ui/                     # 基础 UI 组件
│   ├── alert-dialog.tsx    # 确认对话框
│   ├── badge.tsx           # 标签徽章
│   ├── button.tsx          # 按钮
│   ├── card.tsx            # 卡片容器
│   ├── dropdown-menu.tsx   # 下拉菜单
│   ├── input.tsx           # 输入框
│   ├── label.tsx           # 表单标签
│   ├── separator.tsx       # 分隔线
│   ├── tabs.tsx            # 标签页
│   └── textarea.tsx        # 文本域
└── theme-provider.tsx      # 主题上下文
```

### 4.2 核心组件规范

#### Button 组件

```tsx
// src/components/ui/button.tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-background",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "border border-border bg-background hover:bg-muted",
        ghost: "hover:bg-muted",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90"
      },
      size: {
        default: "h-10 px-4",
        sm: "h-9 rounded-lg px-3",
        lg: "h-11 rounded-lg px-6",
        icon: "h-10 w-10"
      }
    }
  }
)
```

**变体说明**：

| 变体 | 用途 | 视觉特征 |
|------|------|---------|
| `default` | 主要操作 | 实心填充，主题色 |
| `secondary` | 次要操作 | 浅色填充 |
| `outline` | 边框按钮 | 透明背景，边框 |
| `ghost` | 幽灵按钮 | 无边框，hover 效果 |
| `destructive` | 危险操作 | 红色填充 |

#### Card 组件

```tsx
// src/components/ui/card.tsx
const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("rounded-lg border border-border bg-card text-card-foreground shadow-sm", className)}
      {...props}
    />
  )
)

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn("font-display text-xl tracking-tight", className)} {...props} />
  )
)
```

**组合模式**：

```tsx
<Card>
  <CardHeader>
    <CardTitle>标题</CardTitle>
    <CardDescription>描述文字</CardDescription>
  </CardHeader>
  <CardContent>内容区域</CardContent>
  <CardFooter>底部操作</CardFooter>
</Card>
```

#### Badge 组件

```tsx
// src/components/ui/badge.tsx
const badgeVariants = cva(
  "inline-flex items-center rounded-lg border border-border px-2.5 py-1 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-secondary text-secondary-foreground",
        outline: "bg-background text-foreground",
        accent: "bg-accent text-accent-foreground",
        muted: "bg-muted text-muted-foreground"
      }
    }
  }
)
```

**使用场景**：

| 变体 | 用途 |
|------|------|
| `default` | 默认标签 |
| `outline` | 轮廓标签 |
| `accent` | 强调标签（如状态） |
| `muted` | 弱化标签（如 ID） |

### 4.3 shadcn/ui 使用规范

项目遵循 shadcn/ui 的核心原则：

1. **使用现有组件优先**：避免重复造轮子
2. **组合而非继承**：通过组合构建复杂 UI
3. **语义化颜色**：使用 `bg-primary` 而非 `bg-blue-500`
4. **内置变体**：优先使用 `variant` 属性而非自定义样式

**间距规范**：
- 使用 `gap-*` 而非 `space-x-*` / `space-y-*`
- 使用 `flex flex-col gap-*` 构建垂直布局

**当前现状说明**：
- 现有页面中仍存在部分 `space-y-*` 用法，属于历史实现；新代码应按 `gap-*` 规范新增。
- 历史样式类替换建议在不改变视觉表现的前提下分批进行，优先改动活跃页面（`/login`、`/register`、`/skills/*`）。

---

## 5. 页面结构

### 5.1 路由架构

```
src/app/
├── layout.tsx              # 根布局
├── page.tsx                # 首页（入口卡片，不自动重定向）
├── globals.css             # 全局样式
├── login/
│   └── page.tsx            # 登录页
├── register/
│   └── page.tsx            # 注册页
├── dashboard/
│   └── page.tsx            # 控制台概览
├── skills/
│   ├── page.tsx            # Skills 列表
│   ├── new/
│   │   └── page.tsx        # 创建 Skill
│   └── [skillUuid]/
│       └── page.tsx        # Skill 详情
├── tokens/
│   └── page.tsx            # API Token 管理
├── profile/
│   └── page.tsx            # 个人信息
└── security/
    └── page.tsx            # 安全设置
```

### 5.2 布局结构

#### 根布局

```tsx
// src/app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${displayFont.variable} ${bodyFont.variable}`} suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  )
}
```

#### 应用外壳

```tsx
// src/components/app/app-shell.tsx
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isAuthRoute = pathname === "/login" || pathname === "/register"

  // 认证路由：无导航栏
  if (isAuthRoute) {
    return <main className="min-h-screen">{children}</main>
  }

  // 受保护路由：带导航栏
  return (
    <div className="min-h-screen bg-[...]">
      <header>
        {/* Logo + 用户菜单 + 导航标签 */}
      </header>
      <main className="container mx-auto max-w-screen-xl px-6 py-8">
        {children}
      </main>
    </div>
  )
}
```

### 5.3 页面设计模式

#### 登录页

```tsx
// 双栏布局：左侧品牌展示 + 右侧登录表单
<div className="mx-auto grid min-h-screen max-w-screen-xl items-center gap-10 px-6 py-12 lg:grid-cols-[1.1fr_0.9fr]">
  <div className="space-y-6">
    {/* 品牌区域 */}
  </div>
  <Card className="border-border/80 shadow-lg">
    {/* 登录表单 */}
  </Card>
</div>
```

**交互流程**：
1. 用户输入邮箱
2. 点击"发送验证码"按钮
3. 后端发送 6 位验证码到邮箱
4. 用户输入验证码
5. 点击"登录"完成认证

#### 控制台概览

```tsx
// 统计卡片网格
<div className="grid gap-4 lg:grid-cols-3">
  {[
    { title: "活跃 Skills", value: "3", tag: "启用中" },
    { title: "可用 Tokens", value: "2", tag: "未过期" },
    { title: "工具调用成功率", value: "92.3%", tag: "过去 24h" }
  ].map((item) => (
    <Card key={item.title}>
      <CardHeader>
        <CardDescription>{item.title}</CardDescription>
        <CardTitle className="text-3xl">{item.value}</CardTitle>
      </CardHeader>
      <CardContent>
        <Badge variant="accent">{item.tag}</Badge>
      </CardContent>
    </Card>
  ))}
</div>
```

#### Skills 列表页

```tsx
// 搜索 + 列表布局
<Card>
  <CardHeader>
    <CardTitle>搜索与筛选</CardTitle>
  </CardHeader>
  <CardContent>
    <form className="flex flex-wrap gap-3">
      <div className="flex flex-1 items-center gap-2 rounded-lg border border-input bg-background px-3">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input className="border-0 px-0 focus-visible:ring-0" placeholder="搜索 Skill" />
      </div>
      <Button type="submit" variant="secondary">搜索</Button>
    </form>
  </CardContent>
</Card>
```

#### Skill 详情页

```tsx
// Tabs 组织内容
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">概览</TabsTrigger>
    <TabsTrigger value="files">文件</TabsTrigger>
    <TabsTrigger value="versions">版本</TabsTrigger>
    <TabsTrigger value="settings">设置</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">
    {/* 概览内容：名称、描述、可见性、状态 */}
  </TabsContent>
  <TabsContent value="files">
    {/* 文件列表：支持预览 */}
  </TabsContent>
  <TabsContent value="versions">
    {/* 版本列表：支持对比、回滚、下载、安装说明 */}
  </TabsContent>
  <TabsContent value="settings">
    {/* 设置表单：名称、描述、可见性修改 */}
  </TabsContent>
</Tabs>
```

**版本标签页功能**（P1 待实现）：
- 调用 `api.listSkillVersions(skillUuid)` 获取版本列表
- 调用 `api.diffSkillVersions(skillUuid, fromVersion, toVersion)` 对比版本差异
- 调用 `api.rollbackSkillVersion(skillUuid, version)` 回滚到指定版本
- 调用 `api.downloadSkill({ skill_uuid, version })` 下载指定版本
- 调用 `api.getInstallInstructions(skillUuid, version)` 获取安装说明

---

## 6. 状态管理与数据流

### 6.1 本地状态

页面级状态使用 React `useState`：

```tsx
const [status, setStatus] = useState<"loading" | "ready" | "error">("loading")
const [error, setError] = useState<string | null>(null)
const [skills, setSkills] = useState<Skill[]>([])
```

### 6.2 认证状态

认证 Token 存储在 `localStorage`：

```tsx
// src/lib/api.ts
const storageKey = "agentskills.tokens"

export function getStoredTokens(): TokenPair | null {
  if (typeof window === "undefined") return null
  const raw = window.localStorage.getItem(storageKey)
  if (!raw) return null
  return JSON.parse(raw) as TokenPair
}

export function storeTokens(tokens: TokenPair) {
  if (typeof window === "undefined") return
  window.localStorage.setItem(storageKey, JSON.stringify(tokens))
}

export function clearTokens() {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(storageKey)
}
```

### 6.3 数据获取模式

```tsx
// 标准数据加载模式
const [status, setStatus] = useState<"loading" | "ready" | "error">("loading")

useEffect(() => {
  const loadData = async () => {
    setStatus("loading")
    try {
      const data = await api.getData()
      setData(data)
      setStatus("ready")
    } catch (err) {
      setStatus("error")
      setError(err instanceof Error ? err.message : "加载失败")
    }
  }
  loadData()
}, [])
```

---

## 7. 认证与安全

### 7.1 认证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        认证流程                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 用户输入邮箱，点击"发送验证码"                                  │
│     POST /api/v1/auth/verification-code { email, purpose }       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 用户输入验证码，点击"登录"                                      │
│     POST /api/v1/auth/login { email, code }                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 后端返回 Token 对                                              │
│     { access_token, refresh_token }                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 前端存储 Token 到 localStorage                                 │
│     storeTokens({ access_token, refresh_token })                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. 跳转到控制台首页                                                │
│     router.replace("/dashboard")                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Token 自动刷新

```tsx
// src/lib/api.ts
async function apiFetch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { response, payload } = await fetchJson(path, options)
  
  if (response.ok) {
    return payload as T
  }
  
  // 401 错误时尝试刷新 Token
  if (response.status === 401 && !options.skipRefresh) {
    const tokens = getStoredTokens()
    if (tokens?.refresh_token) {
      try {
        const refreshed = await refreshTokens(tokens.refresh_token)
        storeTokens({ access_token: refreshed.access_token, refresh_token: tokens.refresh_token })
        // 使用新 Token 重试请求
        const retry = await fetchJson(path, { ...options, accessToken: refreshed.access_token })
        if (retry.response.ok) {
          return retry.payload as T
        }
      } catch (error) {
        clearTokens()
        throw error
      }
    }
  }
  
  throw new Error(getDetail(payload, response.statusText))
}
```

### 7.3 路由保护

#### 保护机制

```tsx
// src/components/app/app-shell.tsx
useEffect(() => {
  if (isAuthRoute) return
  
  const tokens = getStoredTokens()
  if (!tokens?.access_token) {
    router.replace("/login")
    return
  }
}, [isAuthRoute, router])
```

#### 路由分类

| 路由类型 | 路径 | 保护策略 |
|---------|------|---------|
| 公开路由 | `/login`, `/register` | 无需认证，已登录用户自动跳转到 `/dashboard` |
| 受保护路由 | `/dashboard`, `/skills/*`, `/tokens`, `/profile`, `/security` | 需要有效 Token，否则跳转到 `/login` |
| 首页 | `/` | 显示入口卡片，无自动重定向 |

#### 完整实现

```tsx
// src/components/app/app-shell.tsx
"use client"

import { usePathname, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { getStoredTokens } from "@/lib/api"

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  const isAuthRoute = pathname === "/login" || pathname === "/register"
  const isHomePage = pathname === "/"

  useEffect(() => {
    const tokens = getStoredTokens()
    
    // 已登录用户访问认证页面 -> 跳转到控制台
    if (isAuthRoute && tokens?.access_token) {
      router.replace("/dashboard")
      return
    }
    
    // 未登录用户访问受保护页面 -> 跳转到登录
    if (!isAuthRoute && !isHomePage && !tokens?.access_token) {
      router.replace("/login")
      return
    }
    
    setChecking(false)
  }, [isAuthRoute, isHomePage, router])

  // 认证检查中，显示空白或加载状态
  if (checking && !isAuthRoute && !isHomePage) {
    return null
  }

  // 认证路由：无导航栏
  if (isAuthRoute) {
    return <main className="min-h-screen">{children}</main>
  }

  // 受保护路由：带导航栏
  return (
    <div className="min-h-screen bg-[radial-gradient(...)]">
      <header>
        {/* Logo + 用户菜单 + 导航标签 */}
      </header>
      <main className="container mx-auto max-w-screen-xl px-6 py-8">
        {children}
      </main>
    </div>
  )
}
```

#### Token 过期处理

当 API 返回 401 且 Token 刷新失败时：
1. 清除本地存储的 Token
2. 跳转到 `/login` 页面
3. 可选：保存当前路径，登录后重定向回原页面

---

## 8. 主题系统

### 8.1 主题提供者

```tsx
// src/components/theme-provider.tsx
"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  )
}
```

### 8.2 主题切换组件

```tsx
// src/components/app/theme-toggle.tsx
export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === "dark"

  return (
    <Button variant="outline" size="icon" onClick={() => setTheme(isDark ? "light" : "dark")}>
      {isDark ? <Sun className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
    </Button>
  )
}
```

### 8.3 主题配置

| 属性 | 值 | 说明 |
|------|-----|------|
| `attribute` | `class` | 通过 class 切换主题 |
| `defaultTheme` | `system` | 默认跟随系统 |
| `enableSystem` | `true` | 启用系统主题检测 |
| `disableTransitionOnChange` | `true` | 切换时禁用过渡动画 |

---

## 9. API 集成

### 9.1 API 客户端

```tsx
// src/lib/api.ts
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export const api = {
  // 认证
  sendVerificationCode: (payload: { email: string; purpose: "login" | "register" | "bind_email" }) =>
    apiFetch<VerificationCodeResponse>("/api/v1/auth/verification-code", { method: "POST", body: JSON.stringify(payload) }),
  register: (payload: { email: string; username: string; code: string }) =>
    apiFetch<TokenPair>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; code: string }) =>
    apiFetch<TokenPair>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  refresh: (payload: { refresh_token: string }) =>
    apiFetch<AccessTokenResponse>("/api/v1/auth/refresh", { method: "POST", body: JSON.stringify(payload) }),
  ssoLogin: (payload: { id_token: string }) =>
    apiFetch<TokenPair>("/api/v1/auth/sso/login", { method: "POST", body: JSON.stringify(payload) }),
  ldapLogin: (payload: { username: string; password: string }) =>
    apiFetch<TokenPair>("/api/v1/auth/ldap/login", { method: "POST", body: JSON.stringify(payload) }),

  // 用户
  getMe: () => apiFetch<User>("/api/v1/users/me"),
  updateMe: (payload: { username?: string; email?: string }) =>
    apiFetch<User>("/api/v1/users/me", { method: "PUT", body: JSON.stringify(payload) }),

  // 用户账户管理
  requestDeleteAccount: () =>
    apiFetch<void>("/api/v1/users/me/delete-request", { method: "POST" }),
  deleteAccount: (payload: { code: string }) =>
    apiFetch<void>("/api/v1/users/me", { method: "DELETE", body: JSON.stringify(payload) }),
  bindEmail: (payload: { email: string; code: string }) =>
    apiFetch<{ bound: boolean }>("/api/v1/users/bind-email", { method: "POST", body: JSON.stringify(payload) }),
  updateUserIdentity: (userId: string, payload: UserIdentityUpdate) =>
    apiFetch<User>(`/api/v1/users/${userId}/identity`, { method: "PUT", body: JSON.stringify(payload) }),

  // Skills
  listSkills: (query?: string, includeInactive?: boolean) =>
    apiFetch<{ items: Skill[]; total: number }>(`/api/v1/skills${query ? `?q=${encodeURIComponent(query)}` : ""}${includeInactive ? (query ? "&" : "?") + "include_inactive=true" : ""}`),
  createSkill: (payload: { name: string; description?: string; tags?: string[]; visible?: "private" | "team" | "enterprise" }) =>
    apiFetch<Skill>("/api/v1/skills", { method: "POST", body: JSON.stringify(payload) }),
  getSkill: (skillUuid: string) => apiFetch<Skill>(`/api/v1/skills/${skillUuid}`),
  updateSkill: (skillUuid: string, payload: { name?: string; description?: string; tags?: string[]; visible?: "private" | "team" | "enterprise" }) =>
    apiFetch<Skill>(`/api/v1/skills/${skillUuid}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSkill: (skillUuid: string) => apiFetch<void>(`/api/v1/skills/${skillUuid}`, { method: "DELETE" }),
  activateSkill: (skillUuid: string) =>
    apiFetch<Skill>(`/api/v1/skills/${skillUuid}/activate`, { method: "POST" }),
  deactivateSkill: (skillUuid: string) =>
    apiFetch<Skill>(`/api/v1/skills/${skillUuid}/deactivate`, { method: "POST" }),
  getSkillCachePolicy: () => apiFetch<SkillCachePolicyResponse>("/api/v1/skills/cache-policy"),

  // Skill 文件管理
  listSkillFiles: (skillUuid: string) => apiFetch<string[]>(`/api/v1/skills/${skillUuid}/files`),
  getSkillFileContent: (skillUuid: string, filePath: string) =>
    apiFetchText(`/api/v1/skills/${skillUuid}/files/${encodeURIComponent(filePath)}`),
  uploadSkillFile: (skillUuid: string, file: File, metadata?: string) => { /* FormData upload */ },

  // Skill 版本管理
  listSkillVersions: (skillUuid: string) =>
    apiFetch<{ items: SkillVersion[] }>(`/api/v1/skills/${skillUuid}/versions`),
  diffSkillVersions: (skillUuid: string, fromVersion: string, toVersion: string) =>
    apiFetch<SkillVersionDiff>(`/api/v1/skills/${skillUuid}/versions/diff?from=${encodeURIComponent(fromVersion)}&to=${encodeURIComponent(toVersion)}`),
  getInstallInstructions: (skillUuid: string, version: string) =>
    apiFetch<SkillInstallInstructions>(`/api/v1/skills/${skillUuid}/versions/${version}/install-instructions`),
  rollbackSkillVersion: (skillUuid: string, version: string) =>
    apiFetch<SkillVersion>(`/api/v1/skills/${skillUuid}/versions/${version}/rollback`, { method: "POST" }),
  downloadSkill: (payload: { skill_uuid: string; version?: string }) =>
    apiFetch<SkillDownloadResponse>("/api/v1/skills/download", { method: "POST", body: JSON.stringify(payload) }),

  // Tokens
  listTokens: () => apiFetch<{ items: Token[]; total: number }>("/api/v1/tokens"),
  createToken: (payload: { name: string; expires_at?: string }) =>
    apiFetch<Token>("/api/v1/tokens", { method: "POST", body: JSON.stringify(payload) }),
  revokeToken: (tokenId: string) => apiFetch<void>(`/api/v1/tokens/${tokenId}`, { method: "DELETE" }),

  // Dashboard
  getDashboardOverview: () => apiFetch<DashboardOverview>("/api/v1/dashboard/overview"),
  cleanupMetrics: (payload?: { retention_days?: number }) =>
    apiFetch<{ removed: number; retention_days: number; cutoff: string }>("/api/v1/dashboard/metrics/cleanup", { method: "POST", body: JSON.stringify(payload ?? {}) }),
  resetMetrics24h: () =>
    apiFetch<{ removed: number; window_hours: number; window_start: string; window_end: string }>("/api/v1/dashboard/metrics/reset-24h", { method: "POST" }),
}
```

### 9.2 类型定义

> ⚠️ **说明**：以下类型定义对应前端实际代码（`src/lib/api.ts`），而后端实际返回字段可能更完整。前端类型与后端 Schema 字段对照请参见"前后端契约映射"表格。

```tsx
// src/lib/api.ts
export type TokenPair = {
  access_token: string
  refresh_token: string
}

export type Skill = {
  id: string
  name: string
  description: string | null
  tags?: string[]
  created_at?: string
  updated_at?: string
}

export type Token = {
  id: string
  name: string
  token?: string | null
  created_at?: string
  expires_at?: string | null
  revoked_at?: string | null
}

export type User = {
  id?: string
  email: string
  username: string
  is_superuser?: boolean
}

export type DashboardOverview = {
  active_skills: number
  available_tokens: number
  success_rate: number | null
  success_rate_window_hours: number
  success_rate_total: number
}

export type VerificationCodeResponse = {
  sent: boolean
  expires_in?: number
  resend_interval?: number
  max_attempts?: number
  attempts_left?: number
}

export type MetricsCleanupResponse = {
  removed: number
  retention_days: number
  cutoff: string
}

export type MetricsReset24hResponse = {
  removed: number
  window_hours: number
  window_start: string
  window_end: string
}
```

### 9.3 文件上传

```tsx
uploadSkillFile: async (skillUuid: string, file: File) => {
  const tokens = getStoredTokens()
  const formData = new FormData()
  formData.append("skill_uuid", skillUuid)
  formData.append("file", file)
  
  const response = await fetch(`${apiBaseUrl}/api/v1/skills/upload`, {
    method: "POST",
    body: formData,
    headers: tokens?.access_token ? { Authorization: `Bearer ${tokens.access_token}` } : undefined
  })
  
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}))
    throw new Error(errorPayload.detail || response.statusText)
  }
  
  return response.json()
}
```

### 9.4 前后端契约映射（当前实现）

| 页面/能力 | 前端调用 | 后端接口 | 状态 |
|---|---|---|---|
| 登录验证码发送 | `api.sendVerificationCode({ purpose: "login" })` | `POST /api/v1/auth/verification-code` | ✅ 已实现 |
| 注册验证码发送 | `api.sendVerificationCode({ purpose: "register" })` | `POST /api/v1/auth/verification-code` | ✅ 已实现 |
| 绑定邮箱验证码 | `api.sendVerificationCode({ purpose: "bind_email" })` | `POST /api/v1/auth/verification-code` | ✅ 已实现 |
| 登录 | `api.login` | `POST /api/v1/auth/login` | ✅ 已实现 |
| 注册 | `api.register` | `POST /api/v1/auth/register` | ✅ 已实现 |
| Token 刷新 | `api.refresh` + `apiFetch` 自动重试 | `POST /api/v1/auth/refresh` | ✅ 已实现 |
| 获取当前用户 | `api.getMe` | `GET /api/v1/users/me` | ✅ 已实现 |
| 更新当前用户 | `api.updateMe` | `PUT /api/v1/users/me` | ✅ 已实现 |
| 修改密码 | `api.changePassword` | **后端无此接口** | ❌ P0 需移除 |
| 账户删除 | `api.deleteAccount({ password })` | `DELETE /api/v1/users/me` (需 `code`) | ❌ P0 需修复 |
| 概览统计 | `api.getDashboardOverview` | `GET /api/v1/dashboard/overview` | ✅ 已实现 |
| 指标清理 | `api.cleanupMetrics` | `POST /api/v1/dashboard/metrics/cleanup` | ✅ 已实现（仅 superuser） |
| 24h 指标清零 | `api.resetMetrics24h` | `POST /api/v1/dashboard/metrics/reset-24h` | ✅ 已实现（仅 superuser） |
| Skill 列表 | `api.listSkills` | `GET /api/v1/skills` | ✅ 已实现 |
| Skill 创建 | `api.createSkill` | `POST /api/v1/skills` | ✅ 已实现 |
| Skill 详情 | `api.getSkill` | `GET /api/v1/skills/{skill_uuid}` | ✅ 已实现 |
| Skill 更新 | `api.updateSkill` | `PUT /api/v1/skills/{skill_uuid}` | ✅ 已实现 |
| Skill 删除 | `api.deleteSkill` | `DELETE /api/v1/skills/{skill_uuid}` | ✅ 已实现 |
| Skill 文件列表 | `api.listSkillFiles` | `GET /api/v1/skills/{skill_uuid}/files` | ✅ 已实现 |
| Skill 文件预览 | `api.getSkillFileContent` | `GET /api/v1/skills/{skill_uuid}/files/{file_path}` | ✅ 已实现 |
| Skill 文件上传 | `api.uploadSkillFile` | `POST /api/v1/skills/upload` | ✅ 已实现 |
| Token 列表 | `api.listTokens` | `GET /api/v1/tokens` | ✅ 已实现 |
| Token 创建 | `api.createToken` | `POST /api/v1/tokens` | ✅ 已实现 |
| Token 撤销 | `api.revokeToken` | `DELETE /api/v1/tokens/{token_id}` | ✅ 已实现 |
| SSO 登录 | 未实现 | `POST /api/v1/auth/sso/login` | 🔲 P2 待实现 |
| LDAP 登录 | 未实现 | `POST /api/v1/auth/ldap/login` | 🔲 P2 待实现 |
| Skill 缓存策略 | 未实现 | `GET /api/v1/skills/cache-policy` | 🔲 P1 待实现 |
| 请求删除账户验证码 | 未实现 | `POST /api/v1/users/me/delete-request` | 🔲 P0 待实现 |
| 邮箱绑定 | 未实现 | `POST /api/v1/users/bind-email` | 🔲 P1 待实现 |
| 用户身份管理 | 未实现 | `PUT /api/v1/users/{user_id}/identity` | 🔲 P2 待实现 |
| Skill 激活 | 未实现 | `POST /api/v1/skills/{skill_uuid}/activate` | 🔲 P1 待实现 |
| Skill 停用 | 未实现 | `POST /api/v1/skills/{skill_uuid}/deactivate` | 🔲 P1 待实现 |
| Skill 版本列表 | 未实现 | `GET /api/v1/skills/{skill_uuid}/versions` | 🔲 P1 待实现 |
| Skill 版本对比 | 未实现 | `GET /api/v1/skills/{skill_uuid}/versions/diff` | 🔲 P1 待实现 |
| Skill 安装说明 | 未实现 | `GET /api/v1/skills/{skill_uuid}/versions/{version}/install-instructions` | 🔲 P1 待实现 |
| Skill 版本回滚 | 未实现 | `POST /api/v1/skills/{skill_uuid}/versions/{version}/rollback` | 🔲 P1 待实现 |
| Skill 下载 | 未实现 | `POST /api/v1/skills/download` | 🔲 P1 待实现 |

**图例**：✅ 已实现 | ❌ 需修复/移除 | 🔲 待实现

**前端当前实现差异**（与后端实际接口对比）：

| 功能 | 前端实现 | 后端接口 | 差异说明 | 优先级 |
|------|---------|---------|---------|--------|
| 账户删除 | 发送 `password` | 需 `code`（通过 `/me/delete-request` 获取） | 需改为验证码模式 | P0 |
| 修改密码 | 调用 `changePassword` | **后端无此接口** | 需删除此功能 | P0 |
| 验证码发送 | 仅支持 `login`, `register`, `bind_email` | 还支持 `delete_account` | 需补齐 purpose | P0 |
| Skill 类型 | 缺少 `visible`, `is_active`, `current_version` 等 | `SkillResponse` 包含完整字段 | 需补齐类型定义 | P1 |
| Token 类型 | 缺少 `is_active`, `last_used_at` | `TokenResponse` 包含完整字段 | 需补齐类型定义 | P1 |
| User 类型 | 缺少 `role`, `status`, `enterprise_id`, `team_id` | `UserResponse` 包含完整字段 | 需补齐类型定义 | P1 |

**后端 Schema 与前端类型对照**：

| 后端 Schema | 后端实际字段 | 前端类型字段 | 说明 |
|------------|------------|------------|------|
| `SkillResponse` | `id, name, description, tags, visible, enterprise_id, team_id, skill_dir, current_version, is_active, cache_revoked_at, created_at, updated_at` | `id, name, description, tags?, created_at?, updated_at?` | 前端缺少大部分字段 |
| `TokenResponse` | `id, name, token?, is_active, expires_at, last_used_at, created_at` | `id, name, token?, created_at?, expires_at?, revoked_at?` | 前端缺少 `is_active`, `last_used_at`，多了 `revoked_at` |
| `UserResponse` | `id, email, username, is_active, is_superuser, enterprise_id, team_id, role, status, created_at, updated_at` | `id?, email, username, is_superuser?` | 前端缺少大部分字段 |
| `VerificationCodeRequest.purpose` | `"login" \| "register" \| "bind_email" \| "delete_account"` | `"login" \| "register" \| "bind_email"` | 前端不支持 `delete_account` |

补充说明：

- 后端 `DELETE /api/v1/users/me` 接收 `UserDeleteConfirm { code: string }`，需先调用 `POST /api/v1/users/me/delete-request` 获取验证码。
- 密码修改功能在后端已无对应接口，应移除前端安全页的"修改密码"卡片。
- 后端支持 SSO/LDAP 登录，需根据配置启用（`ENABLE_SSO`/`ENABLE_LDAP`）。
- 后端 Skill 接口支持 `visible`（enterprise/team/private）与版本能力，建议 Skill 详情页增加"版本"标签页。

---

## 10. 开发规范

### 10.1 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 组件 | PascalCase | `SkillCard`, `TokenList` |
| 函数 | camelCase | `loadSkills`, `handleDelete` |
| 常量 | camelCase（文件级常量） | `storageKey`, `apiBaseUrl` |
| 类型 | PascalCase | `Skill`, `TokenPair` |
| 文件 | kebab-case | `skill-card.tsx`, `api.ts` |

### 10.2 组件结构

```tsx
// 标准组件结构
"use client"

import { useEffect, useState } from "react"
import { IconName } from "lucide-react"

import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

export default function ComponentName() {
  // 1. 状态声明
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading")
  
  // 2. 副作用
  useEffect(() => {
    loadData()
  }, [])
  
  // 3. 事件处理
  const handleClick = async () => {
    // ...
  }
  
  // 4. 渲染
  return (
    <div className="flex flex-col gap-6">
      {/* ... */}
    </div>
  )
}
```

### 10.3 样式规范

**优先使用语义化类名**：

```tsx
// ✅ 推荐
<div className="bg-background text-foreground border-border">
<div className="bg-primary text-primary-foreground">
<div className="bg-muted text-muted-foreground">

// ❌ 避免
<div className="bg-white text-gray-900 border-gray-200">
<div className="bg-blue-600 text-white">
```

**间距使用 gap**：

```tsx
// ✅ 推荐
<div className="flex flex-col gap-4">
<div className="flex items-center gap-2">

// ❌ 避免
<div className="space-y-4">
<div className="flex items-center space-x-2">
```

### 10.4 错误处理

```tsx
// 标准错误处理模式
try {
  const data = await api.getData()
  setData(data)
  setStatus("ready")
} catch (err) {
  setStatus("error")
  setError(err instanceof Error ? err.message : "加载失败")
}
```

### 10.5 表单验证规范

**验证时机**：
- 邮箱：失焦时验证格式
- 验证码：实时验证长度（6位）
- 必填字段：提交时验证

**验证规则**：

| 字段 | 规则 | 错误提示 |
|------|------|---------|
| 邮箱 | 正则 `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` | "请输入有效的邮箱地址" |
| 验证码 | 长度 === 6，仅数字 | "验证码为 6 位数字" |
| Skill 名称 | 非空，长度 1-100 | "名称不能为空" / "名称最长 100 字符" |
| Skill 描述 | 可选，最长 500 字符 | "描述最长 500 字符" |

**验证状态样式**：

```tsx
// 错误状态
<Input
  className="border-destructive focus-visible:ring-destructive"
  aria-invalid="true"
/>
<span className="text-sm text-destructive">{error}</span>

// 成功状态（可选）
<Input className="border-accent" />
```

### 10.6 加载状态规范

**状态类型**：

| 状态 | 使用场景 | 实现方式 |
|------|---------|---------|
| `loading` | 初始数据加载 | Skeleton 骨架屏 |
| `submitting` | 表单提交中 | 按钮禁用 + 文案变化 |
| `refreshing` | 后台刷新 | 保持当前内容，静默更新 |

**骨架屏实现**：

```tsx
import { Skeleton } from "@/components/ui/skeleton"

// 卡片骨架屏
<Card>
  <CardHeader>
    <Skeleton className="h-6 w-32" />
  </CardHeader>
  <CardContent className="flex flex-col gap-2">
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
  </CardContent>
</Card>

// 列表骨架屏
<div className="flex flex-col gap-4">
  {Array.from({ length: 5 }).map((_, i) => (
    <Skeleton key={i} className="h-16 w-full" />
  ))}
</div>
```

**按钮加载状态**：

```tsx
<Button disabled={isSubmitting}>
  {isSubmitting ? "处理中..." : "提交"}
</Button>
```

### 10.7 响应式设计断点

**断点定义**（基于 Tailwind 默认）：

| 断点 | 最小宽度 | 使用场景 |
|------|---------|---------|
| `sm` | 640px | 大手机横屏 |
| `md` | 768px | 平板竖屏 |
| `lg` | 1024px | 平板横屏 / 小笔记本 |
| `xl` | 1280px | 桌面显示器 |
| `2xl` | 1536px | 大显示器 |

**响应式布局模式**：

```tsx
// 网格布局：移动端单列，桌面端多列
<div className="grid gap-4 lg:grid-cols-3">
  {/* 移动端：单列，桌面端：三列 */}
</div>

// 双栏布局：移动端堆叠，桌面端并排
<div className="flex flex-col lg:flex-row gap-6">
  <div className="lg:w-1/3">{/* 侧边栏 */}</div>
  <div className="lg:w-2/3">{/* 主内容 */}</div>
</div>

// 隐藏/显示元素
<div className="hidden lg:block">{/* 仅桌面端显示 */}</div>
<div className="lg:hidden">{/* 仅移动端显示 */}</div>
```

**当前项目断点使用**：
- 登录/注册页：`lg:grid-cols-[1.1fr_0.9fr]`（桌面端双栏）
- 控制台统计卡片：`lg:grid-cols-3`（桌面端三列）
- 容器最大宽度：`max-w-screen-xl`（1280px）

---

## 11. 部署配置

### 11.1 环境变量

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 11.2 构建命令

```json
// package.json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

### 11.3 启动流程

```bash
# 开发环境
cd frontend
npm install
npm run dev

# 生产环境
npm run build
npm start
```

### 11.4 与后端联调

```bash
# 后端服务
uvicorn mcp_agentskills.api_app:app --host 0.0.0.0 --port 8000

# 前端服务
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

---

## 12. 当前差异与修复优先级

### 12.1 P0（契约错误，优先修复）

1. **安全页账户删除流程重构**
   - 当前前端：`DELETE /api/v1/users/me` 发送 `{ password }`，且有"修改密码"卡片
   - 后端契约：需先调用 `POST /api/v1/users/me/delete-request` 获取验证码，再调用 `DELETE /api/v1/users/me` 发送 `{ code }`
   - 修改密码功能：后端无对应接口，建议移除该卡片或改为"邮箱绑定"功能
2. **安全页修改密码功能无后端接口**
   - 当前前端调用 `/api/v1/users/me/password`
   - 当前后端无此路由，功能应下线或替换为"邮箱绑定"

### 12.2 P1（体验与能力补齐）

1. **注册成功后的 Token 使用策略未明确**
   - 后端 `register` 返回 `TokenPair`，当前前端仅提示成功并跳转登录
   - 建议二选一：自动登录（存 Token）或维持现状并在文档中明确"注册后需手动登录"
2. **Skill 可见性与版本能力未接入**
   - 后端已支持 `visible`、`is_active`、`current_version` 字段与版本接口，前端仍停留在基础 CRUD
   - 建议 Skill 详情页增加"版本"标签页，支持查看历史版本、版本对比、回滚
3. **Skill 激活/停用功能未接入**
   - 后端已支持 `/activate` 和 `/deactivate` 接口，前端可在 Skill 列表/详情页添加状态切换功能
4. **邮箱绑定功能未接入**
   - 后端已支持 `POST /api/v1/users/bind-email`，可在个人信息页添加入口

### 12.3 P2（规范收敛）

1. **shadcn 间距规范收敛**
   - 渐进替换 `space-y-*` 到 `gap-*`
2. **类型契约增强**
   - 前端 `src/lib/api.ts` 中的类型定义需与文档对齐：
     - `Skill` 类型：补齐 `visible`、`is_active`、`current_version`、`enterprise_id`、`team_id`、`skill_dir`、`cache_revoked_at`
     - `Token` 类型：补齐 `is_active`、`last_used_at`，移除 `revoked_at`
     - `User` 类型：补齐 `is_active`、`enterprise_id`、`team_id`、`role`、`status`、`created_at`、`updated_at`
3. **错误码可视化**
   - 对 `CODE_EXPIRED`、`CODE_INVALID`、`TOO_MANY_ATTEMPTS`、`RESEND_TOO_FREQUENT` 显式分类提示，提升可恢复性
4. **SSO/LDAP 登录支持**
   - 根据后端配置 `ENABLE_SSO` 和 `ENABLE_LDAP` 决定是否显示相应登录入口

### 12.4 错误码可视化规范

后端返回的验证错误码：

| 错误码 | 说明 | 建议提示文案 |
|--------|------|--------------|
| `CODE_EXPIRED` | 验证码已过期 | "验证码已过期，请重新获取" |
| `CODE_INVALID` | 验证码错误 | "验证码错误，请检查后重试" |
| `TOO_MANY_ATTEMPTS` | 尝试次数过多 | "尝试次数过多，请稍后再试" |
| `RESEND_TOO_FREQUENT` | 重发过于频繁 | "验证码发送过于频繁，请稍候再试" |
| `SKILL_DEACTIVATED` | Skill 已停用 | "Skill 已停用，无法执行此操作" |

错误处理模式：
```tsx
// src/lib/api.ts 已包含错误码映射
const _verification_error_messages = {
  "CODE_EXPIRED": "验证码已过期",
  "CODE_INVALID": "验证码错误",
  "TOO_MANY_ATTEMPTS": "尝试次数过多，请稍后再试",
  "RESEND_TOO_FREQUENT": "重发过于频繁",
}

// 页面中使用
try {
  await api.login({ email, code })
} catch (err) {
  const message = err instanceof Error ? err.message : "登录失败"
  // 根据 message 内容或错误码显示对应的友好提示
  setError(message)
}
```

---

## 13. 待实现功能详细指导

本章节为第 1.2 节"待前端实现的能力"提供详细的实现指导，包括 UI 组件设计、交互流程和参考代码。

### 13.1 安全页账户删除流程（P0）

#### 交互流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    账户删除流程（验证码模式）                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 用户点击"删除账户"按钮                                          │
│     显示 AlertDialog 确认对话框                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 用户确认后，调用 api.requestDeleteAccount()                     │
│     后端发送验证码到用户邮箱                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 显示验证码输入界面                                               │
│     用户输入收到的 6 位验证码                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 调用 api.deleteAccount({ code })                              │
│     成功：清除本地 Token，跳转到登录页                                │
│     失败：显示错误提示（验证码过期/无效）                              │
└─────────────────────────────────────────────────────────────────┘
```

#### UI 组件结构

```tsx
// src/app/security/page.tsx
<Card className="border-destructive/50">
  <CardHeader>
    <CardTitle className="text-destructive">删除账户</CardTitle>
    <CardDescription>
      此操作不可撤销。删除账户将永久移除您的所有数据。
    </CardDescription>
  </CardHeader>
  <CardContent>
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">删除账户</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除账户？</AlertDialogTitle>
          <AlertDialogDescription>
            我们将发送验证码到您的邮箱以确认此操作。
          </AlertDialogDescription>
        </AlertDialogHeader>
        
        {/* 步骤 1：请求验证码 */}
        {!codeSent && (
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleRequestCode}>
              发送验证码
            </AlertDialogAction>
          </AlertDialogFooter>
        )}
        
        {/* 步骤 2：输入验证码 */}
        {codeSent && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="delete-code">验证码</Label>
              <Input
                id="delete-code"
                placeholder="输入 6 位验证码"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                maxLength={6}
              />
            </div>
            <AlertDialogFooter>
              <AlertDialogCancel>取消</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                disabled={code.length !== 6 || isDeleting}
              >
                {isDeleting ? "删除中..." : "确认删除"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </div>
        )}
      </AlertDialogContent>
    </AlertDialog>
  </CardContent>
</Card>
```

#### 实现代码

```tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api, clearTokens } from "@/lib/api"

export default function SecurityPage() {
  const router = useRouter()
  const [codeSent, setCodeSent] = useState(false)
  const [code, setCode] = useState("")
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRequestCode = async () => {
    try {
      setError(null)
      await api.requestDeleteAccount()
      setCodeSent(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送验证码失败")
    }
  }

  const handleDelete = async () => {
    try {
      setIsDeleting(true)
      setError(null)
      await api.deleteAccount({ code })
      clearTokens()
      router.replace("/login")
    } catch (err) {
      setIsDeleting(false)
      const message = err instanceof Error ? err.message : "删除失败"
      if (message.includes("CODE_EXPIRED")) {
        setError("验证码已过期，请重新获取")
      } else if (message.includes("CODE_INVALID")) {
        setError("验证码错误")
      } else {
        setError(message)
      }
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* 其他安全设置卡片 */}
      
      {/* 删除账户卡片 */}
      <Card className="border-destructive/50">
        {/* ... 如上 UI 组件结构 */}
      </Card>
    </div>
  )
}
```

#### 注意事项

1. **移除"修改密码"卡片**：后端无密码修改接口，应删除此功能
2. **错误处理**：需处理 `CODE_EXPIRED`、`CODE_INVALID` 等错误码
3. **成功后清理**：删除账户后必须清除本地 Token 并跳转到登录页

---

### 13.2 Skill 版本管理标签页（P1）

#### 功能概述

在 Skill 详情页新增"版本"标签页，支持：
- 查看版本历史列表
- 对比两个版本的差异
- 回滚到指定版本
- 下载指定版本
- 查看安装说明

#### UI 组件结构

```tsx
// src/app/skills/[skillUuid]/page.tsx 中的版本标签页
<TabsContent value="versions" className="flex flex-col gap-6">
  {/* 版本列表 */}
  <Card>
    <CardHeader>
      <CardTitle>版本历史</CardTitle>
      <CardDescription>
        当前版本：{skill.current_version || "无"}
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div className="flex flex-col gap-2">
        {versions.map((v) => (
          <div
            key={v.id}
            className="flex items-center justify-between rounded-lg border border-border p-4"
          >
            <div className="flex flex-col gap-1">
              <span className="font-medium">{v.version}</span>
              <span className="text-sm text-muted-foreground">
                {v.description}
              </span>
              <span className="text-xs text-muted-foreground">
                {new Date(v.created_at).toLocaleString()}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => showDiff(v.version)}
              >
                对比
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => showInstructions(v.version)}
              >
                安装说明
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => downloadVersion(v.version)}
              >
                下载
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => rollbackVersion(v.version)}
                disabled={v.version === skill.current_version}
              >
                回滚
              </Button>
            </div>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>

  {/* 版本对比对话框 */}
  <Dialog open={diffOpen} onOpenChange={setDiffOpen}>
    <DialogContent className="max-w-3xl">
      <DialogHeader>
        <DialogTitle>
          版本对比：{fromVersion} → {toVersion}
        </DialogTitle>
      </DialogHeader>
      <div className="flex flex-col gap-4">
        {diffData.added.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-green-600">新增文件：</span>
            <div className="flex flex-wrap gap-2">
              {diffData.added.map((file) => (
                <Badge key={file} variant="accent">{file}</Badge>
              ))}
            </div>
          </div>
        )}
        {diffData.removed.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-red-600">删除文件：</span>
            <div className="flex flex-wrap gap-2">
              {diffData.removed.map((file) => (
                <Badge key={file} variant="destructive">{file}</Badge>
              ))}
            </div>
          </div>
        )}
        {diffData.modified.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-yellow-600">修改文件：</span>
            <div className="flex flex-col gap-2">
              {diffData.modified.map((item) => (
                <details key={item.path} className="rounded-lg border border-border">
                  <summary className="cursor-pointer px-4 py-2 text-sm font-medium">
                    {item.path}
                  </summary>
                  <pre className="max-h-64 overflow-auto bg-muted p-4 text-xs">
                    {item.diff}
                  </pre>
                </details>
              ))}
            </div>
          </div>
        )}
        {diffData.added.length === 0 && diffData.removed.length === 0 && diffData.modified.length === 0 && (
          <p className="text-muted-foreground">两个版本无差异</p>
        )}
      </div>
    </DialogContent>
  </Dialog>

  {/* 安装说明对话框 */}
  <Dialog open={instructionsOpen} onOpenChange={setInstructionsOpen}>
    <DialogContent className="max-w-2xl">
      <DialogHeader>
        <DialogTitle>安装说明 - {selectedVersion}</DialogTitle>
      </DialogHeader>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium">策略：</span>
          <Badge variant="secondary">{instructionsData.strategy}</Badge>
        </div>
        {instructionsData.ecosystem && (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium">生态系统：</span>
            <Badge variant="outline">{instructionsData.ecosystem}</Badge>
          </div>
        )}
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium">依赖项：</span>
          <div className="flex flex-wrap gap-2">
            {instructionsData.dependencies.map((dep) => (
              <Badge key={dep} variant="secondary">{dep}</Badge>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium">安装命令：</span>
          <pre className="max-h-32 overflow-auto rounded-lg bg-muted p-4 text-sm">
            {instructionsData.commands.join("\n")}
          </pre>
        </div>
        {instructionsData.requirements_text && (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium">依赖文件：</span>
            <pre className="max-h-64 overflow-auto rounded-lg bg-muted p-4 text-sm">
              {instructionsData.requirements_text}
            </pre>
          </div>
        )}
      </div>
    </DialogContent>
  </Dialog>
</TabsContent>
```

#### 实现代码

```tsx
"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { api } from "@/lib/api"
import type { SkillVersion, SkillVersionDiff, SkillInstallInstructions } from "@/lib/api"

interface VersionTabProps {
  skillUuid: string
  currentVersion: string | null
}

export function VersionTab({ skillUuid, currentVersion }: VersionTabProps) {
  const [versions, setVersions] = useState<SkillVersion[]>([])
  const [loading, setLoading] = useState(true)

  const [diffOpen, setDiffOpen] = useState(false)
  const [fromVersion, setFromVersion] = useState("")
  const [toVersion, setToVersion] = useState("")
  const [diffData, setDiffData] = useState<SkillVersionDiff | null>(null)

  const [instructionsOpen, setInstructionsOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState("")
  const [instructionsData, setInstructionsData] = useState<SkillInstallInstructions | null>(null)

  useEffect(() => {
    loadVersions()
  }, [skillUuid])

  const loadVersions = async () => {
    try {
      setLoading(true)
      const data = await api.listSkillVersions(skillUuid)
      setVersions(data.items)
    } catch (err) {
      console.error("加载版本列表失败:", err)
    } finally {
      setLoading(false)
    }
  }

  const showDiff = async (targetVersion: string) => {
    if (!currentVersion) return
    try {
      const diff = await api.diffSkillVersions(skillUuid, currentVersion, targetVersion)
      setFromVersion(currentVersion)
      setToVersion(targetVersion)
      setDiffData(diff)
      setDiffOpen(true)
    } catch (err) {
      console.error("获取版本差异失败:", err)
    }
  }

  const showInstructions = async (version: string) => {
    try {
      const data = await api.getInstallInstructions(skillUuid, version)
      setSelectedVersion(version)
      setInstructionsData(data)
      setInstructionsOpen(true)
    } catch (err) {
      console.error("获取安装说明失败:", err)
    }
  }

  const downloadVersion = async (version: string) => {
    try {
      const data = await api.downloadSkill({ skill_uuid: skillUuid, version })
      // 注意：后端返回 encrypted_code，需要解密或由后端处理
      const blob = new Blob([data.encrypted_code], { type: "application/octet-stream" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `skill-${skillUuid}-${version}.enc`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error("下载失败:", err)
    }
  }

  const rollbackVersion = async (version: string) => {
    if (!confirm(`确定要回滚到版本 ${version} 吗？`)) return
    try {
      await api.rollbackSkillVersion(skillUuid, version)
      loadVersions()
    } catch (err) {
      console.error("回滚失败:", err)
    }
  }

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  return (
    <div className="flex flex-col gap-6">
      {/* ... 如上 UI 组件结构 */}
    </div>
  )
}
```

**注意**：`downloadSkill` 接口返回的是加密后的代码（`encrypted_code`），前端可能需要：
1. 直接保存加密文件供后续解密使用
2. 或在后端配置 `ENABLE_SKILL_DOWNLOAD_ENCRYPTION=false` 以获取明文

---

### 13.3 Skill 激活/停用状态切换（P1）

#### 功能概述

在 Skill 列表和详情页添加激活/停用状态切换功能。

#### UI 组件设计

**列表页 - 状态徽章 + 切换按钮：**

```tsx
// src/app/skills/page.tsx
<div className="flex items-center gap-2">
  <Badge variant={skill.is_active ? "accent" : "muted"}>
    {skill.is_active ? "已激活" : "已停用"}
  </Badge>
  <Button
    variant="ghost"
    size="sm"
    onClick={() => toggleActive(skill.id, !skill.is_active)}
  >
    {skill.is_active ? "停用" : "激活"}
  </Button>
</div>
```

**详情页 - 状态开关：**

```tsx
// src/app/skills/[skillUuid]/page.tsx 概览标签页
<div className="flex items-center justify-between rounded-lg border border-border p-4">
  <div className="flex flex-col gap-1">
    <span className="font-medium">状态</span>
    <span className="text-sm text-muted-foreground">
      {skill.is_active ? "Skill 正在运行" : "Skill 已停用"}
    </span>
  </div>
  <Switch
    checked={skill.is_active ?? true}
    onCheckedChange={(checked) => toggleActive(checked)}
  />
</div>
```

#### 实现代码

```tsx
const toggleActive = async (skillUuid: string, activate: boolean) => {
  try {
    if (activate) {
      await api.activateSkill(skillUuid)
    } else {
      await api.deactivateSkill(skillUuid)
    }
    setSkill((prev) => prev ? { ...prev, is_active: activate } : prev)
  } catch (err) {
    console.error("切换状态失败:", err)
  }
}
```

#### 状态显示样式

| 状态 | Badge 变体 | 颜色 |
|------|-----------|------|
| 已激活 | `accent` | 青绿色 |
| 已停用 | `muted` | 灰色 |

---

### 13.4 邮箱绑定功能（P1）

#### 功能概述

在个人信息页添加邮箱绑定入口，支持用户绑定/更换邮箱。

#### 交互流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      邮箱绑定流程                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 用户点击"绑定邮箱"按钮                                          │
│     显示 Dialog，输入新邮箱                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 点击"发送验证码"                                               │
│     调用 api.sendVerificationCode({ email, purpose: "bind_email" })│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 用户输入验证码                                                 │
│     调用 api.bindEmail({ email, code })                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 绑定成功，更新用户信息显示                                       │
└─────────────────────────────────────────────────────────────────┘
```

#### UI 组件结构

```tsx
// src/app/profile/page.tsx
<Card>
  <CardHeader>
    <CardTitle>邮箱设置</CardTitle>
  </CardHeader>
  <CardContent className="flex flex-col gap-4">
    <div className="flex items-center justify-between">
      <div className="flex flex-col gap-1">
        <span className="text-sm text-muted-foreground">当前邮箱</span>
        <span className="font-medium">{user.email}</span>
      </div>
      <Button variant="outline" onClick={() => setBindEmailOpen(true)}>
        更换邮箱
      </Button>
    </div>
  </CardContent>
</Card>

{/* 绑定邮箱对话框 */}
<Dialog open={bindEmailOpen} onOpenChange={setBindEmailOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>绑定新邮箱</DialogTitle>
      <DialogDescription>
        我们将发送验证码到您的新邮箱以确认绑定。
      </DialogDescription>
    </DialogHeader>
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="new-email">新邮箱</Label>
        <Input
          id="new-email"
          type="email"
          placeholder="请输入新邮箱"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
        />
      </div>
      
      {!codeSent ? (
        <Button
          onClick={handleSendCode}
          disabled={!newEmail || !newEmail.includes("@")}
        >
          发送验证码
        </Button>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            <Label htmlFor="bind-code">验证码</Label>
            <Input
              id="bind-code"
              placeholder="输入 6 位验证码"
              value={bindCode}
              onChange={(e) => setBindCode(e.target.value)}
              maxLength={6}
            />
          </div>
          <Button
            onClick={handleBindEmail}
            disabled={bindCode.length !== 6 || isBinding}
          >
            {isBinding ? "绑定中..." : "确认绑定"}
          </Button>
        </>
      )}
    </div>
  </DialogContent>
</Dialog>
```

#### 实现代码

```tsx
const [bindEmailOpen, setBindEmailOpen] = useState(false)
const [newEmail, setNewEmail] = useState("")
const [bindCode, setBindCode] = useState("")
const [codeSent, setCodeSent] = useState(false)
const [isBinding, setIsBinding] = useState(false)

const handleSendCode = async () => {
  try {
    await api.sendVerificationCode({ email: newEmail, purpose: "bind_email" })
    setCodeSent(true)
  } catch (err) {
    console.error("发送验证码失败:", err)
  }
}

const handleBindEmail = async () => {
  try {
    setIsBinding(true)
    await api.bindEmail({ email: newEmail, code: bindCode })
    setUser((prev) => prev ? { ...prev, email: newEmail } : prev)
    setBindEmailOpen(false)
    setNewEmail("")
    setBindCode("")
    setCodeSent(false)
  } catch (err) {
    const message = err instanceof Error ? err.message : "绑定失败"
    if (message.includes("CODE_EXPIRED")) {
      alert("验证码已过期，请重新获取")
    } else if (message.includes("CODE_INVALID")) {
      alert("验证码错误")
    } else {
      alert(message)
    }
  } finally {
    setIsBinding(false)
  }
}
```

---

## 附录

### A. 组件清单

| 组件 | 路径 | 用途 |
|------|------|------|
| AppShell | `components/app/app-shell.tsx` | 应用外壳 |
| ThemeToggle | `components/app/theme-toggle.tsx` | 主题切换 |
| ThemeProvider | `components/theme-provider.tsx` | 主题上下文 |
| Button | `components/ui/button.tsx` | 按钮 |
| Card | `components/ui/card.tsx` | 卡片容器 |
| Badge | `components/ui/badge.tsx` | 标签徽章 |
| Input | `components/ui/input.tsx` | 输入框 |
| Label | `components/ui/label.tsx` | 表单标签 |
| Textarea | `components/ui/textarea.tsx` | 文本域 |
| Tabs | `components/ui/tabs.tsx` | 标签页 |
| AlertDialog | `components/ui/alert-dialog.tsx` | 确认对话框 |
| Dialog | `components/ui/dialog.tsx` | 模态对话框 |
| DropdownMenu | `components/ui/dropdown-menu.tsx` | 下拉菜单 |
| Separator | `components/ui/separator.tsx` | 分隔线 |
| Switch | `components/ui/switch.tsx` | 开关组件 |
| Skeleton | `components/ui/skeleton.tsx` | 骨架屏加载 |

**待添加组件**（第 13 章实现需要）：
- `Dialog`：用于版本对比、安装说明、邮箱绑定等模态对话框
- `Switch`：用于 Skill 激活/停用状态切换
- `Skeleton`：用于数据加载时的骨架屏显示

### B. 页面清单

| 页面 | 路径 | 功能 |
|------|------|------|
| 登录 | `/login` | 邮箱验证码登录 |
| 注册 | `/register` | 用户注册 |
| 控制台 | `/dashboard` | 概览统计 |
| Skills 列表 | `/skills` | Skill 管理 |
| Skill 详情 | `/skills/[skillUuid]` | Skill 详情与编辑 |
| 创建 Skill | `/skills/new` | 创建新 Skill |
| Token 管理 | `/tokens` | API Token 管理 |
| 个人信息 | `/profile` | 用户资料编辑 |
| 安全设置 | `/security` | 安全配置 |

### C. 参考资源

- [Next.js 文档](https://nextjs.org/docs)
- [shadcn/ui 文档](https://ui.shadcn.com)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [Radix UI 文档](https://www.radix-ui.com/primitives)
- [Lucide 图标](https://lucide.dev/icons)
