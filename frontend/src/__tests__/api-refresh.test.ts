import { beforeEach, describe, expect, it, vi } from "vitest"

type FetchResponse = {
  ok: boolean
  status: number
  json: () => Promise<unknown>
}

const createResponse = (status: number, body: unknown): FetchResponse => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body
})

describe("api refresh token", () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unmock("@/lib/api")
    window.localStorage.clear()
  })

  it("refreshes token and retries request", async () => {
    const fetchMock = vi.fn()
    fetchMock
      .mockResolvedValueOnce(createResponse(401, { detail: "Unauthorized" }))
      .mockResolvedValueOnce(createResponse(200, { access_token: "new-access", refresh_token: "new-refresh" }))
      .mockResolvedValueOnce(createResponse(200, { username: "demo", email: "demo@example.com" }))
    vi.stubGlobal("fetch", fetchMock)

    const { api, storeTokens, getStoredTokens } = await import("@/lib/api")
    storeTokens({ access_token: "expired", refresh_token: "refresh" })

    const user = await api.getMe()

    expect(user).toEqual({ username: "demo", email: "demo@example.com" })
    expect(getStoredTokens()).toEqual({ access_token: "new-access", refresh_token: "new-refresh" })
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it("clears tokens when refresh fails", async () => {
    const fetchMock = vi.fn()
    fetchMock
      .mockResolvedValueOnce(createResponse(401, { detail: "Unauthorized" }))
      .mockResolvedValueOnce(createResponse(401, { detail: "Refresh expired" }))
    vi.stubGlobal("fetch", fetchMock)

    const { api, storeTokens, getStoredTokens } = await import("@/lib/api")
    storeTokens({ access_token: "expired", refresh_token: "refresh" })

    await expect(api.getMe()).rejects.toThrow("Refresh expired")
    expect(getStoredTokens()).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
