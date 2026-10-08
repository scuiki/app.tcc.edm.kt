import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ReopenApprovalNotice } from './ReopenApprovalNotice'

const NOTICE = 'Editar a matriz agora reabre todos os conceitos para aprovação.'

describe('ReopenApprovalNotice', () => {
  it('keeps the line until the dialog closes, even when the reload brings the draft', () => {
    const { rerender } = render(<ReopenApprovalNotice reopensApproval />)
    expect(screen.getByText(NOTICE)).toHaveClass('kc-dialog__note')
    rerender(<ReopenApprovalNotice reopensApproval={false} />)
    expect(screen.getByText(NOTICE)).toBeInTheDocument()
  })

  it('says nothing in a dialog opened on a draft', () => {
    render(<ReopenApprovalNotice reopensApproval={false} />)
    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument()
  })
})
