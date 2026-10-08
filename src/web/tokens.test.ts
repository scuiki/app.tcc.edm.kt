import { readdirSync, readFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Todo token lido está declarado no tokens.css, e nenhuma cor literal mora fora dele

const SRC = resolve(import.meta.dirname, 'src')
const TOKENS = join(SRC, 'styles', 'tokens.css')

// Os testes e o schema gerado ficam de fora, porque não desenham nada
function styleFiles(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const path = join(folder, entry.name)
    if (entry.isDirectory()) return styleFiles(path)
    const isSource = /\.(css|tsx?)$/.test(entry.name)
    const isExcluded = /\.test\./.test(entry.name) || entry.name === 'schema.d.ts'
    return isSource && !isExcluded ? [path] : []
  })
}

const FILES = styleFiles(SRC).map((file) => ({
  path: relative(SRC, file),
  text: readFileSync(file, 'utf8'),
}))

const DECLARED = new Set(
  [...readFileSync(TOKENS, 'utf8').matchAll(/^\s*(--[\w-]+)\s*:/gm)].map((match) => match[1]),
)

// O var(--x) do CSS e o tokenColor('--x') do gráfico, que lê o token em tempo de execução
const READS = [/var\(\s*(--[\w-]+)/g, /tokenColor\(\s*['"](--[\w-]+)['"]/g]
const HEX_COLOR = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b/
const FUNCTION_COLOR = /\b(?:rgba?|hsla?)\(/

describe('design tokens', () => {
  it('finds the style files and the declared tokens, so the checks never pass on empty', () => {
    expect(FILES.length).toBeGreaterThan(0)
    expect(DECLARED.size).toBeGreaterThan(0)
  })

  it('declares in tokens.css every token that a style or a chart reads', () => {
    const missing = FILES.flatMap(({ path, text }) =>
      READS.flatMap((read) => [...text.matchAll(read)])
        .filter((match) => !DECLARED.has(match[1]))
        .map((match) => `${path} lê ${match[1]}`),
    )
    expect(missing).toEqual([])
  })

  it('keeps literal colors inside tokens.css', () => {
    const literals = FILES.filter(({ path }) => path !== relative(SRC, TOKENS)).flatMap(
      ({ path, text }) =>
        text
          .split('\n')
          .map((line, index) => ({ line, row: index + 1 }))
          .filter(({ line }) => HEX_COLOR.test(line) || FUNCTION_COLOR.test(line))
          .map(({ line, row }) => `${path}:${row} ${line.trim()}`),
    )
    expect(literals).toEqual([])
  })
})
