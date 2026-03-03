import { render, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { AppShell } from "@/components/app/app-shell"

const replaceMock = vi.fn()

vi.mock("next/navigation", () => ({
  usePathname: () => "/profile",
  useRouter: () => ({ replace: replaceMock })
}))

describe("AppShell auth guard", () => {
  it("redirects to login when not authenticated", async () => {
    replaceMock.mockClear()
    window.localStorage.removeItem("agentskills.tokens")
    render(<AppShell>content</AppShell>)
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/login")
    })
  })
})
