import { readdirSync, readFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// As fronteiras entre as camadas do frontend, conferidas pelo caminho real de cada import

const SRC = resolve(import.meta.dirname, 'src')

function sourceFiles(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const path = join(folder, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    const isSource = /\.tsx?$/.test(entry.name) && !entry.name.endsWith('.d.ts')
    return isSource ? [path] : []
  })
}

// Cada import relativo vira o caminho dentro de src, como features/classrooms/api/useClassrooms
function importsOf(file: string): string[] {
  const text = readFileSync(file, 'utf8')
  const specifiers = [...text.matchAll(/(?:from|import)\s+['"](\.{1,2}\/[^'"]+)['"]/g)]
  return specifiers.map((match) => relative(SRC, resolve(dirname(file), match[1])))
}

const FILES = sourceFiles(SRC).map((file) => ({
  path: relative(SRC, file),
  imports: importsOf(file),
}))

function violations(isForbidden: (from: string, to: string) => boolean): string[] {
  return FILES.flatMap(({ path, imports }) =>
    imports.filter((to) => isForbidden(path, to)).map((to) => `${path} importa ${to}`),
  )
}

const layer = (path: string) => path.split('/')[0]
const feature = (path: string) => path.split('/')[1]
const featureRole = (path: string) => path.split('/')[2]

describe('frontend architecture', () => {
  it('components know no feature and no app code', () => {
    const found = violations(
      (from, to) => layer(from) === 'components' && ['features', 'app'].includes(layer(to)),
    )
    expect(found).toEqual([])
  })

  it('lib and http depend only on lib and http', () => {
    const found = violations(
      (from, to) => ['lib', 'http'].includes(layer(from)) && !['lib', 'http'].includes(layer(to)),
    )
    expect(found).toEqual([])
  })

  it('a feature never imports app code', () => {
    const found = violations((from, to) => layer(from) === 'features' && layer(to) === 'app')
    expect(found).toEqual([])
  })

  it('a feature imports only the api folder of another feature', () => {
    const found = violations(
      (from, to) =>
        layer(from) === 'features' &&
        layer(to) === 'features' &&
        feature(from) !== feature(to) &&
        featureRole(to) !== 'api',
    )
    expect(found).toEqual([])
  })
})
