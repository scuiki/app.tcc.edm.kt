// Os endereços do app, montados num lugar só, para um link nunca sair digitado à mão

export type AssignmentScreen = 'knowledge-components' | 'analysis'

export function classroomPath(classroomId: number): string {
  return `/classrooms/${classroomId}`
}

export function assignmentPath(
  classroomId: number,
  assignmentId: number,
  screen: AssignmentScreen,
): string {
  return `${classroomPath(classroomId)}/assignments/${assignmentId}/${screen}`
}

// A importação é uma tela fixa, e a turma vai na query quando já se sabe qual é
export function classroomImportPath(classroomId?: number): string {
  return classroomId == null ? '/classroom-imports' : `/classroom-imports?classroom=${classroomId}`
}
