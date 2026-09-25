import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { hashParam, pathOf, useHashPath } from './hashRoute'

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

describe('hashParam', () => {
  it('reads a parameter from the query of the hash', () => {
    expect(hashParam('#/knowledge-components?classroom=3', 'classroom')).toBe('3')
  })

  it('is null without the parameter or without a query', () => {
    expect(hashParam('#/knowledge-components?other=1', 'classroom')).toBeNull()
    expect(hashParam('#/knowledge-components', 'classroom')).toBeNull()
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
