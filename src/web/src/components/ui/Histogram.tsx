import { Tooltip } from './Tooltip'
import './Histogram.css'

interface HistogramProps {
  // Uma contagem por faixa, da faixa de 0 a 10% até a de 90 a 100%
  bins: number[]
  // O que está sendo contado, como "alunos", para o texto de cada barra
  unit: string
  label: string
}

// Dez barras num tom só, sem eixo, porque a escala está na dica do cabeçalho da coluna
export function Histogram({ bins, unit, label }: HistogramProps) {
  const max = Math.max(1, ...bins)
  const width = Math.round(100 / bins.length)
  return (
    <figure className="histogram" aria-label={label}>
      <div className="histogram__bars">
        {bins.map((count, index) => (
          <Tooltip
            key={index}
            text={`${index * width} a ${(index + 1) * width}%, ${count} ${unit}`}
          >
            {count === 0 ? (
              <span className="histogram__bar is-zero" />
            ) : (
              <span className="histogram__bar" style={{ height: `${(count / max) * 100}%` }} />
            )}
          </Tooltip>
        ))}
      </div>
      <div className="visually-hidden">
        <table>
          <tbody>
            {bins.map((count, index) => (
              <tr key={index}>
                <th scope="row">
                  {index * width}% a {(index + 1) * width}%
                </th>
                <td>{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  )
}
