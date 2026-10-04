# O modelo e a versão do prompt da geração de KCs, que também entram na chave do cache do LLM.

# O Sonnet 5.5 não tem versão datada, então o job grava o modelo e a versão do prompt da extração
KC_GENERATION_MODEL_ID = "claude-sonnet-5-5"

# Incremente quando o prompt mudar, para um prompt novo não reaproveitar respostas do antigo
PROMPT_VERSION = "kcgen-v2"
