// As respostas da api em cada estado, tipadas pelo schema gerado para quebrar se o contrato mudar

import type { AssignmentSummary } from '../assignments/api/useAssignments'
import type { MasteryResponse } from './api/useMastery'
import type { PreTrainingStatistics } from './api/usePreTrainingStatistics'
import type { ReinforcementRecommendation } from './api/useReinforcementRecommendations'

export const masteryTrained: MasteryResponse = {
  assignment_id: 1,
  first_attempt_auc: 0.76,
  trained_at: '2026-06-21T00:00:00Z',
  matrix: [
    { student_id: 's1', kc_id: 439, mastery: 0.31 },
    { student_id: 's1', kc_id: 440, mastery: 0.82 },
    { student_id: 's2', kc_id: 439, mastery: 0.55 },
    { student_id: 's2', kc_id: 440, mastery: 0.68 },
  ],
  critical_kcs: [
    { kc_id: 439, mean_mastery: 0.43 },
    { kc_id: 440, mean_mastery: 0.75 },
  ],
  students_at_risk: ['s1', 's2'],
}

export const masteryUntrained: MasteryResponse = {
  assignment_id: 2,
  first_attempt_auc: null,
  trained_at: null,
  matrix: [],
  critical_kcs: [],
  students_at_risk: [],
}

export const statisticsWithData: PreTrainingStatistics = {
  assignment_id: 1,
  success_rate: { '439': 0.5, '440': 0.72 },
  learning_curve: { '0': 0.2, '1': 0.45, '2': 0.6 },
  compile_error_rate: { '439': 0.18, '440': 0.09 },
}

export const statisticsWithoutData: PreTrainingStatistics = {
  assignment_id: 2,
  success_rate: {},
  learning_curve: {},
  compile_error_rate: {},
}

export const recommendations: {
  assignment_id: number
  recommendations: ReinforcementRecommendation[]
} = {
  assignment_id: 1,
  recommendations: [
    {
      kc_id: 439,
      kc_name: 'Laços de repetição',
      mean_mastery: 0.43,
      text: 'Laços de repetição: domínio parcial — vale revisar (mastery média 43%).',
    },
  ],
}

export const assignments: { assignments: AssignmentSummary[] } = {
  assignments: [
    {
      id: 1,
      progsnap_assignment_id: 439,
      name: 'Assignment 439',
      status: 'trained',
      published_model_id: 7,
    },
    {
      id: 2,
      progsnap_assignment_id: 440,
      name: 'Assignment 440',
      status: 'kc_approved',
      published_model_id: null,
    },
  ],
}
