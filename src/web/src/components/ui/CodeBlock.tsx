import { Fragment, useEffect, useId, useRef, useState, type ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

import './CodeBlock.css'

type CodeFileKey = string | number

export interface CodeFile<K extends CodeFileKey> {
  key: K
  label: string
  code: string
  icon?: LucideIcon
  // Depois do rótulo, como as estrelas na aba da solução que tem o trecho
  marker?: ReactNode
  // O nome da aba para o leitor de tela, para o marcador não entrar nele
  ariaLabel?: string
}

// As linhas destacadas de um arquivo, contadas a partir de 1, com a última incluída
export interface CodeHighlight<K extends CodeFileKey> {
  file: K
  firstLine: number
  lastLine: number
}

interface CodeBlockProps<K extends CodeFileKey> {
  files: CodeFile<K>[]
  // O nome da fileira de abas para o leitor de tela
  label: string
  // Sem ela, ou com uma que não existe, o bloco abre no primeiro arquivo
  initialFile?: K
  highlight?: CodeHighlight<K> | null
}

// O código com as abas presas ao topo, a numeração das linhas e o destaque, rolando por dentro
export function CodeBlock<K extends CodeFileKey>({
  files,
  label,
  initialFile,
  highlight,
}: CodeBlockProps<K>) {
  const id = useId()
  const [selected, setSelected] = useState(initialFile)
  const panelRef = useRef<HTMLDivElement>(null)
  const active = files.find((file) => file.key === selected) ?? files[0]
  const activeKey = active?.key
  const shownHighlight = highlight != null && highlight.file === activeKey ? highlight : null
  const hasHighlight = shownHighlight != null

  // Rolar um elemento é falar com o DOM, e na primeira abertura o diálogo ainda está fechado agora
  useEffect(() => {
    const panel = panelRef.current
    if (!panel || !hasHighlight) return
    const frame = requestAnimationFrame(() => revealFirstHighlightedLine(panel))
    return () => cancelAnimationFrame(frame)
  }, [activeKey, hasHighlight])

  if (!active) return null
  const tabId = (key: K) => `${id}-tab-${key}`
  const panelId = `${id}-panel`
  const isHighlighted = (line: number) =>
    shownHighlight != null && line >= shownHighlight.firstLine && line <= shownHighlight.lastLine

  return (
    <div className="code-block">
      <div role="tablist" aria-label={label} className="code-block__tabs">
        {files.map(({ key, label: text, icon: Icon, marker, ariaLabel }) => (
          <button
            key={key}
            type="button"
            role="tab"
            id={tabId(key)}
            aria-selected={key === activeKey}
            aria-controls={key === activeKey ? panelId : undefined}
            aria-label={ariaLabel}
            className="code-block__tab"
            onClick={() => setSelected(key)}
          >
            {Icon ? <Icon size={14} aria-hidden="true" /> : null}
            <span>{text}</span>
            {marker}
          </button>
        ))}
      </div>
      <div
        // Um elemento novo por arquivo, para cada um abrir no topo da própria rolagem
        key={active.key}
        ref={panelRef}
        role="tabpanel"
        id={panelId}
        aria-labelledby={tabId(active.key)}
        tabIndex={0}
        className="code-block__code"
      >
        {linesOf(active.code).map((text, index) => {
          const line = index + 1
          const modifier = isHighlighted(line) ? ' is-highlighted' : ''
          return (
            <Fragment key={line}>
              <span className={`code-block__number${modifier}`} aria-hidden="true">
                {line}
              </span>
              <span className={`code-block__line${modifier}`}>{text}</span>
            </Fragment>
          )
        })}
      </div>
    </div>
  )
}

// O código guarda o fim de linha de quem o escreveu, e a quebra depois da última linha não conta
function linesOf(code: string): string[] {
  const lines = code.split(/\r?\n/)
  if (lines.length > 1 && lines[lines.length - 1] === '') lines.pop()
  return lines
}

// Rola só o bloco, sem mexer na página, e deixa um pouco de código acima do destaque
function revealFirstHighlightedLine(panel: HTMLElement) {
  const line = panel.querySelector<HTMLElement>('.code-block__line.is-highlighted')
  if (!line || panel.scrollHeight <= panel.clientHeight) return
  panel.scrollTop = Math.max(0, line.offsetTop - panel.clientHeight * 0.3)
}
