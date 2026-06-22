// At-risk student list (DASH-03). at_risk_students is a string[] of student IDs (Pitfall 1 — NOT
// objects); treating an entry as an object and reading a field off it would crash. Render each string
// verbatim as a list item.

const MONO = 'ui-monospace, "SF Mono", "Cascadia Code", monospace'

export function AtRiskList({ atRiskStudents }: { atRiskStudents: string[] }) {
  return (
    <section>
      <h3>Alunos em atenção</h3>
      <ul>
        {atRiskStudents.map((subjectId) => (
          <li key={subjectId} style={{ fontFamily: MONO }}>
            {subjectId}
          </li>
        ))}
      </ul>
    </section>
  )
}
