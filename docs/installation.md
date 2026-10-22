# Instalação em qualquer harness

Este guia explica como instalar a skill `invest-portfolio-review` e o agente `carteira` em diferentes
harnesses. O formato é portável; o que muda é o diretório que cada ferramenta varre.

## 1. O que significa instalar

Uma skill é uma **pasta autocontida**, não um pacote com build ou `pip install`.

```text
invest-portfolio-review/
├── SKILL.md          # contrato e instruções
├── README.md
├── references/       # conhecimento de apoio
├── scripts/          # cálculos e automação
├── assets/           # schema e exemplo
├── templates/        # relatório mensal
├── evals/            # casos manuais
├── tests/            # testes dos scripts
└── state/            # carteira e decisões (gitignored, criado em runtime)
```

Instalar = copiar ou criar um symlink da **pasta inteira** para o diretório de skills do harness.

> Não copie apenas o `SKILL.md`. Os caminhos para `references/`, `scripts/` e `assets/` são relativos
> à pasta da skill.

## 2. Requisitos

- **Python 3.10+** recomendado.
- Apenas biblioteca padrão; os scripts não exigem `pip install`.
- O harness precisa permitir:
  1. descobrir skills;
  2. ler arquivos;
  3. executar shell/comandos para rodar os scripts.
- A pasta `state/` precisa ser gravável. Se a instalação for em diretório somente leitura, use
  `--state` e `--history` para apontar para um caminho gravável.

Sem execução de comandos, o harness pode usar o `SKILL.md` como instrução, mas não conseguirá rodar a
reconciliação, a alocação, o aporte ou os testes.

## 3. Onde colocar em cada harness

| Harness | Caminho típico |
|---|---|
| **Claude Code / setup atual deste repo** | `~/.claude/skills/invest-portfolio-review/` ou `.claude/skills/` no projeto |
| **Cursor** | `~/.cursor/skills/invest-portfolio-review/` ou `.cursor/skills/` no projeto |
| **Claude apps** | ZIP da pasta, importado em Settings → Capabilities → Skills, se disponível no plano |
| **OpenCode** | diretório de skills configurado no setup; neste ambiente, `~/.claude/skills/` é usado |
| **Outros harnesses** | diretório de skills/instruções configurado; se não houver suporte a skills, use o `SKILL.md` como prompt e exponha os scripts como ferramentas |

O nome da pasta deve ser igual ao `name` do frontmatter:

```yaml
---
name: invest-portfolio-review
---
```

## 4. Instalação global x por projeto

### Global

Vale para todos os projetos do usuário.

```bash
# Claude Code / OpenCode neste setup
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/invest-portfolio-review" ~/.claude/skills/invest-portfolio-review

# Cursor
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/skills/invest-portfolio-review" ~/.cursor/skills/invest-portfolio-review
```

### Por projeto

Vale só para o repositório atual.

```bash
mkdir -p .claude/skills
ln -s "$(pwd)/skills/invest-portfolio-review" .claude/skills/invest-portfolio-review
```

Para Cursor, troque `.claude/skills` por `.cursor/skills`.

## 5. Symlink x cópia

| Estratégia | Vantagem | Cuidado |
|---|---|---|
| **Symlink** | Atualiza junto com o repo; ótimo para desenvolvimento | O harness precisa seguir symlinks |
| **Cópia** | Isola a versão instalada | Atualização manual; preserve `state/` ao recopiar |

Se já existir um link antigo:

```bash
ln -sfn "$(pwd)/skills/invest-portfolio-review" ~/.claude/skills/invest-portfolio-review
```

Se preferir copiar:

```bash
cp -R skills/invest-portfolio-review ~/.claude/skills/
```

## 6. Instalando o agente `carteira`

O agente depende da skill. O ideal é deixar os dois como irmãos no diretório de skills:

```bash
ln -s "$(pwd)/skills/invest-portfolio-review" ~/.claude/skills/invest-portfolio-review
ln -s "$(pwd)/agents/carteira" ~/.claude/skills/carteira
```

Assim o fallback do agente (`../../skills/invest-portfolio-review/SKILL.md`) funciona. Se o harness
carregar skills por nome, ele pode chamar `invest-portfolio-review` diretamente.

Se o harness tiver um diretório separado para agentes, instale o agente lá e ajuste a dependência para
o nome da skill ou para o caminho correto.

## 7. Como testar a instalação

```bash
cd ~/.claude/skills/invest-portfolio-review
python3 -m unittest discover -s tests
python3 scripts/portfolio_allocation.py --example
```

Depois, no harness:

```text
Use a skill invest-portfolio-review para avaliar minha alocação.
```

Com o agente:

```text
Agente Carteira, como está minha alocação?
```

## 8. Empacotar para upload

Se o harness pedir ZIP:

```bash
cd skills
zip -r invest-portfolio-review.zip invest-portfolio-review \
  -x '*/state/*' '*/__pycache__/*'
```

Alguns harnesses exigem o `SKILL.md` na raiz do ZIP, não dentro de uma pasta:

```bash
cd skills/invest-portfolio-review
zip -r ../../invest-portfolio-review.zip . \
  -x 'state/*' '__pycache__/*'
```

Nunca inclua `state/` com dados reais no ZIP.

## 9. Atualização

### Com symlink

```bash
cd ~/Personal/my-agents-skills
git pull
```

O link aponta para o repo, então a atualização é imediata.

### Com cópia

1. Preserve `state/`.
2. Copie a nova versão da skill.
3. Rode os testes.
4. Confira se o schema mudou.

```bash
cp -R skills/invest-portfolio-review ~/.claude/skills/
cd ~/.claude/skills/invest-portfolio-review
python3 -m unittest discover -s tests
```

## 10. Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| Skill não aparece | Pasta fora do diretório varrido ou `SKILL.md` ausente | Coloque a pasta diretamente no diretório de skills; confirme `SKILL.md` na raiz |
| Skill aparece com outro nome | `name` do frontmatter difere da pasta | Renomeie a pasta ou o `name` |
| Skill carrega, mas não calcula | Harness sem shell/Python ou cwd errado | Rode a partir da raiz da skill e confirme Python 3.10+ |
| Erro ao gravar estado | Diretório somente leitura | Instale no home ou use `--state`/`--history` |
| Cálculo não bate | Dados parciais ou bruto x líquido | Reconcilie antes de concluir; a skill não deve gravar com divergência |
| Agente não acha a skill | Dependência não instalada ou caminho mudou | Instale a skill como irmã ou ajuste a referência para o nome |

## 11. Segurança e privacidade

- A skill executa scripts Python locais. Revise o código antes de instalar em harness com permissão de
  shell.
- Os scripts usam apenas biblioteca padrão e não fazem chamadas de rede.
- `state/` contém carteira, decisões e possivelmente dados pessoais. Nunca versione nem inclua em ZIP.
- O agente mantém apenas preferências em `agents/carteira/state/agent-memory.md`; a carteira fica no
  estado da skill.

## 12. Resumo

1. Copie ou symlinka a pasta `skills/invest-portfolio-review` para o diretório de skills do harness.
2. Mantenha a estrutura interna (`references/`, `scripts/`, `assets/`, `templates/`).
3. Garanta Python 3.10+ e `state/` gravável.
4. Instale o agente `carteira` junto, se quiser a orquestração.
5. Teste com `python3 -m unittest discover -s tests`.
6. Se o harness não suportar skills, use o `SKILL.md` como prompt e os scripts como ferramentas.
