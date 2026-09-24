import { createEvent, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { FileDropZone } from './FileDropZone'

const FILE = new File(['conteúdo'], 'pacote.zip', { type: 'application/zip' })

function renderZone(overrides: Partial<Parameters<typeof FileDropZone>[0]> = {}) {
  const onFile = vi.fn()
  render(
    <FileDropZone
      onFile={onFile}
      title="Arraste o arquivo .zip aqui"
      hint="ou clique para escolher no computador"
      detail="até 512 MB"
      {...overrides}
    />,
  )
  return { onFile, input: screen.getByLabelText(/Arraste o arquivo/) as HTMLInputElement }
}

// O jsdom não monta o dataTransfer, então o evento recebe um com os arquivos
function drop(target: Element, files: File[]) {
  const event = createEvent.drop(target)
  Object.defineProperty(event, 'dataTransfer', { value: { files } })
  fireEvent(target, event)
}

describe('FileDropZone', () => {
  it('hands over the file picked with the real file input', () => {
    const { onFile, input } = renderZone()
    fireEvent.change(input, { target: { files: [FILE] } })
    expect(onFile).toHaveBeenCalledWith(FILE)
  })

  it('hands over a dropped file', () => {
    const { onFile, input } = renderZone()
    drop(input.closest('label')!, [FILE])
    expect(onFile).toHaveBeenCalledWith(FILE)
  })

  it('asks to drop while a file is over the area', () => {
    const { input } = renderZone()
    fireEvent.dragOver(input.closest('label')!)
    expect(screen.getByText('Solte para enviar')).toBeInTheDocument()
    fireEvent.dragLeave(input.closest('label')!)
    expect(screen.getByText('Arraste o arquivo .zip aqui')).toBeInTheDocument()
  })

  it('ignores a drop and disables the input when disabled', () => {
    const { onFile, input } = renderZone({ disabled: true })
    expect(input).toBeDisabled()
    drop(input.closest('label')!, [FILE])
    expect(onFile).not.toHaveBeenCalled()
  })
})
