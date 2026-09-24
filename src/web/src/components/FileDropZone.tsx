import { useState, type DragEvent } from 'react'
import { CloudUpload } from 'lucide-react'

import './FileDropZone.css'

interface FileDropZoneProps {
  onFile: (file: File) => void
  title: string
  hint: string
  // O que é aceito, como o formato e o tamanho máximo
  detail?: string
  accept?: string
  disabled?: boolean
}

// Arrastar ou clicar, e o input de arquivo real por baixo para o teclado e o leitor de tela
export function FileDropZone({ onFile, title, hint, detail, accept, disabled }: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  function handleDragOver(event: DragEvent) {
    event.preventDefault()
    if (!disabled) setIsDragging(true)
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files[0]
    if (file && !disabled) onFile(file)
  }

  return (
    <label
      className={`dropzone${isDragging ? ' dropzone--dragging' : ''}${disabled ? ' dropzone--disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <input
        type="file"
        className="visually-hidden"
        accept={accept}
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0]
          // Limpa o input, para escolher o mesmo arquivo de novo disparar outra vez
          event.target.value = ''
          if (file) onFile(file)
        }}
      />
      <CloudUpload className="dropzone__icon" size={24} aria-hidden="true" />
      <span className="dropzone__title">{isDragging ? 'Solte para enviar' : title}</span>
      <span className="dropzone__hint">{hint}</span>
      {detail ? <span className="dropzone__detail">{detail}</span> : null}
    </label>
  )
}
