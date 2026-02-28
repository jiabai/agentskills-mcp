import { render, screen } from "@testing-library/react"

import LoginPage from "@/app/login/page"
import RegisterPage from "@/app/register/page"
import DashboardPage from "@/app/dashboard/page"
import SkillsPage from "@/app/skills/page"
import SkillDetailPage from "@/app/skills/[skillId]/page"
import TokensPage from "@/app/tokens/page"
import ProfilePage from "@/app/profile/page"
import SecurityPage from "@/app/security/page"

describe("console pages", () => {
  it("renders login form", () => {
    render(<LoginPage />)
    expect(screen.getByRole("heading", { name: "欢迎回来" })).toBeInTheDocument()
    expect(screen.getByLabelText("邮箱")).toBeInTheDocument()
    expect(screen.getByLabelText("密码")).toBeInTheDocument()
  })

  it("renders register form", () => {
    render(<RegisterPage />)
    expect(screen.getByRole("heading", { name: "创建账户" })).toBeInTheDocument()
    expect(screen.getByLabelText("用户名")).toBeInTheDocument()
    expect(screen.getByLabelText("邮箱")).toBeInTheDocument()
  })

  it("renders dashboard overview", () => {
    render(<DashboardPage />)
    expect(screen.getByRole("heading", { name: "控制台概览" })).toBeInTheDocument()
  })

  it("renders skills list", async () => {
    render(<SkillsPage />)
    expect(await screen.findByRole("heading", { name: "Skills" })).toBeInTheDocument()
    expect(screen.getByPlaceholderText("搜索 Skill")).toBeInTheDocument()
  })

  it("renders skill detail tabs", async () => {
    render(<SkillDetailPage params={{ skillId: "demo" }} />)
    expect(await screen.findByRole("heading", { name: "Skill 详情" })).toBeInTheDocument()
    expect(await screen.findByRole("tab", { name: "概览" })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: "文件" })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: "设置" })).toBeInTheDocument()
  })

  it("renders tokens page", async () => {
    render(<TokensPage />)
    expect(await screen.findByRole("heading", { name: "API Tokens" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "创建 Token" })).toBeInTheDocument()
  })

  it("renders profile form", async () => {
    render(<ProfilePage />)
    expect(screen.getByRole("heading", { name: "个人信息" })).toBeInTheDocument()
    expect(await screen.findByLabelText("显示名称")).toBeInTheDocument()
  })

  it("renders security form", () => {
    render(<SecurityPage />)
    expect(screen.getByRole("heading", { name: "安全设置" })).toBeInTheDocument()
    expect(screen.getByLabelText("当前密码")).toBeInTheDocument()
  })
})
