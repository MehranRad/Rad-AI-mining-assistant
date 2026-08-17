export type ChatRole = 'user' | 'assistant'

export type StepDetail = {
  label: string
  sql: string
  result: string
}

export type ChatMessage = {
  role: ChatRole
  content: string
  steps?: StepDetail[]
}

export type SessionSummary = {
  session_id: string
  title: string
}

export type StoredUser = {
  user_id: number
  username: string
  role: string
}

export type AuthSession = {
  token: string
  user: StoredUser
}