"""Value objects da app layer: uma invariante por tipo, construída na fronteira.

Cada tipo aqui absorve uma checagem que o código repetia — `TurmaSlug` substituiu 7 definições
de `_slug`, `ProgSnapAssignmentId` 5 de `_progsnap_aid`, `CodeStateId` o `_safe_csid_name` e
`ConfinedPath` o `_confine`.

Regra de fronteira: o VO é construído e validado AQUI, na app layer, e desembrulhado para
primitivo antes de sair dela — antes de entrar em `ml` (camada congelada, que compara
com colunas de DataFrame) e antes de virar corpo de resposta HTTP (serializado cru, o FastAPI
emitiria `{"value": ...}` e quebraria o contrato).

Todos são `frozen`: um valor validado não muda depois de construído; para ter outro, construa
outro.
"""

from edmkt_app.values.code_state_id import CodeStateId
from edmkt_app.values.progsnap_assignment_id import ProgSnapAssignmentId
from edmkt_app.values.turma_slug import TurmaSlug

__all__ = ["CodeStateId", "ProgSnapAssignmentId", "TurmaSlug"]
