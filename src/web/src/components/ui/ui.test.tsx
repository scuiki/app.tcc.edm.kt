import { fireEvent, render, screen, within } from '@testing-library/react'
import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'

import { Button, IconButton } from './Button'
import { ColumnHeader, ColumnLabel, DataTable } from './DataTable'
import { Dialog, DialogBody, DialogFooter } from './Dialog'
import dialogStyles from './Dialog.css?raw'
import { SelectField } from './SelectField'
import { Tabs } from './Tabs'
import { TextField } from './TextField'

describe('DataTable', () => {
  it('names the table and gives the column the marker, the label and the hint', () => {
    render(
      <DataTable label="Turmas">
        <thead>
          <tr>
            <ColumnHeader
              label="Distribuição"
              leading={<span role="img" aria-label="Dado estimado" />}
              hint={<button type="button" aria-label="Como ler" />}
            />
          </tr>
        </thead>
      </DataTable>,
    )
    const header = screen.getByRole('columnheader', { name: /Distribuição/ })
    expect(screen.getByRole('table', { name: 'Turmas' })).toContainElement(header)
    expect(header).toContainElement(screen.getByRole('img', { name: 'Dado estimado' }))
    expect(header).toContainElement(screen.getByRole('button', { name: 'Como ler' }))
  })

  it('keeps the plain table with the automatic layout, no pinned column and no scroll mark', () => {
    render(
      <DataTable label="Turmas">
        <tbody>
          <tr>
            <td>Turma A</td>
          </tr>
        </tbody>
      </DataTable>,
    )
    const table = screen.getByRole('table', { name: 'Turmas' })
    expect(table).toHaveAttribute('class', 'data-table')
    const scroller = table.parentElement as HTMLElement
    Object.defineProperty(scroller, 'scrollLeft', { configurable: true, value: 40 })
    fireEvent.scroll(scroller)
    expect(scroller).not.toHaveClass('is-scrolled')
  })

  it('fixes the layout and pins the first column when asked', () => {
    render(
      <DataTable label="Conceitos por problema" fixedLayout stickyFirstColumn>
        <tbody>
          <tr>
            <td>Laços</td>
          </tr>
        </tbody>
      </DataTable>,
    )
    expect(screen.getByRole('table')).toHaveClass(
      'data-table',
      'data-table--fixed',
      'data-table--sticky',
    )
  })

  it('marks the pinned column only while something is scrolled under it', () => {
    render(
      <DataTable label="Conceitos por problema" stickyFirstColumn>
        <tbody>
          <tr>
            <td>Laços</td>
          </tr>
        </tbody>
      </DataTable>,
    )
    const scroller = screen.getByRole('table').parentElement as HTMLElement
    expect(scroller).not.toHaveClass('is-scrolled')

    Object.defineProperty(scroller, 'scrollLeft', { configurable: true, value: 40 })
    fireEvent.scroll(scroller)
    expect(scroller).toHaveClass('data-table__scroll', 'is-scrolled')

    Object.defineProperty(scroller, 'scrollLeft', { configurable: true, value: 0 })
    fireEvent.scroll(scroller)
    expect(scroller).not.toHaveClass('is-scrolled')
  })

  it('lets a header cell take the class that aligns it to the left', () => {
    render(
      <DataTable label="Problemas">
        <thead>
          <tr>
            <ColumnHeader label="Enunciado" className="data-table__left" />
          </tr>
        </thead>
      </DataTable>,
    )
    expect(screen.getByRole('columnheader', { name: 'Enunciado' })).toHaveClass('data-table__left')
  })
})

describe('ColumnLabel', () => {
  it('truncates at the 150px cap by default, with the whole text on hover', () => {
    render(<ColumnLabel text="Tentativas até completar" />)
    const label = screen.getByText('Tentativas até completar')
    expect(label).toHaveClass('data-table__label')
    expect(label).not.toHaveClass('data-table__label--fill')
    fireEvent.mouseEnter(label)
    expect(screen.getByRole('tooltip')).toHaveTextContent('Tentativas até completar')
  })

  it('drops the cap and takes the width of the cell in the fill variant', () => {
    render(<ColumnLabel text="Uso de operadores lógicos em condições" fillCell />)
    const label = screen.getByText('Uso de operadores lógicos em condições')
    expect(label).toHaveClass('data-table__label', 'data-table__label--fill')
    fireEvent.mouseEnter(label)
    expect(screen.getByRole('tooltip')).toHaveTextContent('Uso de operadores lógicos em condições')
  })
})

describe('Tabs', () => {
  const items = [
    { key: 'matrix', label: 'Conceitos por problema' },
    { key: 'problems', label: 'Problemas' },
  ]

  it('keeps the actions and the leading label out of the tablist', () => {
    render(
      <Tabs
        items={items}
        active="matrix"
        onChange={() => {}}
        label="O que revisar"
        leading="Problema"
        actions={
          <button type="button" disabled>
            Aprovar conceitos
          </button>
        }
      />,
    )
    const tablist = screen.getByRole('tablist', { name: 'O que revisar' })
    expect(within(tablist).getAllByRole('tab')).toHaveLength(2)
    expect(within(tablist).queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Aprovar conceitos' })).toBeInTheDocument()

    const leading = screen.getByText('Problema')
    expect(tablist).not.toContainElement(leading)
    expect(leading).toHaveAttribute('aria-hidden', 'true')
  })

  it('names a tab by its ariaLabel and reports the chosen key', () => {
    const onChange = vi.fn()
    render(
      <Tabs
        items={[
          { key: '3', label: '3', ariaLabel: 'Problema 3' },
          { key: '12', label: '12', ariaLabel: 'Problema 12' },
        ]}
        active="3"
        onChange={onChange}
        label="Problemas em que o conceito aparece"
      />,
    )
    expect(screen.getByRole('tab', { name: 'Problema 3' })).toHaveAttribute('aria-selected', 'true')
    fireEvent.click(screen.getByRole('tab', { name: 'Problema 12' }))
    expect(onChange).toHaveBeenCalledWith('12')
  })

  it('shows only the identifier in the data font in the identifier variant', () => {
    render(
      <Tabs
        variant="identifier"
        items={[{ key: '232', label: '232', ariaLabel: 'Problema 232' }]}
        active="232"
        onChange={() => {}}
        label="Problemas em que o conceito aparece"
      />,
    )
    const tab = screen.getByRole('tab', { name: 'Problema 232' })
    expect(tab).toHaveTextContent(/^232$/)
    expect(within(tab).getByText('232')).toHaveClass('num')
    expect(tab.closest('.tabs')).toHaveClass('tabs', 'tabs--identifier')
  })

  it('keeps the label of the default tabs in the interface font', () => {
    render(<Tabs items={items} active="matrix" onChange={() => {}} label="O que revisar" />)
    expect(screen.getByText('Problemas')).not.toHaveClass('num')
    expect(screen.getByRole('tablist').parentElement).toHaveAttribute('class', 'tabs')
  })
})

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
  // O jsdom aplica as regras de uma folha de estilo do documento, e o teste lê o CSS do Dialog
  beforeAll(() => {
    const style = document.createElement('style')
    style.id = 'dialog-styles'
    style.textContent = dialogStyles
    document.head.append(style)
  })

  afterAll(() => {
    document.getElementById('dialog-styles')?.remove()
  })

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

  it('keeps open on Esc when it is not dismissible', () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="Extraindo conceitos" dismissible={false}>
        <p>Conteúdo</p>
      </Dialog>,
    )
    const cancel = new Event('cancel', { cancelable: true })
    fireEvent(screen.getByRole('dialog'), cancel)
    expect(cancel.defaultPrevented).toBe(true)

    fireEvent(screen.getByRole('dialog'), new Event('close'))
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog')).toHaveAttribute('open')
  })

  it('stays 440px wide by default and takes 760px in the wide size', () => {
    const { rerender } = render(
      <Dialog open onClose={() => {}} title="Nova turma">
        <p>Conteúdo</p>
      </Dialog>,
    )
    expect(getComputedStyle(screen.getByRole('dialog')).width).toBe('440px')

    rerender(
      <Dialog open onClose={() => {}} title="Laços" size="wide">
        <p>Conteúdo</p>
      </Dialog>,
    )
    expect(screen.getByRole('dialog')).toHaveClass('dialog', 'dialog--wide')
    expect(getComputedStyle(screen.getByRole('dialog')).width).toBe('760px')
  })

  it('keeps the marker after the title out of the accessible name, and shows the facts', () => {
    render(
      <Dialog
        open
        onClose={() => {}}
        title="Laços"
        size="wide"
        titleAside={<span role="img" aria-label="Gerado pelo modelo de linguagem" />}
        facts={<p>aparece em 2 de 10 problemas</p>}
      >
        <p>Conteúdo</p>
      </Dialog>,
    )
    const dialog = screen.getByRole('dialog', { name: 'Laços' })
    const heading = within(dialog).getByRole('heading', { level: 2, name: 'Laços' })
    const marker = within(dialog).getByRole('img', { name: 'Gerado pelo modelo de linguagem' })
    expect(heading).not.toContainElement(marker)
    expect(heading.nextElementSibling).toBe(marker)
    expect(within(dialog).getByText('aparece em 2 de 10 problemas')).toBeInTheDocument()
  })

  it('never grows past the window, with the header and the footer pinned and the body scrolling', () => {
    render(
      <Dialog open onClose={() => {}} title="Laços" size="wide">
        <DialogBody>
          <p>Um painel mais alto que a janela</p>
        </DialogBody>
        <DialogFooter>
          <button type="button">Fechar</button>
        </DialogFooter>
      </Dialog>,
    )
    const dialog = screen.getByRole('dialog')
    expect(getComputedStyle(dialog).maxHeight).toBe('calc(100vh - 48px)')
    expect(getComputedStyle(dialog).display).toBe('flex')
    expect(getComputedStyle(dialog).overflow).toBe('hidden')
    const header = dialog.querySelector('.dialog__header')!
    const body = dialog.querySelector('.dialog__body')!
    const footer = dialog.querySelector('.dialog__footer')!
    expect(getComputedStyle(header).flexShrink).toBe('0')
    expect(getComputedStyle(footer).flexShrink).toBe('0')
    expect(getComputedStyle(body).overflow).toBe('auto')
    expect(getComputedStyle(body).minHeight).toBe('0')
  })

  it('lets the body of a form scroll too, with the form passing the column on', () => {
    render(
      <Dialog open onClose={() => {}} title="Novo conceito">
        <form>
          <DialogBody>
            <p>Nome e problemas</p>
          </DialogBody>
          <DialogFooter>
            <button type="submit">Criar</button>
          </DialogFooter>
        </form>
      </Dialog>,
    )
    const form = screen.getByRole('dialog').querySelector('form')!
    expect(getComputedStyle(form).display).toBe('flex')
    expect(getComputedStyle(form).flexDirection).toBe('column')
    expect(getComputedStyle(form).minHeight).toBe('0')
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

describe('SelectField', () => {
  const options = [
    { value: '1', label: 'Turma A' },
    { value: '2', label: 'Turma B' },
  ]

  it('starts on the placeholder and reports the chosen value', () => {
    const onChange = vi.fn()
    render(
      <SelectField
        label="Turma"
        placeholder="Escolha a turma"
        value=""
        options={options}
        onChange={onChange}
        hint="Ajuda"
      />,
    )
    const select = screen.getByLabelText('Turma')
    expect(select).toHaveDisplayValue('Escolha a turma')
    expect(select).toHaveAccessibleDescription('Ajuda')
    fireEvent.change(select, { target: { value: '2' } })
    expect(onChange).toHaveBeenCalledWith('2')
  })

  it('never offers the placeholder as a choice', () => {
    render(
      <SelectField
        label="Turma"
        placeholder="Escolha a turma"
        value="1"
        options={options}
        onChange={() => {}}
      />,
    )
    expect(screen.getByRole('option', { name: 'Escolha a turma' })).toBeDisabled()
  })
})
