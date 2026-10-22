# Convenções do repositório

Este repositório reúne **skills e agentes pessoais**. Cada artefato é autocontido e deve poder ser
copiado para outro lugar sem depender de arquivos fora da própria pasta.

## Estrutura

```
skills/<skill>/          # capacidades reutilizáveis (métodos, ferramentas, workflows)
agents/<agent>/          # personas e orquestradores com identidade própria
tools/                   # validação do repositório
docs/                    # documentação compartilhada
AGENTS.md                # estas convenções
README.md                # índice
```

Cada skill ou agente empacotado como skill segue o mesmo formato:

```
<artefato>/
├── SKILL.md          # contrato: frontmatter + instruções
├── README.md         # visão humana, instalação e uso
├── references/       # conhecimento de apoio
├── scripts/          # cálculos e automações
├── tests/            # testes dos scripts
├── templates/        # saídas/modelos
├── assets/           # schemas e exemplos
├── evals/            # casos de teste manuais
├── state/            # dados do usuário (gitignored)
└── output/           # relatórios gerados (gitignored)
```

- **Skills** ficam em `skills/<nome>/`.
- **Agentes** ficam em `agents/<nome>/`. Quando o agente for empacotado como skill, ele também tem
  `SKILL.md`; quando for só configuração/orquestração, tem `README.md` e os arquivos próprios.
- Nome da pasta = `name` do `SKILL.md`, em kebab-case.
- `SKILL.md` é o contrato. Se uma referência discordar dele, a referência está errada.
- Não criar pastas de skill na raiz. O validador procura apenas `skills/*/SKILL.md` e
  `agents/*/SKILL.md`.

## Dados e privacidade

- **Nunca** versionar `state/`, `output/`, extratos, posições, decisões, `.env` ou credenciais.
- Exemplos em `assets/` e `evals/` devem ser fictícios ou anonimizados.
- Não pedir ao usuário para editar JSON/schema quando a skill pode ingerir o dado bruto.
- Não commitar `__pycache__` nem arquivos gerados.

## Como adicionar uma skill

1. Criar `skills/<nome>/` com o nome em kebab-case.
2. Escrever `SKILL.md` com frontmatter (`name`, `description`, `license`, `metadata`) e o fluxo.
3. Separar conhecimento em `references/`, cálculos em `scripts/`, testes em `tests/`.
4. Adicionar uma linha na tabela de skills do `README.md` raiz.
5. Rodar a validação:

```bash
python3 tools/validate_skills.py
```

## Como adicionar um agente

1. Criar `agents/<nome>/`.
2. Se o agente for uma skill, seguir o mesmo formato de `SKILL.md` acima.
3. Se for configuração/orquestração, escrever `README.md` com objetivo, escopo, ferramentas e limites.
4. Adicionar uma linha na seção de agentes do `README.md` raiz.
5. Rodar `python3 tools/validate_skills.py`.

## Testes

Cada skill com scripts deve ter testes e rodar:

```bash
cd skills/<skill>   # ou agents/<agent>
python3 -m unittest discover -s tests
```

O validador roda isso automaticamente em todas as skills e agentes com `SKILL.md`. Se um teste depende
de rede, marcar como opcional e não bloquear a validação padrão.

## Commits

- Um commit por mudança coerente (skill nova, correção, mudança de política).
- Mensagem no imperativo e escopo claro: `add invest-portfolio-review`, `fix reconciliation`.
- Nunca commitar dados pessoais, mesmo em branch privada.
