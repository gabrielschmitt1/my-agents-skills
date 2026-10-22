# Invest Portfolio Review — Agent Skill

Revisão de carteira de investimentos pelo método **KRAKED** (adaptação pessoal do KRAKEN: caixa/renda
fixa, FIIs, ações brasileiras, cripto, exterior e diversos). O investidor **cola os dados do banco**; a skill extrai, confere,
classifica, grava o estado e responde à pergunta.

## O que ela faz

- **Ingere** texto de extrato/tela de carteira sem pedir JSON ao investidor.
- **Reconcilia** a soma das posições com os subtotais do extrato e recusa gravar quando não fecha.
- **Classifica** cada ativo no sleeve certo (a aba do banco não é o sleeve).
- Compara a carteira com a política declarada (alvo, banda, desvio em p.p. e gap em R$).
- Roda o **teste de desvio estrutural**: o aporte mensal corrige o desvio? Em quantos meses?
- Distribui o aporte entre sleeves abaixo do alvo, respeitando ticket mínimo.
- Responde **"devo comprar X?"** com encaixe, sobreposição, preço, tamanho e veredito.
- Separa o que é **Diversos (D)** — ouro, commodities, negócio próprio, alternativas — do resto.
- Checa concentração, sobreposição, liquidez, crédito, câmbio, estresse e tributo.
- Registra a decisão e o próximo review.

## Três modos de uso

1. **Avaliar a alocação:** cole o extrato e peça "como está minha alocação?".
2. **Aportar:** cole o extrato e diga "tenho R$ 5.000 para aportar; para onde vai?".
3. **Comprar:** cole o extrato e pergunte "devo comprar KNRI11?".

Nos três, a primeira etapa é a ingestão. Se já houver `state/portfolio.json` e nenhum dado novo, a skill
usa o estado salvo e confirma a data.

## Alocação baseline

| Sleeve | Alvo | Banda |
|---|---:|---|
| Caixa / renda fixa | 20% | 15–25% |
| FIIs | 20% | 15–25% |
| Ações BR | 25% | 20–30% |
| Cripto | 5% | 0–7% |
| Exterior | 25% | 20–30% |
| Diversos | 5% | 2–8% |

Soma 100%. Esta é uma **política pessoal** (KRAKED), não o KRAKEN original: caixa em 20%, FIIs em 20% e
Diversos em 5%. Ver `references/allocation-framework.md`.

## Fluxo de ingestão

```
extrato colado
   → extração da tabela normalizada
   → reconciliação com os subtotais (tolerância R$ 1,00)
   → classificação por sleeve
   → scripts/save_portfolio.py (valida, faz backup, mostra diff)
   → análise (alocação, aporte ou compra)
```

Regras: usar **saldo bruto** na alocação e **líquido** para resgate; não confiar na aba "Renda
Variável" do banco; commodity/ouro e negócio próprio ficam em **D (Diversos)**; posição residual é
mantida e sinalizada; carteira parcial é declarada como parcial.

## Estrutura

```
SKILL.md                          política, modos, regras e formatos de saída
references/data-ingestion.md      protocolo de extração e reconciliação do extrato
references/asset-classification.md tabela de tickers e regras de sleeve
references/buy-decision.md        protocolo "devo comprar X?"
references/monthly-review.md      passo a passo operacional + checklist
references/allocation-framework.md alvos, bandas, KRAKED e papel de D
references/                       risco, tributo, classes de ativo, fontes
scripts/save_portfolio.py         grava a carteira extraída (único caminho de escrita)
scripts/                           cálculos de alocação, aporte e desvio
templates/monthly-report.md       esqueleto do relatório mensal
assets/portfolio-schema.json      schema da carteira (v4)
assets/portfolio.example.json     exemplo preenchido
state/                            SUA carteira, backups e log de decisões (gitignored)
output/                           relatórios gerados (gitignored)
evals/test-cases.md               casos de teste da skill
tests/                            testes dos cálculos e da ingestão
```

## Uso

```bash
# 1) o investidor cola o extrato; a skill monta /tmp/carteira.json e grava:
python3 scripts/save_portfolio.py --input /tmp/carteira.json --expected-total 134000.00

# 2) análise
python3 scripts/portfolio_allocation.py state/portfolio.json
python3 scripts/portfolio_allocation.py state/portfolio.json --no-contribution
python3 scripts/rebalance_contribution.py state/portfolio.json --amount 5000
python3 scripts/structural_drift.py state/portfolio.json --amount 5000

# 2b) renda fixa: escada de vencimentos, carry líquido e tamanho da venda
python3 scripts/maturity_ladder.py state/portfolio.json --amount 5000 --months 24
python3 scripts/maturity_ladder.py state/portfolio.json --cdi 13.90 --inflation 4.50 --sell 12000

# 3) testes
python3 -m unittest discover -s tests
```

`save_portfolio.py` é o único caminho de escrita do estado: valida sleeves e números, reconcilia o
total, guarda o snapshot anterior em `state/history/` e mostra o diff por sleeve. Os demais scripts
aceitam `sleeves` (valor por classe) ou `positions` (ativo a ativo) e nomes de sleeve em português.
São apoio de cálculo: não decidem compra, venda ou adequação.

`maturity_ladder.py` é a exceção: exige `positions` com `maturity`, `indexer`, `rate_pct` e
`tax_exempt` por título de renda fixa, porque vencimento e indexador são propriedades do papel, não do
sleeve. Taxas de referência entram por `--cdi`, `--selic` e `--inflation` — o script não inventa taxa.

## Privacidade

`state/` e `output/` estão no `.gitignore`. Não commitar carteira, extratos, custo de aquisição ou
relatórios pessoais. Se for publicar a skill, publique só `SKILL.md`, `references/`, `scripts/`,
`templates/`, `assets/` e `evals/`.

## Aviso

Conteúdo educacional e estruturação de decisão. Não é garantia de retorno nem substitui aconselhamento
individual regulado. Verifique preços, regras tributárias e documentos dos produtos antes de agir.
