import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { FileCheck } from 'lucide-react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { CodeBlock, type CodeFile } from './CodeBlock'

// O código como o banco guarda, com o fim de linha do Windows, a tabulação e a quebra final
const FIRST = 'public int sum(int a, int b) {\r\n\treturn a + b;\r\n}\r\n'
const SECOND =
  'public int max(int a, int b) {\n\tif (a > b) {\n\t\treturn a;\n\t}\n\treturn b;\n}\n'
const THIRD = 'public int one() {\n\treturn 1;\n}'

function files(): CodeFile<number>[] {
  return [
    { key: 1, label: 'Solução 1', code: FIRST, icon: FileCheck },
    {
      key: 2,
      label: 'Solução 2',
      code: SECOND,
      icon: FileCheck,
      marker: <span role="img" aria-label="Gerado pelo modelo de linguagem" />,
      ariaLabel: 'Solução 2, com o trecho',
    },
    { key: 3, label: 'Solução 3', code: THIRD, icon: FileCheck },
  ]
}

// As linhas do painel aberto, cada uma com o número e o texto
function shownLines() {
  const panel = screen.getByRole('tabpanel')
  const numbers = [...panel.querySelectorAll('.code-block__number')].map((n) => n.textContent)
  const texts = [...panel.querySelectorAll('.code-block__line')].map((line) => line.textContent)
  return { numbers, texts }
}

function highlightedNumbers() {
  const panel = screen.getByRole('tabpanel')
  return [...panel.querySelectorAll('.code-block__number.is-highlighted')].map((n) => n.textContent)
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('CodeBlock', () => {
  it('gives each file a tab in the tablist, named by the label or by its ariaLabel', () => {
    render(<CodeBlock files={files()} label="Soluções do problema 3 que o modelo leu" />)
    const tablist = screen.getByRole('tablist', { name: 'Soluções do problema 3 que o modelo leu' })
    const tabs = within(tablist).getAllByRole('tab')
    expect(tabs).toHaveLength(3)
    expect(tabs[0]).toHaveAccessibleName('Solução 1')
    expect(tabs[2]).toHaveAccessibleName('Solução 3')
    // O marcador fica dentro da aba, mas fora do nome dela
    expect(tabs[1]).toHaveAccessibleName('Solução 2, com o trecho')
    expect(within(tabs[1]).getByRole('img')).toBeInTheDocument()
  })

  it('opens on the first file without an initial one, and draws only the open panel', () => {
    render(<CodeBlock files={files()} label="Soluções" />)
    expect(screen.getByRole('tab', { name: 'Solução 1' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getAllByRole('tabpanel')).toHaveLength(1)
    expect(screen.getByRole('tabpanel')).toHaveAccessibleName('Solução 1')
    expect(screen.getByRole('tabpanel')).toHaveAttribute('tabindex', '0')
  })

  it('splits the Windows line ends, keeps the tabs and drops the empty line after the last break', () => {
    render(<CodeBlock files={files()} label="Soluções" />)
    expect(shownLines()).toEqual({
      numbers: ['1', '2', '3'],
      texts: ['public int sum(int a, int b) {', '\treturn a + b;', '}'],
    })
  })

  it('opens on the initial file with its lines highlighted, numbers included', () => {
    render(
      <CodeBlock
        files={files()}
        label="Soluções"
        initialFile={2}
        highlight={{ file: 2, firstLine: 2, lastLine: 4 }}
      />,
    )
    expect(screen.getByRole('tab', { name: 'Solução 2, com o trecho' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(shownLines().numbers).toEqual(['1', '2', '3', '4', '5', '6'])
    expect(highlightedNumbers()).toEqual(['2', '3', '4'])
    const panel = screen.getByRole('tabpanel')
    expect([...panel.querySelectorAll('.code-block__line.is-highlighted')]).toHaveLength(3)
  })

  it('opens on the first file when the initial one is not there', () => {
    render(<CodeBlock files={files()} label="Soluções" initialFile={9} />)
    expect(screen.getByRole('tab', { name: 'Solução 1' })).toHaveAttribute('aria-selected', 'true')
  })

  it('switches the panel on a tab click, and the highlight stays with its own file', () => {
    render(
      <CodeBlock
        files={files()}
        label="Soluções"
        initialFile={2}
        highlight={{ file: 2, firstLine: 2, lastLine: 4 }}
      />,
    )
    fireEvent.click(screen.getByRole('tab', { name: 'Solução 3' }))
    expect(screen.getByRole('tab', { name: 'Solução 3' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Solução 2, com o trecho' })).toHaveAttribute(
      'aria-selected',
      'false',
    )
    expect(shownLines().texts).toEqual(['public int one() {', '\treturn 1;', '}'])
    expect(highlightedNumbers()).toEqual([])

    fireEvent.click(screen.getByRole('tab', { name: 'Solução 2, com o trecho' }))
    expect(highlightedNumbers()).toEqual(['2', '3', '4'])
  })

  it('scrolls only the code, down to the first highlighted line, when it shows the highlight', async () => {
    // Sem layout no jsdom, o painel ganha 100px de altura, 300px de código e a linha 4 a 200px
    vi.spyOn(Element.prototype, 'clientHeight', 'get').mockReturnValue(100)
    vi.spyOn(Element.prototype, 'scrollHeight', 'get').mockReturnValue(300)
    vi.spyOn(HTMLElement.prototype, 'offsetTop', 'get').mockImplementation(function (
      this: HTMLElement,
    ) {
      return this.classList.contains('is-highlighted') ? 200 : 0
    })
    const scrollTop = vi.spyOn(Element.prototype, 'scrollTop', 'set')

    render(
      <CodeBlock
        files={files()}
        label="Soluções"
        initialFile={2}
        highlight={{ file: 2, firstLine: 4, lastLine: 5 }}
      />,
    )
    const panel = screen.getByRole('tabpanel')
    await waitFor(() => expect(scrollTop).toHaveBeenCalledWith(170))
    expect(scrollTop.mock.contexts).toEqual([panel])

    // A aba sem destaque não rola, e a volta à aba do trecho rola de novo
    scrollTop.mockClear()
    fireEvent.click(screen.getByRole('tab', { name: 'Solução 1' }))
    fireEvent.click(screen.getByRole('tab', { name: 'Solução 2, com o trecho' }))
    await waitFor(() => expect(scrollTop).toHaveBeenCalledWith(170))
    expect(scrollTop.mock.contexts).toEqual([screen.getByRole('tabpanel')])
  })

  it('cancels the scroll when it leaves before the next frame', async () => {
    vi.spyOn(Element.prototype, 'clientHeight', 'get').mockReturnValue(100)
    vi.spyOn(Element.prototype, 'scrollHeight', 'get').mockReturnValue(300)
    const scrollTop = vi.spyOn(Element.prototype, 'scrollTop', 'set')
    const frame = vi.spyOn(window, 'requestAnimationFrame')
    const cancel = vi.spyOn(window, 'cancelAnimationFrame')

    const { unmount } = render(
      <CodeBlock
        files={files()}
        label="Soluções"
        initialFile={2}
        highlight={{ file: 2, firstLine: 4, lastLine: 5 }}
      />,
    )
    expect(frame).toHaveBeenCalledOnce()
    unmount()
    expect(cancel).toHaveBeenCalledWith(frame.mock.results[0].value)
    await new Promise((resolve) => requestAnimationFrame(resolve))
    await new Promise((resolve) => requestAnimationFrame(resolve))
    expect(scrollTop).not.toHaveBeenCalled()
  })

  it('does not scroll when the code fits in the block', async () => {
    vi.spyOn(Element.prototype, 'clientHeight', 'get').mockReturnValue(300)
    vi.spyOn(Element.prototype, 'scrollHeight', 'get').mockReturnValue(300)
    const scrollTop = vi.spyOn(Element.prototype, 'scrollTop', 'set')
    const frame = vi.spyOn(window, 'requestAnimationFrame')

    render(
      <CodeBlock
        files={files()}
        label="Soluções"
        initialFile={2}
        highlight={{ file: 2, firstLine: 4, lastLine: 5 }}
      />,
    )
    await waitFor(() => expect(frame).toHaveBeenCalled())
    await new Promise((resolve) => requestAnimationFrame(resolve))
    expect(scrollTop).not.toHaveBeenCalled()
  })
})
