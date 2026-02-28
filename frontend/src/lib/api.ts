export type TokenPair = {
  access_token: string
  refresh_token: string
}

export type Skill = {
  id: string
  name: string
  description: string | null
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
}

const storageKey = "agentskills.tokens"

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export function getStoredTokens(): TokenPair | null {
  if (typeof window === "undefined") {
    return null
  }
  const raw = window.localStorage.getItem(storageKey)
  if (!raw) {
    return null
  }
  try {
    return JSON.parse(raw) as TokenPair
  } catch {
    return null
  }
}

export function storeTokens(tokens: TokenPair) {
  if (typeof window === "undefined") {
    return
  }
  window.localStorage.setItem(storageKey, JSON.stringify(tokens))
}

export function clearTokens() {
  if (typeof window === "undefined") {
    return
  }
  window.localStorage.removeItem(storageKey)
}

type ApiRequestOptions = RequestInit & {
  skipRefresh?: boolean
  accessToken?: string
}

type ApiResponse = {
  response: Response
  payload: unknown
}

const getDetail = (payload: unknown, fallback: string) => {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: string }).detail
    if (detail) {
      return detail
    }
  }
  return fallback
}

const fetchJson = async (path: string, options: ApiRequestOptions = {}): Promise<ApiResponse> => {
  const { skipRefresh: _skipRefresh, accessToken, ...requestOptions } = options
  const tokens = getStoredTokens()
  const headers = new Headers(requestOptions.headers)
  headers.set("Content-Type", "application/json")
  const resolvedToken = accessToken ?? tokens?.access_token
  if (resolvedToken) {
    headers.set("Authorization", `Bearer ${resolvedToken}`)
  }
  const response = await fetch(`${apiBaseUrl}${path}`, { ...requestOptions, headers })
  if (response.status === 204) {
    return { response, payload: {} }
  }
  const payload = await response.json().catch(() => ({}))
  return { response, payload }
}

const refreshTokens = async (refreshToken: string) => {
  const { response, payload } = await fetchJson("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
    accessToken: "",
    skipRefresh: true
  })
  if (!response.ok) {
    throw new Error(getDetail(payload, response.statusText))
  }
  return payload as TokenPair
}

async function apiFetch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { response, payload } = await fetchJson(path, options)
  if (response.ok) {
    return payload as T
  }
  if (response.status === 401 && !options.skipRefresh) {
    const tokens = getStoredTokens()
    if (tokens?.refresh_token) {
      try {
        const refreshed = await refreshTokens(tokens.refresh_token)
        storeTokens(refreshed)
        const retry = await fetchJson(path, { ...options, accessToken: refreshed.access_token, skipRefresh: true })
        if (retry.response.ok) {
          return retry.payload as T
        }
        throw new Error(getDetail(retry.payload, retry.response.statusText))
      } catch (error) {
        clearTokens()
        throw error
      }
    }
  }
  throw new Error(getDetail(payload, response.statusText))
}

export const api = {
  register: (payload: { email: string; username: string; password: string }) =>
    apiFetch("/api/v1/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    apiFetch<TokenPair>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  refresh: (payload: { refresh_token: string }) =>
    apiFetch<TokenPair>("/api/v1/auth/refresh", { method: "POST", body: JSON.stringify(payload) }),
  getMe: () => apiFetch<User>("/api/v1/users/me"),
  updateMe: (payload: { username?: string; email?: string }) =>
    apiFetch("/api/v1/users/me", { method: "PUT", body: JSON.stringify(payload) }),
  changePassword: (payload: { current_password: string; new_password: string }) =>
    apiFetch("/api/v1/users/me/password", { method: "PUT", body: JSON.stringify(payload) }),
  deleteAccount: (payload: { password: string }) =>
    apiFetch("/api/v1/users/me", { method: "DELETE", body: JSON.stringify(payload) }),
  listSkills: (query?: string) =>
    apiFetch<{ items: Skill[]; total: number }>(`/api/v1/skills${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createSkill: (payload: { name: string; description?: string | null }) =>
    apiFetch<Skill>("/api/v1/skills", { method: "POST", body: JSON.stringify(payload) }),
  getSkill: (skillId: string) => apiFetch<Skill>(`/api/v1/skills/${skillId}`),
  updateSkill: (skillId: string, payload: { name?: string; description?: string | null }) =>
    apiFetch<Skill>(`/api/v1/skills/${skillId}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSkill: (skillId: string) => apiFetch(`/api/v1/skills/${skillId}`, { method: "DELETE" }),
  listSkillFiles: (skillId: string) => apiFetch<string[]>(`/api/v1/skills/${skillId}/files`),
  uploadSkillFile: async (skillId: string, file: File) => {
    const tokens = getStoredTokens()
    const formData = new FormData()
    formData.append("skill_id", skillId)
    formData.append("file", file)
    const response = await fetch(`${apiBaseUrl}/api/v1/skills/upload`, {
      method: "POST",
      body: formData,
      headers: tokens?.access_token ? { Authorization: `Bearer ${tokens.access_token}` } : undefined
    })
    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}))
      const detail = errorPayload.detail || response.statusText
      throw new Error(detail)
    }
    return (await response.json()) as { filename: string }
  },
  listTokens: () => apiFetch<{ items: Token[]; total: number }>("/api/v1/tokens"),
  createToken: (payload: { name: string; expires_at?: string | null }) =>
    apiFetch<Token>("/api/v1/tokens", { method: "POST", body: JSON.stringify(payload) }),
  revokeToken: (tokenId: string) => apiFetch(`/api/v1/tokens/${tokenId}`, { method: "DELETE" })
}
