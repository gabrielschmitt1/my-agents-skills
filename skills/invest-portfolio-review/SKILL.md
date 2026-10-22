---
name: invest-portfolio-review
description: "Analisa e revisa carteiras de investimento no Brasil pelo método KRAKED (adaptação pessoal do KRAKEN: caixa/renda fixa, FIIs, ações brasileiras, criptoativos, exterior e diversos) a partir de dados colados do banco ou corretora. Use quando o usuário pedir 'avalia minha alocação', 'onde aporto esse mês', 'devo comprar X', 'revisão mensal da carteira', 'rebalancear', 'Kraken', 'Kraked', 'reavaliar meus investimentos', ou colar extrato/posições e pedir análise. Extrai as posições do texto, reconcilia os totais, grava a carteira em state/portfolio.json, calcula desvios e bandas, roda o teste de desvio estrutural, decide o aporte com ticket mínimo, avalia a compra de um ativo específico e registra a decisão. Não é recomendação regulada."
license: MIT
metadata:
  version: "4.0.0"
  language: "pt-BR"
  domain: "investment-management"
  framework: "KRAKED"
---

# Invest Portfolio Review

## Idioma e postura

- Responder **sempre em português do Brasil**, valores em R$ com vírgula decimal.
- Educacional e estruturação de decisão — não é recomendação individual regulada nem garantia de retorno.
- Separar **fato verificado**, **premissa** e **julgamento**; dizer o que falta em vez de preencher.
- Preferir resposta útil com premissas marcadas a resposta vazia por falta de dado. Nunca inventar preço,
  quantidade, alíquota ou total.

## Modos de uso

1. **Alocação:** o investidor cola os dados (extrato, posições, print transcrito) e pede "como está minha
   alocação?" → ingestão + diagnóstico.
2. **Aporte:** dados + "tenho R$ X para aportar" → ingestão + plano de aporte.
3. **Compra:** dados + "devo comprar Y?" → ingestão + decisão sobre o ativo.

Os três começam pela **ingestão**. Se a carteira já estiver em `state/portfolio.json` e o investidor não
trouxer dados novos, usar o estado salvo e confirmar a data.

## Ingestão de dados (o investidor cola, você estrutura)

**Nunca peça ao investidor para editar JSON ou preencher schema.** Ele cola o extrato; você extrai,
confere e grava.

1. Ler o texto colado e montar uma tabela normalizada: `symbol`, `name`, `group` (bloco do extrato),
   `primary_sleeve`, `quantity`, `price_brl`, `market_value_brl`, `net_value_brl`, `cost_basis_brl`,
   `income_brl`, `notes`.
2. **Reconciliar:** somar as posições e comparar com os subtotais **de cada grupo** (ETFs, FIIs, CDB…)
   e com o total do extrato. Testar **bruto e líquido** antes de acusar falta (o subtotal de renda fixa
   costuma ser bruto). Divergência acima de R$ 1,00 → **não gravar**, mostrar a diferença e pedir o dado
   que falta.
3. **Marcar cobertura:** `completa` ou `parcial`. Carteira parcial não permite conclusão sobre a
   alocação total — dizer isso explicitamente. Se o extrato trouxer percentuais por grupo, usá-los para
   estimar o total implícito e identificar seção faltante (ver `references/data-ingestion.md`).
4. Classificar por **sleeve**, não pela aba do banco ("Renda Variável" do banco mistura FIIs e ETFs).
   Ver `references/asset-classification.md`.
5. Perguntar só o que é bloqueante: data de referência, se há caixa livre não listado, se a carteira é
   parcial, se há posição em D. Registrar bruto e líquido quando o extrato mostrar os dois.
6. Gravar com `python3 scripts/save_portfolio.py` (valida, faz backup e mostra o diff). Nunca escrever
   `state/portfolio.json` à mão.
7. Repetir a tabela normalizada na resposta, com os totais conferidos, para o investidor validar.

Protocolo completo, tratamento de nomes truncados, aluguel de ações, posições empoeiradas e bruto x
líquido: `references/data-ingestion.md`.

## Baseline estratégico

**KRAKED** = KRAKEN adaptado: o antigo **N de Negócios** vira **D de Diversos**.

| Sleeve | Letra | Alvo | Banda de revisão |
|---|---|---:|---|
| Caixa / renda fixa pós-fixada | K1 | 20% | 15–25% |
| FIIs / imóveis | R | 20% | 15–25% |
| Ações brasileiras | A | 25% | 20–30% |
| Criptoativos | K2 | 5% | 0–7% |
| Ações/ativos internacionais | E | 25% | 20–30% |
| Diversos | D | 5% | 2–8% |

Soma 100%. Esta é uma **política pessoal declarada**, não o KRAKEN original: caixa em 20%, FIIs em 20%
e Diversos em 5%. O D é sempre parte da política — não existe “N não aplicável” nem renormalização.
Ver `references/allocation-framework.md`.

## Regras não negociáveis

1. Avaliar a carteira inteira (ou declarar que ela é parcial), não só o ativo proposto.
2. Separar alocação estratégica de oportunidade tática.
3. Não forçar compra só para bater percentual quando valuation, risco ou adequação não justificam.
4. Preferir aportes, distribuições e vencimentos para rebalancear antes de vender — salvo risco, tese,
   liquidez, tributo ou adequação que exijam outra ação.
5. Reserva de emergência é separada; o caixa de 20% não é automaticamente reserva.
6. Sem alavancagem, derivativos ou opções sem pedido explícito e análise de perda máxima e margem.
7. Cripto e capital de oportunidade não são diversificação nem renda garantidas.
8. Considerar tributo, custos, liquidez, crédito, câmbio, inflação e concentração em toda decisão.
9. **Uma posição, um sleeve primário.** Exposição secundária só em nota — evita dupla contagem.
10. **Denominador único e declarado:** ativos financeiros investíveis, **pós-aporte do mês**.
11. Nunca inventar preço, cota, yield, alíquota ou regra. Fonte + data ou "não informado".
12. Nunca garantir retorno nem apresentar cenário como previsão.
13. **Não comprar** é uma resposta válida e frequente. Se o sleeve está no teto da banda, o default é
    não comprar, salvo tese excepcional e concentração controlada.
14. **Diversos não é “o resto”:** só entra em D o que não pertence a K1, R, A, K2 ou E, com tese e
    limite de perda explícitos.

## Classificação e sleeve D (Diversos)

**D é o catch-all dos seis sleeves.** Entra em D o que não é K1, R, A, K2 nem E:

- ouro e commodities (ex.: GOLD11);
- negócio próprio, participação privada e private equity;
- capital de oportunidade e alternativas ilíquidas;
- estratégias com derivativos, se o investidor decidir operá-las.

D tem alvo de 5% e banda de 2–8%. **D não é lixeira:** cada posição precisa de tese, valor conservador,
limite de perda e prazo de revisão. Ouro é hedge, não motor de retorno; negócio próprio não é reserva de
emergência.

- Se D estiver acima do teto, o default é não comprar mais.
- Se D estiver abaixo e não houver ativo elegível, manter o valor em liquidez com prazo — não forçar
  compra ruim só para bater 5%.
- Ações de oportunidade listadas podem ficar em D **ou** dentro de A; escolher um enquadramento e
  registrar, para não contar o mesmo ativo duas vezes.
- Detalhes: `references/allocation-framework.md`, `references/diversos.md` e a tabela de classificação em
  `references/asset-classification.md`.

## Ritual mensal (resumo)

1. **Estado/ingestão:** ler `state/portfolio.json`; se houver dados colados, ingerir e reconciliar;
   se não houver nada, pedir o extrato (não pedir JSON).
2. **Data e denominador:** exigir a data de referência dos saldos (não assumir hoje) e declarar o que
   fica fora do modelo e se a cobertura é completa ou parcial.
3. **Valores:** usar preço/cota do extrato ou de fonte com data; sem cotação, pedir.
4. **Classificação:** uma posição por sleeve; ouro, commodities, negócio próprio e alternativas vão
   para **D (Diversos)**.
5. **Desvio:** rodar a alocação, comparar com alvo e banda, ordenar por gravidade.
6. **Teste estrutural:** o fluxo de aporte corrige? Em quantos meses? E os vencimentos de renda fixa?
7. **Risco:** concentração, sobreposição, crédito, liquidez, câmbio, estresse e tributo (se houver venda).
8. **Decisão:** plano de aporte ou veredito de compra, registro em `state/decisions.md`, próximo review.

Passo a passo operacional e checklist final: `references/monthly-review.md`.

## Teste de desvio estrutural

Sleeve **acima** da banda, sem vender: `total necessário = valor do sleeve / limite superior da banda`;
`meses ≈ (total necessário − total pós-aporte) / aporte mensal`.

Sleeve **abaixo** da banda: `gap = limite inferior × total − valor`; `meses ≈ gap / aporte mensal`
(só se 100% do aporte for para ele).

Acima de ~36 meses é **desvio estrutural**: a decisão é aceitar, rever a política ou vender parte.
Nunca responder "continue aportando" quando a aritmética mostra que o fluxo não fecha.

Quando o sleeve sobrepeso é **K1 (renda fixa)**, esse teste é pessimista: supõe o sleeve congelado.
Títulos vencem e saem do sleeve sem venda, sem IR antecipado e sem spread. Rodar também
`maturity_ladder.py`: se a escada concentra vencimentos nos próximos 12–24 meses, a correção é bem
mais rápida do que a diluição sugere — e pode dispensar a venda. Ver `references/portfolio-management.md`.

Quando a venda for necessária, o tamanho não é "o que falta": é
`(caixa − vencimentos no horizonte) − alvo × (total + aporte × meses)`. O script devolve esse número;
vender mais obriga a recomprar depois. Ver `references/fixed-income-brazil.md` para escolher **qual**
título sai (carry líquido, isento x tributado, cupom mais baixo primeiro).

## Ferramentas

Executar a partir da raiz da skill:

```bash
# 1) gravar a carteira extraída do extrato (valida, faz backup e mostra o diff)
python3 scripts/save_portfolio.py --input /tmp/carteira-extraida.json --expected-total 134000.00

# 2) diagnóstico e plano
python3 scripts/portfolio_allocation.py state/portfolio.json
python3 scripts/portfolio_allocation.py state/portfolio.json --no-contribution   # visão pré-aporte
python3 scripts/rebalance_contribution.py state/portfolio.json --amount 5000
python3 scripts/structural_drift.py state/portfolio.json --amount 5000

# 3) renda fixa: escada de vencimentos, carry líquido e tamanho da venda
python3 scripts/maturity_ladder.py state/portfolio.json --amount 5000 --months 24
python3 scripts/maturity_ladder.py state/portfolio.json --cdi 13.90 --inflation 4.50 --sell 12000

# 4) testes dos cálculos
python3 -m unittest discover -s tests
```

- `state/portfolio.json` guarda o que **já está investido** na data `as_of`. `contribution_month_brl`
  é o aporte do mês **ainda não investido**: os scripts o somam ao caixa. Depois de investir, zere o
  campo e atualize as posições.
- Aporte citado na conversa é **cenário**: use `--amount` no plano. Só grave `contribution_month_brl`
  se o dinheiro já estiver disponível e não investido; caso contrário, não infle o denominador.
- Aceitam `sleeves` (valores por classe) ou `positions` (ativo a ativo); aceitam nomes em português.
- `maturity_ladder.py` exige `maturity`, `indexer`, `rate_pct` e `tax_exempt` por título de renda fixa;
  as taxas de referência (CDI, Selic, inflação) vêm de `--cdi`, `--selic` e `--inflation`. Sem elas, a
  coluna líquida sai como `n/d` — o script não inventa taxa.
- Os seis sleeves são sempre ativos. **D (Diversos)** é um sleeve normal: recebe aporte quando está
  abaixo do alvo, como qualquer outro.
- Scripts são **apoio de cálculo**, não decisão: se o resultado conflitar com a análise, explicar a
  diferença. Nunca editar o script para acomodar um dado.
- `--json` para saída estruturada. Ticket mínimo vem de `min_ticket_brl` no JSON.

## Estado do investidor

| Arquivo | Conteúdo | Versionar? |
|---|---|---|
| `state/portfolio.json` | carteira, alvos, bandas, tickets, perfil | **não** (gitignored) |
| `state/decisions.md` | log append-only de decisões | **não** |
| `state/history/` | snapshots anteriores (backup automático) | **não** |
| `output/AAAA-MM-revisao.md` | relatório do mês | **não** |
| `assets/`, `templates/`, `references/` | material reutilizável | sim |

Nunca sobrescrever o snapshot anterior sem backup — `save_portfolio.py` já faz isso.

## Dados

Regra: preço/cota/taxa só com fonte e data; sem acesso, perguntar. Câmbio por PTAX de venda do dia útil
anterior, registrando a taxa. Detalhes: `references/data-sources.md`. Ingestão de extrato:
`references/data-ingestion.md`.

## Formato de saída

### A) Alocação (revisão)

1. **Snapshot:** data de referência, fonte dos dados (extrato colado), cobertura (completa/parcial),
   denominador (pré/pós-aporte), qualidade dos dados, total, tabela por sleeve (valor, peso, alvo, desvio,
   gap, banda, situação), o que ficou fora do modelo. Gap: **negativo = acima do alvo**.
2. **Reconciliação da ingestão:** total somado x total do extrato; divergências e o que ficou de fora.
3. **Mudanças desde o último review:** aportes, compras/vendas, cruzamentos de banda, pendências. No
   primeiro review, declarar "sem snapshot anterior" e registrar a linha de base.
4. **Comparação com o alvo:** ordenada por gravidade, dizendo o critério usado.
5. **Desvio estrutural:** meses estimados e conclusão (fluxo resolve / lento / estrutural). Dizer se o
   aporte é recorrente; se for evento único, apresentar como cenário único.
6. **Riscos:** concentração (por ativo, gestora, segmento, emissor), sobreposição, crédito, liquidez,
   câmbio, estresse e tributo (fonte + data).
7. **Ações recomendadas:** imediatas x watchlist, com o que **não** fazer agora.
8. **Riscos e premissas:** o que invalidaria o plano e quais dados faltam.
9. **Registro e fontes:** decisão registrada (ou onde será), próximo review, fontes com data, até 5
   perguntas abertas priorizadas.

### B) Aporte

Mesmo formato de A, com a seção 7 substituída pelo **plano de aporte**: tabela por sleeve, ativo
candidato, ticket mínimo, resíduo em liquidez, contingências e o que não comprar.

### C) Decisão de compra ("devo comprar X?")

1. **Encaixe na política:** sleeve, peso atual, alvo, banda, gap e se o sleeve está no teto.
2. **Sobreposição:** o que a carteira já tem parecido (mesmo índice, mesma gestora, mesmo segmento,
   mesma tese) e quanto ficaria concentrado.
3. **Tese e qualidade:** o que se sabe do ativo e o que falta; nunca preencher com achismo.
4. **Preço e valuation:** múltiplos, P/VP, yield, comparação com alternativas; fonte e data.
5. **Tamanho e execução:** valor da posição, ticket mínimo, lote, liquidez, custo, spread.
6. **Risco e tributo:** o que pode dar errado; regra aplicável só com fonte verificada.
7. **Veredito:** comprar / comprar parcialmente / não comprar agora / só se [condição] — com o motivo
   em uma frase e as condições que mudariam a resposta.
8. **Alternativa:** onde o mesmo dinheiro rende mais valor estratégico (sleeve carente, reserva, nada).

Protocolo detalhado: `references/buy-decision.md`.

## Mapa de arquivos

| Arquivo | Carregar quando |
|---|---|
| `references/monthly-review.md` | sempre que for revisão mensal |
| `references/data-ingestion.md` | sempre que houver dados colados/extrato |
| `references/asset-classification.md` | classificar ticker, ETF, FII ou renda fixa |
| `references/buy-decision.md` | "devo comprar X?" |
| `references/allocation-framework.md` | alvos, bandas, KRAKED, papel de D |
| `references/portfolio-management.md` | rebalanceamento, estresse, performance |
| `references/risk-and-suitability.md` | perfil, reserva, concentração, qualidade de dados |
| `references/data-sources.md` | qualquer atualização de preço/câmbio/taxa |
| `references/brazil-tax-and-regulatory-checklist.md` | venda, realização, resgate, cripto, exterior |
| `references/brazilian-equities.md` | ação ou BDR específico |
| `references/real-estate-fiis.md` | FII específico |
| `references/fixed-income-brazil.md` | CDB, LCI/LCA, Tesouro, fundo de RF — e qual vender primeiro |
| `references/international-assets.md` | ETF exterior, BDR, ativo fora do Brasil |
| `references/cryptoassets.md` | cripto direta, ETF de cripto, custódia |
| `references/diversos.md` | sleeve D: ouro, commodities, negócio próprio, alternativas |
| `references/decision-log-template.md` | registrar decisão |
| `references/research-and-bibliography.md` | atribuição, fontes, verificação |
| `templates/monthly-report.md` | gerar o relatório do mês |
| `evals/test-cases.md` | testar/ajustar a própria skill |

## Limites

Suporte educacional e de estruturação de decisão; não substitui aconselhamento regulado individual.
Perguntar dado faltante em vez de inventar. Não assumir que o investidor deve ter os seis sleeves.
Não recomendar ativo específico sem análise do sleeve, do ativo e da adequação.
