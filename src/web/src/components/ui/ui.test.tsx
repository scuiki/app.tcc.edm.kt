import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { describe, expect, it, vi } from 'vitest'

import { Button, IconButton } from './Button'
import { Dialog, DialogBody } from './Dialog'
import { TextField } from './TextField'

describe('Button and IconButton', () => {
  it('defaults to type button, so it never submits a form by accident', () => {
    render(<Button variant="primary">Criar</Button>)
    expect(screen.getByRole('button', { name: 'Criar' })).toHaveAttribute('type', 'button')
  })

  it('names the icon-only button by its label', () => {
    render(<IconButton icon={Trash2} label="Excluir Turma A" />)
    expect(screen.getByRole('button', { name: 'Excluir Turma A' })).toBeInTheDocument()
  })
})

// Um campo controlado dentro do diálogo, para provar que ele nasce limpo a cada abertura
function DialogWithField() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Abrir
      </button>
      <Dialog open={open} onClose={() => setOpen(false)} title="Nova turma">
        <DialogBody>
          <FieldWithState />
          <button type="button" onClick={() => setOpen(false)}>
            Cancelar
          </button>
        </DialogBody>
      </Dialog>
    </>
  )
}

function FieldWithState() {
  const [name, setName] = useState('')
  return <TextField label="Nome" value={name} onChange={(e) => setName(e.target.value)} />
}

describe('Dialog', () => {
  it('renders nothing inside while closed, and the titled content when open', () => {
    const { rerender } = render(
      <Dialog open={false} onClose={() => {}} title="Nova turma">
        <p>Conteúdo</p>
      </Dialog>,
    )
    expect(screen.queryByText('Conteúdo')).not.toBeInTheDocument()

    rerender(
      <Dialog open onClose={() => {}} title="Nova turma">
        <p>Conteúdo</p>
      </Dialog>,
    )
    expect(screen.getByRole('dialog', { name: 'Nova turma' })).toBeInTheDocument()
    expect(screen.getByText('Conteúdo')).toBeInTheDocument()
  })

  it('becomes an alertdialog in the danger tone', () => {
    render(
      <Dialog open onClose={() => {}} title="Excluir Turma A?" tone="danger">
        <p>Não dá para desfazer.</p>
      </Dialog>,
    )
    expect(screen.getByRole('alertdialog', { name: 'Excluir Turma A?' })).toBeInTheDocument()
  })

  it('calls onClose when the native dialog closes, as on Esc', () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="Nova turma">
        <p>Conteúdo</p>
      </Dialog>,
    )
    fireEvent(screen.getByRole('dialog'), new Event('close'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('opens with a clean field after cancelling a half-typed form', () => {
    render(<DialogWithField />)
    fireEvent.click(screen.getByRole('button', { name: 'Abrir' }))
    fireEvent.change(screen.getByLabelText('Nome'), { target: { value: 'Turma A' } })
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Abrir' }))
    expect(screen.getByLabelText('Nome')).toHaveValue('')
  })
})

describe('TextField', () => {
  it('shows the hint and marks a required field with an asterisk', () => {
    render(<TextField label="Nome" hint="Você importa os dados depois." required />)
    expect(screen.getByText('*')).toBeInTheDocument()
    expect(screen.getByLabelText(/Nome/)).toHaveAccessibleDescription(
      'Você importa os dados depois.',
    )
  })

  it('replaces the hint by the error and flags the input as invalid', () => {
    render(<TextField label="Nome" hint="Ajuda" error="Você já tem uma turma com esse nome." />)
    const input = screen.getByLabelText('Nome')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription('Você já tem uma turma com esse nome.')
    expect(screen.queryByText('Ajuda')).not.toBeInTheDocument()
  })
})
