import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Breadcrumb } from './Breadcrumb'

describe('Breadcrumb', () => {
  it('links the steps that have an address and marks only the last one as the current place', () => {
    render(
      <Breadcrumb
        items={[
          { label: 'Turmas', href: '/classrooms' },
          { label: 'CSEDM Spring 2019', href: '/classrooms/1' },
          { label: 'Assignment 439' },
          { label: 'Análise' },
        ]}
      />,
    )
    const path = screen.getByRole('navigation', { name: 'Caminho' })
    expect(screen.getByRole('link', { name: 'Turmas' })).toHaveAttribute('href', '#/classrooms')
    expect(screen.getByRole('link', { name: 'CSEDM Spring 2019' })).toHaveAttribute(
      'href',
      '#/classrooms/1',
    )
    // O exercício não tem tela própria, então é texto, e não o lugar atual
    expect(screen.queryByRole('link', { name: 'Assignment 439' })).not.toBeInTheDocument()
    expect(screen.getByText('Assignment 439')).not.toHaveAttribute('aria-current')
    expect(screen.getByText('Análise')).toHaveAttribute('aria-current', 'page')
    expect(path).toHaveTextContent('Turmas›CSEDM Spring 2019›Assignment 439›Análise')
  })
})
