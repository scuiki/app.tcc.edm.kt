"""Use cases da app layer: uma operação por classe, `execute(dto)` como única porta.

Escrita estende `BaseWriteUseCase` (valida as specifications antes de agir); leitura NÃO
estende — não há o que validar antes de ler, e herdar só pela simetria adicionaria cerimônia
sem regra por trás.
"""
