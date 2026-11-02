# O modelo e a versão do prompt da geração de KCs, que também entram na chave do cache do LLM.

# O Haiku 4.5 na versão datada, e o job grava o modelo e a versão do prompt da extração
KC_GENERATION_MODEL_ID = "claude-haiku-4-5-20251001"

# Incremente quando o prompt mudar, para um prompt novo não reaproveitar respostas do antigo
PROMPT_VERSION = "kcgen-v2"
