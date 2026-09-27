import { describe, expect, it } from 'vitest'

import { assignmentPath, classroomImportPath, classroomPath } from './paths'

describe('paths', () => {
  it('nests the exercise under its classroom', () => {
    expect(classroomPath(3)).toBe('/classrooms/3')
    expect(assignmentPath(3, 7, 'analysis')).toBe('/classrooms/3/assignments/7/analysis')
    expect(assignmentPath(3, 7, 'knowledge-components')).toBe(
      '/classrooms/3/assignments/7/knowledge-components',
    )
  })

  it('sends the classroom to the import in the query', () => {
    expect(classroomImportPath()).toBe('/classroom-imports')
    expect(classroomImportPath(3)).toBe('/classroom-imports?classroom=3')
  })
})
