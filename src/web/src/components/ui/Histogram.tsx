import { Tooltip } from './Tooltip'
import './Histogram.css'

interface HistogramProps {
  // Uma contagem por faixa, da faixa de 0 a 10% até a de 90 a 100%
  bins: number[]
  // O que está sendo contado, como "alunos", para o texto de cada barra
  unit: string
  label: string
  // Sem o eixo, numa tabela em que o cabeçalho já diz a escala
  axis?: boolean
}

// Dez barras num tom só, sem corte nem rótulo; a forma é o dado e a leitura é de quem olha
export function Histogram({ bins, unit, label, axis = true }: HistogramProps) {
  const max = Math.max(1, ...bins)
  const width = Math.round(100 / bins.length)
  return (
    <figure className="histogram" aria-label={label}>
      <div className="histogram__bars">
        {bins.map((count, index) => (
          <Tooltip
            key={index}
            text={`${count} ${unit} entre ${index * width}% e ${(index + 1) * width}%`}
          >
            <span
              className="histogram__bar"
              style={{ height: `${Math.max(2, (count / max) * 100)}%` }}
            />
          </Tooltip>
        ))}
      </div>
      {axis ? (
        <div className="histogram__axis" aria-hidden="true">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      ) : null}
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
