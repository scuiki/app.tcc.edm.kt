import { useState } from 'react'

import { REOPEN_APPROVAL_NOTICE } from '../knowledgeComponents'
import './KnowledgeComponentDialogs.css'

interface ReopenApprovalNoticeProps {
  // Se os conceitos estavam aprovados quando o diálogo abriu
  reopensApproval: boolean
}

// A linha do aviso de reabrir nos diálogos que já têm confirmação ou formulário próprio
export function ReopenApprovalNotice({ reopensApproval }: ReopenApprovalNoticeProps) {
  // Fica a situação da abertura, porque a recarga traz o rascunho antes de o diálogo fechar
  const [isShown] = useState(reopensApproval)
  return isShown ? <p className="kc-dialog__note">{REOPEN_APPROVAL_NOTICE}</p> : null
}
