import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, getJson, isApiError, sendForm, sendJson } from './client'

function respond(status: number, body?: unknown) {
  return vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response(body === undefined ? null : JSON.stringify(body), { status }))
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('getJson', () => {
  it('returns the parsed body on success', async () => {
    respond(200, { classrooms: [] })
    await expect(getJson('/classrooms')).resolves.toEqual({ classrooms: [] })
  })

  it('throws an ApiError carrying the status and the backend detail', async () => {
    respond(409, { detail: 'Você já tem uma turma com esse nome.' })
    const error = await getJson('/classrooms').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(isApiError(error, 409)).toBe(true)
    expect((error as ApiError).detail).toBe('Você já tem uma turma com esse nome.')
  })

  it('keeps an empty detail when the error has no JSON body', async () => {
    respond(502)
    const error = await getJson('/classrooms').catch((e: unknown) => e)
    expect(isApiError(error, 502)).toBe(true)
    expect((error as ApiError).detail).toBe('')
  })
})

describe('sendJson', () => {
  it('sends the body as JSON with the given method', async () => {
    const fetchSpy = respond(201, { id: 1 })
    await sendJson('POST', '/classrooms', { name: 'Turma A' })
    expect(fetchSpy).toHaveBeenCalledWith('/classrooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{"name":"Turma A"}',
    })
  })

  it('sends no body and no content type when there is nothing to send', async () => {
    const fetchSpy = respond(200, { deleted_classroom_id: 1 })
    await sendJson('DELETE', '/classrooms/1')
    expect(fetchSpy).toHaveBeenCalledWith('/classrooms/1', {
      method: 'DELETE',
      headers: undefined,
      body: undefined,
    })
  })
})

describe('sendForm', () => {
  it('posts the form as is, leaving the multipart header to the browser', async () => {
    const fetchSpy = respond(200, { classroom_id: 1 })
    const form = new FormData()
    form.append('classroom_id', '1')
    await sendForm('/classroom-imports', form)
    expect(fetchSpy).toHaveBeenCalledWith('/classroom-imports', { method: 'POST', body: form })
  })
})
