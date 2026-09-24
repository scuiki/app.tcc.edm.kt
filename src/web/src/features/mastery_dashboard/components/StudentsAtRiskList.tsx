// O backend manda só os student_id, como texto, e não objetos
export function StudentsAtRiskList({ studentIds }: { studentIds: string[] }) {
  return (
    <section>
      <h3 className="t-section-title">Alunos em atenção</h3>
      <ul className="data-list">
        {studentIds.map((studentId) => (
          <li key={studentId} className="data-list__row">
            <span className="mono">{studentId}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
