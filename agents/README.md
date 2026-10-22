# Agentes

Cada agente pessoal fica em `agents/<nome>/`.

| Agente | Função |
|---|---|
| [`carteira`](carteira/) | Orquestração fina da carteira; carrega a skill `invest-portfolio-review` |

- Se o agente for empacotado como skill, use `SKILL.md` + `README.md` e o mesmo formato de `skills/`.
- Se for configuração/orquestração, use `README.md` com objetivo, escopo, ferramentas, limites e
  arquivos de configuração.
- Nunca versionar `state/`, `output/`, dados pessoais ou credenciais.

O validador do repositório procura `agents/*/SKILL.md`; agentes só de configuração são revisados
manualmente pelo README.
