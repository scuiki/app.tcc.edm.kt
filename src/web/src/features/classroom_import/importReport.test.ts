import { describe, expect, it } from 'vitest'

import type { ClassroomImportReport, DetectedUpload } from './api/classroomImport'
import {
  checkTitle,
  fatalChecksOf,
  missingTableOf,
  outcomeOf,
  pathInUpload,
  readinessSentence,
  warningsOf,
} from './importReport'

function report(overrides: Partial<ClassroomImportReport> = {}): ClassroomImportReport {
  return {
    has_fatal: false,
    checks: [],
    dataset_summary: {},
    per_assignment: [],
    ...overrides,
  }
}

const UPLOAD: DetectedUpload = {
  classroom_id: 1,
  raw_dir: '/app/data/1/raw/envio',
  main_tables: ['/app/data/1/raw/envio/MainTable.csv'],
  code_snapshots: '/app/data/1/raw/envio/CodeStates/CodeStates.csv',
}

describe('outcomeOf', () => {
  it('is imported without a fatal check', () => {
    expect(outcomeOf(report())).toBe('imported')
  })

  it('is refused with a fatal check', () => {
    const fatal = { check: 'encoding', severity: 'fatal', message: 'x' }
    expect(outcomeOf(report({ has_fatal: true, checks: [fatal] }))).toBe('refused')
  })

  it('is busy when another job holds the lock, even though that check is fatal', () => {
    const busy = { check: 'another_job_running', severity: 'fatal', message: 'x' }
    expect(outcomeOf(report({ has_fatal: true, checks: [busy] }))).toBe('busy')
  })
})

describe('checkTitle', () => {
  it('names a known check in pt-BR', () => {
    expect(checkTitle({ check: 'orphan_codestate', severity: 'warning', message: '' })).toBe(
      'Eventos sem código descartados',
    )
  })

  it('falls back by severity for an unknown check', () => {
    expect(checkTitle({ check: 'new_check', severity: 'fatal', message: '' })).toBe(
      'Uma verificação obrigatória falhou',
    )
    expect(checkTitle({ check: 'new_check', severity: 'warning', message: '' })).toBe(
      'Aviso do processamento',
    )
  })
})

describe('fatalChecksOf and warningsOf', () => {
  it('split the checks by severity, viability counting as a warning', () => {
    const checks = [
      { check: 'encoding', severity: 'fatal', message: '' },
      { check: 'orphan_codestate', severity: 'warning', message: '' },
      { check: 'few_problems', severity: 'viability', message: '' },
    ]
    expect(fatalChecksOf(report({ checks })).map((c) => c.check)).toEqual(['encoding'])
    expect(warningsOf(report({ checks })).map((c) => c.check)).toEqual([
      'orphan_codestate',
      'few_problems',
    ])
  })

  it('leaves out the repeated compile, which is the ProgSnap2 format', () => {
    const checks = [{ check: 'dedup_compile', severity: 'warning', message: '' }]
    expect(warningsOf(report({ checks }))).toEqual([])
  })
})

describe('pathInUpload', () => {
  it('drops the server folder where the package was extracted', () => {
    expect(pathInUpload(UPLOAD.code_snapshots!, UPLOAD)).toBe('CodeStates/CodeStates.csv')
  })
})

describe('missingTableOf', () => {
  it('asks for nothing when both tables came', () => {
    expect(missingTableOf(UPLOAD)).toBeNull()
  })

  it('asks first for the events table, then for the code', () => {
    expect(missingTableOf({ ...UPLOAD, main_tables: [], code_snapshots: null })).toBe('main_table')
    expect(missingTableOf({ ...UPLOAD, code_snapshots: null })).toBe('code_snapshots')
  })
})

describe('readinessSentence', () => {
  const ready = { progsnap_assignment_id: 1, trainable: true }
  const statisticsOnly = { progsnap_assignment_id: 2, trainable: false }

  it('says all are ready', () => {
    expect(readinessSentence([ready, { ...ready, progsnap_assignment_id: 3 }])).toBe(
      'Os 2 exercícios estão prontos para a extração de conceitos.',
    )
  })

  it('says how many are ready when only some are', () => {
    expect(readinessSentence([ready, statisticsOnly])).toBe(
      '1 dos 2 exercícios estão prontos para a extração de conceitos.',
    )
  })

  it('says only the statistics are left when none is ready', () => {
    expect(readinessSentence([statisticsOnly])).toMatch(/^Nenhum exercício/)
  })
})
