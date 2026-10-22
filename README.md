# my-agents-skills

Coleção pessoal de skills e agentes de IA.

## Skills

| Skill | Para que serve |
|---|---|
| [`invest-portfolio-review`](skills/invest-portfolio-review/) | Revisão de carteira pelo método KRAKED (KRAKEN adaptado) a partir do extrato colado: ingestão, alocação, aporte, decisão de compra e registro |

## Agentes

| Agente | Para que serve |
|---|---|
| [`carteira`](agents/carteira/) | Orquestra a skill `invest-portfolio-review`: decide o modo (alocação, aporte, compra ou revisão), aplica guardrails e mantém preferências, sem recalcular a política |

## Estrutura

```text
skills/<skill>/          # capacidades reutilizáveis
agents/<agent>/          # personas e orquestradores
tools/validate_skills.py # validação do repositório
docs/installation.md     # instalação em diferentes harnesses
AGENTS.md                # convenções e regras de privacidade
```

Cada skill é autocontida: `SKILL.md` na raiz da pasta, material de apoio em `references/`, cálculos em
`scripts/`, templates em `templates/` e exemplos em `assets/`. Convenções e regras de privacidade estão
em [`AGENTS.md`](AGENTS.md).

## Documentação

- [Instalação em qualquer harness](docs/installation.md)

Para validar todas as skills e agentes (frontmatter, links, JSON e testes):

```bash
python3 tools/validate_skills.py
```
