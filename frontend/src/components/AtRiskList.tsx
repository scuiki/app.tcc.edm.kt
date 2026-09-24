// At-risk student list (DASH-03). students_at_risk is a string[] of student IDs (Pitfall 1 — NOT
// objects); treating an entry as an object and reading a field off it would crash. Render each string
// verbatim as a list item.

export function AtRiskList({ atRiskStudents }: { atRiskStudents: string[] }) {
  return (
    <section>
      <h3 className="t-heading">Alunos em atenção</h3>
      <ul className="data-list">
        {atRiskStudents.map((subjectId) => (
          <li key={subjectId} className="data-list__row">
            <span className="data-list__label mono">{subjectId}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
