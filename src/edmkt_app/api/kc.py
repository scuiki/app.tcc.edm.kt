"""Router /kc — HTTP puro sobre os use cases de KC (KC-01..04).

Antes este arquivo tinha ~270 linhas com regra de negócio dentro do HTTP: gate de status,
autorização de KC, guarda 0-KC, reversão de aprovação, pré-check de trava e dispatch de
subprocess. Cada uma dessas foi para o seu lugar — specifications, kc_rules (as que precisam
rodar DENTRO da transação) e os use cases. Aqui ficou o transporte.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from edmkt_app.api.deps import (
    add_kc_uc,
    approve_qmatrix_uc,
    generate_kcs_uc,
    get_kc_job_status_uc,
    merge_kc_uc,
    remove_kc_uc,
    rename_kc_uc,
)
from edmkt_app.use_cases.add_kc import AddKCDto, AddKCUseCase
from edmkt_app.use_cases.approve_qmatrix import ApproveQMatrixDto, ApproveQMatrixUseCase
from edmkt_app.use_cases.generate_kcs import GenerateKCsDto, GenerateKCsUseCase
from edmkt_app.use_cases.get_kc_job_status import GetKCJobStatusUseCase
from edmkt_app.use_cases.merge_kc import MergeKCDto, MergeKCUseCase
from edmkt_app.use_cases.remove_kc import RemoveKCDto, RemoveKCUseCase
from edmkt_app.use_cases.rename_kc import RenameKCBody, RenameKCDto, RenameKCUseCase

router = APIRouter(tags=["kc"])


@router.post("/kc/generate", status_code=202)
def dispatch_kc_generate(
    body: GenerateKCsDto, uc: GenerateKCsUseCase = Depends(generate_kcs_uc)
) -> dict:
    return uc.execute(body)


@router.get("/kc/jobs/{job_id}")
def poll_kc_job(
    job_id: int, uc: GetKCJobStatusUseCase = Depends(get_kc_job_status_uc)
) -> dict:
    return uc.execute(job_id)


# --- edição síncrona da Q-matrix (KC-02, D-07) + aprovação (KC-03, D-06) ----------
# Sem subprocess: são writes diretos no SQLite, cada mutação numa única transação. A guarda
# 0-KC e a reversão de aprovação rodam DENTRO dela (kc_rules), porque só podem ser avaliadas
# depois da mutação — por isso não são specifications.


@router.patch("/kc/{kc_id}")
def rename_kc(
    kc_id: int, body: RenameKCBody, uc: RenameKCUseCase = Depends(rename_kc_uc)
) -> dict:
    return uc.execute(RenameKCDto(kc_id=kc_id, name=body.name))


@router.post("/kc", status_code=201)
def add_kc(body: AddKCDto, uc: AddKCUseCase = Depends(add_kc_uc)) -> dict:
    return uc.execute(body)


@router.delete("/kc/{kc_id}")
def remove_kc(kc_id: int, uc: RemoveKCUseCase = Depends(remove_kc_uc)) -> dict:
    return uc.execute(RemoveKCDto(kc_id=kc_id))


@router.post("/kc/merge")
def merge_kc(body: MergeKCDto, uc: MergeKCUseCase = Depends(merge_kc_uc)) -> dict:
    return uc.execute(body)


@router.post("/kc/approve")
def approve_kc(
    body: ApproveQMatrixDto, uc: ApproveQMatrixUseCase = Depends(approve_qmatrix_uc)
) -> dict:
    return uc.execute(body)
