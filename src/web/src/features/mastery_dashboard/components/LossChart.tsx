import { CategoryScale, Chart, LinearScale, LineElement, PointElement } from 'chart.js'
import { Line } from 'react-chartjs-2'

import { formatNumber } from '../../../lib/format'
import type { TrainingLossHistory } from '../../model_training/api/training'
import './LossChart.css'

Chart.register(CategoryScale, LinearScale, LineElement, PointElement)

type Epoch = TrainingLossHistory['epochs'][number]

// O canvas não lê variáveis do CSS, então a cor vem do token lido na hora
function tokenColor(name: string, fallback: string) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

// A perda de treino por época, que o professor vê cair enquanto espera
export function LossChart({
  epochs,
  totalEpochs,
}: {
  epochs: Epoch[]
  totalEpochs: number | null
}) {
  const line = tokenColor('--color-bar-predicted', '#3b7be0')
  const grid = tokenColor('--color-rule', '#e2e8f0')
  const text = tokenColor('--color-text-muted', '#64748b')
  // O eixo x já nasce com todas as épocas, para a linha crescer da esquerda sem reescalar
  const total = Math.max(totalEpochs ?? 0, epochs.length)
  const labels = Array.from({ length: total }, (_, index) => String(index + 1))
  const values = labels.map((_, index) => epochs[index]?.train_loss ?? null)
  return (
    <figure className="loss-chart" aria-label="Perda de treino por época">
      <div className="loss-chart__canvas">
        <Line
          data={{
            labels,
            datasets: [
              {
                data: values,
                borderColor: line,
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.2,
              },
            ],
          }}
          options={{
            animation: false,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
              x: {
                title: { display: true, text: 'Época', color: text },
                ticks: { color: text, maxTicksLimit: 9 },
                grid: { display: false },
              },
              y: {
                title: { display: true, text: 'Perda', color: text },
                ticks: { color: text, maxTicksLimit: 5 },
                grid: { color: grid },
              },
            },
          }}
        />
      </div>
      <div className="visually-hidden">
        <table>
          <tbody>
            {epochs.map((epoch) => (
              <tr key={epoch.epoch}>
                <th scope="row">Época {epoch.epoch}</th>
                <td>{formatNumber(epoch.train_loss, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  )
}
