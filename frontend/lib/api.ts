const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

function getToken(): string | null {
  return localStorage.getItem("rad_ai_token")
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function handleUnauthorized(res: Response) {
  if (res.status === 401) {
    localStorage.removeItem("rad_ai_token")
    localStorage.removeItem("rad_ai_user")
    if (typeof window !== "undefined" && window.location.pathname !== "/") {
      window.location.href = window.location.origin + "/"
    }
  }
}

async function throwIfUnauthorized(res: Response, fallbackMessage: string) {
  if (res.status === 401) handleUnauthorized(res)
  const err = await res.json().catch(() => ({ detail: fallbackMessage }))
  throw new Error(err.detail || fallbackMessage)
}

export type LoginResult = {
  user_id: number
  username: string
  role: string
}

export async function loginRequest(username: string, password: string): Promise<LoginResult> {
  const res = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "خطا در ورود" }))
    throw new Error(err.detail || "نام کاربری یا رمز عبور اشتباه است.")
  }
  const data = await res.json()
  localStorage.setItem("rad_ai_token", data.token)
  return data.user
}

export type AskResult = {
  answer: string
  steps?: { label: string; sql: string; result: string }[]
  is_confidential?: boolean
}

export async function askQuestion(
  question: string,
  history?: { role: string; content: string }[]
): Promise<AskResult> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ question, history: history || [] }),
  })
  if (!res.ok) {
    await throwIfUnauthorized(res, "خطای غیرمنتظره رخ داد.")
  }
  return res.json()
}

export type StreamCallbacks = {
  onMeta?: (steps: { label: string; sql: string; result: string }[], isConfidential: boolean) => void
  onToken?: (content: string) => void
  onDone?: () => void
  onError?: (message: string) => void
}

export async function askQuestionStream(
  question: string,
  history: { role: string; content: string }[] | undefined,
  callbacks: StreamCallbacks
) {
  try {
    const res = await fetch(`${API_BASE}/api/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ question, history: history || [] }),
    })
    if (res.status === 401) handleUnauthorized(res)
    if (!res.ok || !res.body) {
      throw new Error("خطای غیرمنتظره رخ داد.")
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split("\n\n")
      buffer = parts.pop() || ""
      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith("data:")) continue
        const jsonStr = line.slice(5).trim()
        if (!jsonStr) continue
        const event = JSON.parse(jsonStr)
        if (event.type === "meta") {
          callbacks.onMeta?.(event.steps || [], !!event.is_confidential)
        } else if (event.type === "token") {
          callbacks.onToken?.(event.content || "")
        } else if (event.type === "done") {
          callbacks.onDone?.()
        }
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "خطای غیرمنتظره رخ داد."
    callbacks.onError?.(message)
  }
}

export async function listSessions(userId: number) {
  const res = await fetch(`${API_BASE}/api/sessions/${userId}`, { headers: authHeaders() })
  if (!res.ok) await throwIfUnauthorized(res, "خطا در دریافت گفتگوها")
  return res.json()
}

export async function loadMessages(userId: number, sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${userId}/${sessionId}/messages`, {
    headers: authHeaders(),
  })
  if (!res.ok) await throwIfUnauthorized(res, "خطا در دریافت پیام‌ها")
  return res.json()
}

export async function createSession(title: string): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ title }),
  })
  if (!res.ok) await throwIfUnauthorized(res, "خطا در ایجاد گفتگو")
  return res.json()
}

export async function saveMessage(
  sessionId: string,
  role: string,
  content: string,
  steps?: unknown[]
) {
  const res = await fetch(`${API_BASE}/api/sessions/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, role, content, steps }),
  })
  if (!res.ok) await throwIfUnauthorized(res, "خطا در ذخیره پیام")
  return res.json()
}

export async function deleteSession(userId: number, sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${userId}/${sessionId}`, {
    method: "DELETE",
    headers: authHeaders(),
  })
  if (!res.ok) await throwIfUnauthorized(res, "خطا در حذف گفتگو")
  return res.json()
}

export type Stats = {
  employees: number | null
  equipment: number | null
  running: number | null
  recovery: number | null
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/api/stats`, { headers: authHeaders() })
  if (!res.ok) await throwIfUnauthorized(res, "خطا در دریافت آمار")
  return res.json()
}