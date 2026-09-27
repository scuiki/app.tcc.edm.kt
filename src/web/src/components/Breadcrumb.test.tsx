import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Breadcrumb } from './Breadcrumb'

describe('Breadcrumb', () => {
  it('links every step but the current one, and shows the aside after the path', () => {
    render(
      <Breadcrumb
        items={[
          { label: 'Turmas', href: '/classrooms' },
          { label: 'CSEDM Spring 2019', href: '/classrooms/1' },
          { label: 'Análise' },
        ]}
        aside={<span>Modelo treinado</span>}
      />,
    )
    const path = screen.getByRole('navigation', { name: 'Caminho' })
    expect(screen.getByRole('link', { name: 'Turmas' })).toHaveAttribute('href', '#/classrooms')
    expect(screen.getByRole('link', { name: 'CSEDM Spring 2019' })).toHaveAttribute(
      'href',
      '#/classrooms/1',
    )
    expect(screen.queryByRole('link', { name: 'Análise' })).not.toBeInTheDocument()
    expect(screen.getByText('Análise')).toHaveAttribute('aria-current', 'page')
    expect(path).toHaveTextContent('Modelo treinado')
  })
})
