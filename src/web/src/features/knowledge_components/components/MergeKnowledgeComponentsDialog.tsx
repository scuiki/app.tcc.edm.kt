import { useState } from 'react'

import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { SelectField } from '../../../components/ui/SelectField'
import { useMergeKnowledgeComponents } from '../api/knowledgeComponents'
import {
  editErrorText,
  listProblemIds,
  mergedProblemIds,
  problemCount,
  type KnowledgeComponentUsage,
} from '../knowledgeComponents'
import './KnowledgeComponentDialogs.css'

interface MergeKnowledgeComponentsDialogProps {
  assignmentId: number
  // O conceito de onde o professor pediu a fusão
  knowledgeComponent?: KnowledgeComponentUsage
  knowledgeComponents: KnowledgeComponentUsage[]
  onClose: () => void
}

export function MergeKnowledgeComponentsDialog({
  assignmentId,
  knowledgeComponent,
  knowledgeComponents,
  onClose,
}: MergeKnowledgeComponentsDialogProps) {
  return (
    <Dialog open={knowledgeComponent != null} onClose={onClose} title="Mesclar conceitos">
      {knowledgeComponent ? (
        <MergeForm
          assignmentId={assignmentId}
          origin={knowledgeComponent}
          knowledgeComponents={knowledgeComponents}
          onDone={onClose}
        />
      ) : null}
    </Dialog>
  )
}

interface MergeFormProps {
  assignmentId: number
  origin: KnowledgeComponentUsage
  knowledgeComponents: KnowledgeComponentUsage[]
  onDone: () => void
}

function MergeForm({ assignmentId, origin, knowledgeComponents, onDone }: MergeFormProps) {
  const [otherId, setOtherId] = useState<number | null>(null)
  // Por padrão fica o conceito de onde a fusão começou
  const [keepId, setKeepId] = useState(origin.id)
  const merge = useMergeKnowledgeComponents(assignmentId)
  const other = knowledgeComponents.find((kc) => kc.id === otherId)
  const pair = other ? [origin, other] : []
  const keep = pair.find((kc) => kc.id === keepId)
  const drop = pair.find((kc) => kc.id !== keepId)

  return (
    <>
      <DialogBody>
        <SelectField
          label="Mesclar com"
          placeholder="Escolha o outro conceito"
          value={otherId == null ? '' : String(otherId)}
          options={knowledgeComponents
            .filter((kc) => kc.id !== origin.id)
            .map((kc) => ({ value: String(kc.id), label: kc.name }))}
          onChange={(value) => setOtherId(Number(value))}
        />
        {keep && drop ? (
          <>
            <fieldset className="kc-options">
              <legend className="kc-dialog__label">Qual nome fica</legend>
              {pair.map((kc) => (
                <label
                  key={kc.id}
                  className={`kc-options__item${kc.id === keepId ? ' kc-options__item--chosen' : ''}`}
                >
                  <input
                    type="radio"
                    name="keep-knowledge-component"
                    checked={kc.id === keepId}
                    onChange={() => setKeepId(kc.id)}
                  />
                  <span className="kc-options__text">
                    <span className="kc-options__name">Manter {kc.name}</span>
                    <span className="t-support">marca {problemCount(kc.problemIds.length)}</span>
                  </span>
                </label>
              ))}
            </fieldset>
            <p className="kc-dialog__note">
              O conceito descartado some e seus problemas passam a ser marcados pelo mantido. No fim
              serão {problemCount(mergedProblemIds(keep, drop).length)}:{' '}
              {listProblemIds(mergedProblemIds(keep, drop))}.
            </p>
          </>
        ) : null}
        {merge.isError ? (
          <p role="alert" className="kc-dialog__error">
            {editErrorText(merge.error)}
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button
          variant="primary"
          disabled={!keep || !drop || merge.isPending}
          onClick={() => {
            if (keep && drop) {
              merge.mutate({ keepKcId: keep.id, dropKcId: drop.id }, { onSuccess: onDone })
            }
          }}
        >
          Mesclar
        </Button>
      </DialogFooter>
    </>
  )
}
