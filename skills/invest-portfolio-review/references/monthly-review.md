# Ritual de revisão mensal

Checklist operacional. O `SKILL.md` define a política; este arquivo define a ordem de execução.
Não pular etapas por falta de dado: registrar "não informado" e perguntar.

## Passo 0 — Estado e ingestão

1. Procurar `state/portfolio.json` e `state/decisions.md`.
2. Se o investidor colou dados novos: seguir `references/data-ingestion.md` — extrair, reconciliar
   totais (testando bruto e líquido), classificar e gravar com
   `python3 scripts/save_portfolio.py --input ... --expected-total ...`.
3. Se não houver dados nem estado: pedir o extrato em texto, nunca pedir JSON nem mandar preencher
   schema. Se ele só tiver números aproximados, registrar como estimativa e marcar cobertura parcial.
4. Se existir estado: ler `as_of`, `data_coverage` e `source`; se estiver defasado, pedir atualização
   antes de calcular qualquer desvio.
5. Nunca sobrescrever o snapshot anterior: `save_portfolio.py` já copia para `state/history/`.

## Passo 1 — Data, denominador e natureza do aporte

1. Exigir a **data de referência** dos saldos. Se o investidor não informar, perguntar. Não assumir "hoje".
2. Definir o denominador explicitamente: **ativos financeiros investíveis, pós-aporte do mês**.
3. Separar o que **já está investido** do que é **aporte ainda não investido** (`contribution_month_brl`).
   Registrar se o aporte entra no caixa antes de ser alocado.
4. Listar o que fica fora: reserva de emergência, imóvel, previdência, participação societária não
   incluída em D, dívidas.
5. Registrar aportes e retiradas do mês, com data, e perguntar se o aporte é **recorrente** ou evento
   único — o teste estrutural depende disso.

## Passo 2 — Valores de mercado

1. Atualizar cada posição com preço/cota e data. Fontes em `references/data-sources.md`.
2. **Alocação usa saldo bruto (valor de mercado); resgate usa saldo líquido.** Registrar os dois quando
   o extrato mostrar e não misturar na mesma coluna.
3. Sem cotação? Pedir ao investidor. Nunca estimar, nunca usar preço "de memória".
4. Para ativo em moeda estrangeira: converter por PTAX de venda do dia útil anterior e registrar a taxa.
5. Marcar ativos ilíquidos ou avaliados por estimativa (negócio privado, imóvel) como tal.
6. Posição residual (< R$ 1,00) é mantida e sinalizada; não distorce a análise.

## Passo 3 — Classificação

1. Cada posição em **um** sleeve primário. Exposição secundária só em nota (evita dupla contagem).
2. **D (Diversos)** é o catch-all: ouro, commodities, negócio próprio, private equity, capital de
   oportunidade, derivativos e alternativos. Não existe “N não aplicável” nem renormalização.
3. O que não for identificável vai para `unmapped` com motivo — nunca chutar para fechar a conta.
4. Se D for usado para "ações de oportunidade" listadas: a divisão 80/20 dentro do sleeve A **não** se
   aplica (seria dupla contagem). Escolher um dos dois enquadramentos e registrar.

## Passo 4 — Desvio contra a política

1. Rodar `python3 scripts/portfolio_allocation.py state/portfolio.json` (o script soma
   `contribution_month_brl` ao caixa; use `--no-contribution` para ver o pré-aporte).
2. Reportar peso atual, alvo, desvio em p.p., gap em R$ e situação na banda.
3. Ordenar os desvios por **gravidade**: (a) fora da banda, (b) distância em p.p. até o alvo,
   (c) valor em R$. Dizer qual critério foi usado.
4. Banda é gatilho de análise, não ordem de compra ou venda.

## Passo 5 — Teste estrutural

1. Rodar `python3 scripts/structural_drift.py state/portfolio.json --amount [aporte]`.
2. Se o sleeve acima da banda for **K1 (renda fixa)**, o teste de diluição é pessimista: rodar também
   `python3 scripts/maturity_ladder.py state/portfolio.json --amount [aporte] --months 24` e ler a
   escada de vencimentos. Vencimento tira dinheiro do sleeve sem venda, sem IR e sem spread.
3. Comparar as duas leituras e dizer qual vale: "só diluição" ou "diluição + vencimentos". Se elas
   divergirem, a segunda manda.
4. Se algum sleeve acima da banda levar mais de 36 meses para voltar à banda mesmo com vencimentos:
   declarar **desvio estrutural** e colocar na mesa a decisão explícita: aceitar, rever a política
   ou vender parte (com custo fiscal e de liquidez calculado). Se a venda entrar na mesa, usar
   `--months [horizonte]` para dimensionar o valor exato — vender a mais força recomprar depois.
5. Nunca recomendar "continue aportando" quando a aritmética mostra que o fluxo não corrige. E nunca
   mandar vender o ativo de maior cupom quando a tese declarada do investidor é queda de juros
   (`references/fixed-income-brazil.md`).

## Passo 6 — Risco e concentração

1. Concentração por ativo, emissor, setor e segmento de FII.
2. Sobreposição: ETF x ações, BDR x exterior, FII de papel x renda fixa, cripto via ETF x direta.
3. Reserva de emergência separada? Se o caixa do modelo for a única liquidez, sinalizar.
4. Rodar o estresse mínimo de `references/portfolio-management.md` e dizer se o investidor
   aguentaria sem venda forçada.
5. Carregar `references/brazil-tax-and-regulatory-checklist.md` **sempre que houver venda,
   realização de lucro, resgate, mudança de custódia, ou aporte em exterior/cripto**. Citar alíquota
   só com fonte verificada e data de consulta.

## Passo 7 — Aporte e execução

1. Rodar `python3 scripts/rebalance_contribution.py state/portfolio.json --amount [aporte]`.
2. Aplicar ticket mínimo por sleeve (schema). Resíduo fica em liquidez, com prazo para decidir.
3. Checar executabilidade: lote, fracionário, corretagem, spread, liquidez do ativo.
4. Aporte não é obrigação de comprar: se não houver candidato adequado, manter em liquidez e
   registrar o motivo e a data limite para decidir.

## Passo 8 — Comparação, registro e fechamento

1. Comparar com o snapshot anterior: o que mudou, o que foi executado, o que ficou pendente. Sem
   snapshot anterior, declarar "primeiro review" e registrar a linha de base — não inventar comparação.
2. Calcular performance ajustada por aportes, com a fórmula explícita e a ressalva de que o número é
   aproximado: `(V_fim − aportes_líquidos) / V_início − 1`. Não confundir com rentabilidade do ativo.
   Se não houver `V_início`, registrar "não calculável".
3. Preencher `templates/monthly-report.md` e salvar em `output/AAAA-MM-revisao.md` se o investidor
   quiser o arquivo; caso contrário, responder no chat no mesmo formato.
4. Acrescentar uma entrada em `state/decisions.md` usando `references/decision-log-template.md`.
5. Definir o próximo review e os gatilhos extraordinários (queda >15%, aporte grande, venda).
6. Fechar com as perguntas abertas — no máximo 5, priorizadas.

## Checklist final antes de responder

- [ ] A data de referência está explícita e é do investidor (não inventada).
- [ ] A ingestão foi reconciliada com o extrato (bruto e líquido testados) e a cobertura está declarada.
- [ ] Está claro se os pesos são pré ou pós-aporte (deve ser pós, declarado).
- [ ] Nenhum preço, yield ou alíquota foi inventado.
- [ ] Cada posição aparece em um único sleeve; o que ficou fora está em `unmapped` com motivo.
- [ ] ETF classificado pelo índice replicado, não pelo rótulo de mercado do extrato.
- [ ] Todo desvio fora da banda tem uma leitura (aceitar, corrigir no fluxo, vender, rever política).
- [ ] O teste estrutural foi rodado ou justificado; se o sobrepeso é renda fixa, a escada de vencimentos também.
- [ ] O plano de aporte respeita ticket mínimo e soma o valor do aporte (ou declara o resíduo).
- [ ] Há registro de decisão, próximos passos e próximo review.
