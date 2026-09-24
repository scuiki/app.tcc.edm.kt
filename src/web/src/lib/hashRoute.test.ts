import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { pathOf, useHashPath } from './hashRoute'

afterEach(() => {
  window.location.hash = ''
})

describe('pathOf', () => {
  it('drops the hash sign and the query', () => {
    expect(pathOf('#/classrooms')).toBe('/classrooms')
    expect(pathOf('#/classrooms?id=3')).toBe('/classrooms')
  })

  it('returns an empty path for an empty hash', () => {
    expect(pathOf('')).toBe('')
  })
})

describe('useHashPath', () => {
  it('follows the hash as it changes', () => {
    window.location.hash = '#/classrooms'
    const { result } = renderHook(() => useHashPath())
    expect(result.current).toBe('/classrooms')

    act(() => {
      window.location.hash = '#/mastery-dashboard'
      window.dispatchEvent(new HashChangeEvent('hashchange'))
    })
    expect(result.current).toBe('/mastery-dashboard')
  })
})
