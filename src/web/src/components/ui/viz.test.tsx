import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Histogram } from './Histogram'
import { InfoHint } from './InfoHint'
import { RatioBar } from './RatioBar'
import { SortableHeader } from './SortableHeader'

describe('RatioBar', () => {
  it('names the value for the screen reader and draws it on the whole scale', () => {
    render(<RatioBar value={0.124} tone="observed" label="Taxa de acerto" />)
    const bar = screen.getByRole('img', { name: 'Taxa de acerto 12%' })
    expect(bar.querySelector('.ratio-bar__fill')).toHaveStyle({ width: '12.4%' })
  })

  it('never draws past the scale', () => {
    render(<RatioBar value={1.4} tone="predicted" label="Domínio" />)
    expect(screen.getByRole('img').querySelector('.ratio-bar__fill')).toHaveStyle({ width: '100%' })
  })
})

describe('Histogram', () => {
  it('draws one bar per bin, the tallest at full height, and lists the counts as a table', () => {
    const bins = [11, 83, 79, 93, 60, 19, 8, 17, 14, 0]
    render(<Histogram bins={bins} unit="alunos" label="Distribuição dos alunos" />)
    const figure = screen.getByRole('figure', { name: 'Distribuição dos alunos' })
    const bars = figure.querySelectorAll('.histogram__bar')
    expect(bars).toHaveLength(10)
    expect(bars[3]).toHaveStyle({ height: '100%' })
    fireEvent.mouseEnter(bars[1])
    expect(screen.getByRole('tooltip')).toHaveTextContent('83 alunos entre 10% e 20%')
    expect(screen.getByRole('row', { name: /90% a 100%/ })).toHaveTextContent('0')
  })
})

describe('InfoHint', () => {
  it('carries the explanation as its name', () => {
    render(<InfoHint text="Chance prevista de acertar" />)
    expect(screen.getByRole('button', { name: 'Chance prevista de acertar' })).toBeInTheDocument()
  })
})

describe('SortableHeader', () => {
  it('exposes the direction on the th and sorts on click', () => {
    const onSort = vi.fn()
    render(
      <table>
        <thead>
          <tr>
            <SortableHeader direction="desc" onSort={onSort}>
              Taxa de acerto
            </SortableHeader>
            <SortableHeader direction={null} onSort={onSort}>
              Execuções
            </SortableHeader>
          </tr>
        </thead>
      </table>,
    )
    const [active, inactive] = screen.getAllByRole('columnheader')
    expect(active).toHaveAttribute('aria-sort', 'descending')
    expect(inactive).toHaveAttribute('aria-sort', 'none')
    fireEvent.click(screen.getByRole('button', { name: 'Execuções' }))
    expect(onSort).toHaveBeenCalledTimes(1)
  })
})
