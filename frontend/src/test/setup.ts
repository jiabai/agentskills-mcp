import "@testing-library/jest-dom"
import { vi } from "vitest"

vi.mock("@/lib/api", () => {
  return {
    api: {
      register: vi.fn(async () => ({})),
      login: vi.fn(async () => ({ access_token: "token", refresh_token: "refresh" })),
      refresh: vi.fn(async () => ({ access_token: "token", refresh_token: "refresh" })),
      getMe: vi.fn(async () => ({ username: "测试用户", email: "user@example.com" })),
      updateMe: vi.fn(async () => ({})),
      changePassword: vi.fn(async () => ({})),
      deleteAccount: vi.fn(async () => ({})),
      listSkills: vi.fn(async () => ({ items: [], total: 0 })),
      createSkill: vi.fn(async () => ({ id: "skill", name: "demo", description: "" })),
      getSkill: vi.fn(async () => ({ id: "skill", name: "demo", description: "" })),
      updateSkill: vi.fn(async () => ({ id: "skill", name: "demo", description: "" })),
      deleteSkill: vi.fn(async () => ({})),
      listSkillFiles: vi.fn(async () => []),
      uploadSkillFile: vi.fn(async () => ({ filename: "SKILL.md" })),
      listTokens: vi.fn(async () => ({ items: [], total: 0 })),
      createToken: vi.fn(async () => ({ id: "token", name: "demo", token: "ask_live_demo" })),
      revokeToken: vi.fn(async () => ({}))
    },
    storeTokens: vi.fn(),
    clearTokens: vi.fn()
  }
})
