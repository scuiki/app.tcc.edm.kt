// A via única de dados, sempre na própria origem, porque o Vite repassa as rotas para a api

// O status e o detail do backend, para a tela distinguir um 409 de uma api fora do ar
export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail || `API ${status}`)
    this.status = status
    this.detail = detail
  }
}

export function isApiError(error: unknown, status: number): error is ApiError {
  return error instanceof ApiError && error.status === status
}

export function getJson<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function sendJson<T>(method: 'POST' | 'PUT' | 'DELETE', path: string, body?: unknown) {
  return request<T>(path, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

// O navegador monta o multipart e o boundary sozinho, então não se passa Content-Type
export function sendForm<T>(path: string, form: FormData) {
  return request<T>(path, { method: 'POST', body: form })
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) throw new ApiError(response.status, await readDetail(response))
  return response.json() as Promise<T>
}

// Um erro sem corpo JSON, como o de um proxy sem a api, vira um detail vazio
async function readDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    return typeof body?.detail === 'string' ? body.detail : ''
  } catch {
    return ''
  }
}
