import "@testing-library/jest-dom"
import { vi } from "vitest"

vi.mock("@/lib/api", () => {
  return {
    api: {
      register: vi.fn(async () => ({})),
      login: vi.fn(async () => ({ access_token: "token", refresh_token: "refresh" })),
      refresh: vi.fn(async () => ({ access_token: "token", refresh_token: "refresh" })),
      getMe: vi.fn(async () => ({ username: "测试用户", email: "user@example.com", is_superuser: false })),
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
      revokeToken: vi.fn(async () => ({})),
      cleanupMetrics: vi.fn(async () => ({ removed: 0, retention_days: 90, cutoff: "2026-03-04T00:00:00Z" })),
      resetMetrics24h: vi.fn(async () => ({
        removed: 0,
        window_hours: 24,
        window_start: "2026-03-03T00:00:00Z",
        window_end: "2026-03-04T00:00:00Z"
      }))
    },
    storeTokens: vi.fn(),
    clearTokens: vi.fn(),
    getStoredTokens: vi.fn(() => null)
  }
})
