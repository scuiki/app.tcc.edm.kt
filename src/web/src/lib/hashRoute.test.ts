import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { hashParam, matchPath, pathOf, useHashPath } from './hashRoute'

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

describe('matchPath', () => {
  it('captures the numeric ids named in the pattern', () => {
    expect(matchPath('/classrooms/:classroomId', '/classrooms/3')).toEqual({ classroomId: 3 })
    expect(
      matchPath(
        '/classrooms/:classroomId/assignments/:assignmentId/analysis',
        '/classrooms/3/assignments/7/analysis',
      ),
    ).toEqual({ classroomId: 3, assignmentId: 7 })
  })

  it('matches a literal path with no params', () => {
    expect(matchPath('/classrooms', '/classrooms')).toEqual({})
  })

  it('refuses a different length, a different literal, or an id that is not a positive integer', () => {
    expect(matchPath('/classrooms/:classroomId', '/classrooms')).toBeNull()
    expect(matchPath('/classrooms/:classroomId', '/classrooms/3/x')).toBeNull()
    expect(matchPath('/classrooms/:classroomId', '/turmas/3')).toBeNull()
    expect(matchPath('/classrooms/:classroomId', '/classrooms/abc')).toBeNull()
    expect(matchPath('/classrooms/:classroomId', '/classrooms/0')).toBeNull()
    expect(matchPath('/classrooms/:classroomId', '/classrooms/')).toBeNull()
  })
})

describe('useHashPath', () => {
  it('follows the hash as it changes', () => {
    window.location.hash = '#/classrooms'
    const { result } = renderHook(() => useHashPath())
    expect(result.current).toBe('/classrooms')

    act(() => {
      window.location.hash = '#/classroom-imports'
      window.dispatchEvent(new HashChangeEvent('hashchange'))
    })
    expect(result.current).toBe('/classroom-imports')
  })
})
