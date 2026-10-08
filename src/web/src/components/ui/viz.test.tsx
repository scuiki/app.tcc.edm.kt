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
    // A faixa sem aluno é um traço, sem altura calculada
    expect(bars[9]).toHaveClass('is-zero')
    expect(bars[9]).not.toHaveAttribute('style')
    fireEvent.mouseEnter(bars[1])
    expect(screen.getByRole('tooltip')).toHaveTextContent('10 a 20%, 83 alunos')
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
            <SortableHeader label="Taxa de acerto" direction="desc" onSort={onSort} />
            <SortableHeader label="Execuções" direction={null} onSort={onSort} />
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

  it('keeps the marker out of the button and shows the whole label on hover', () => {
    render(
      <table>
        <thead>
          <tr>
            <SortableHeader
              label="Erros de compilação por execução"
              direction={null}
              onSort={() => {}}
              leading={<span role="img" aria-label="Dado estimado" />}
            />
          </tr>
        </thead>
      </table>,
    )
    const button = screen.getByRole('button', { name: 'Erros de compilação por execução' })
    expect(button).not.toContainElement(screen.getByRole('img', { name: 'Dado estimado' }))
    fireEvent.mouseEnter(screen.getByText('Erros de compilação por execução'))
    expect(screen.getByRole('tooltip')).toHaveTextContent('Erros de compilação por execução')
  })
})
