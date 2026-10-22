# Agente Carteira

Agente fino de orquestração da carteira pessoal. Ele não é um segundo motor de cálculo: carrega a
skill [`invest-portfolio-review`](../../skills/invest-portfolio-review/) e decide **quando** e **como**
usar cada modo dela.

## O que ele faz

- Roteia a conversa para alocação, aporte, decisão de compra ou revisão mensal.
- Cobra data de referência, cobertura e reconciliação antes de concluir.
- Aplica guardrails: não inventa preço, não pede JSON, não esconde carteira parcial.
- Mantém preferências duráveis do investidor.
- Fecha com um próximo passo e o próximo review.

## O que ele não faz

- Não define alvos, bandas ou política. Isso é da skill.
- Não recalcula alocação, aporte, desvio ou imposto.
- Não grava posições sem a skill.
- Não substitui recomendação regulada nem profissional habilitado.

## Dependência

- Skill: `invest-portfolio-review` versão **4.0.0+**.
- Caminho no repositório: `skills/invest-portfolio-review/`.
- Se o runtime carregar skills por nome, use `invest-portfolio-review`. Se não, leia o `SKILL.md` da
  skill pelo caminho relativo.

## Como usar

Exemplos:

- "Agente Carteira, como está minha alocação?"
- "Tenho R$ 5.000 para aportar. Onde coloco?"
- "Devo comprar KNRI11?"
- "Revisão mensal da carteira."
- "Vou colar meu extrato; quero saber se estou fora da banda."

O agente escolhe o modo, carrega a skill e devolve o resultado no formato dela. Se a intenção estiver
ambígua, ele pergunta uma vez.

## Estrutura

```text
agents/carteira/
├── SKILL.md              # orquestração, roteamento e guardrails
├── README.md             # este arquivo
├── evals/test-cases.md   # casos manuais de trigger e roteamento
└── state/                # preferências do agente (gitignored)
```

## Dados e privacidade

- `state/` é ignorado pelo git. Não versionar preferências, extratos ou decisões.
- A carteira e o log de decisões ficam no estado da skill, não no estado do agente.
- Exemplos e evals devem ser fictícios.

## Validação

```bash
python3 tools/validate_skills.py
```

O validador checa frontmatter, nome da pasta, links, JSONs e roda os testes da skill dependente. Os
casos do agente são manuais, em `evals/test-cases.md`.
