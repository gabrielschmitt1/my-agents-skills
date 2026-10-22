# Caixa e renda fixa no Brasil

O sleeve K1 é para liquidez e baixa volatilidade. Nem toda renda fixa é caixa: um título longo com
marcação a mercado pode cair 10%+ se os juros subirem.

## Ficha por instrumento

Registrar: emissor, conglomerado, indexador (CDI/Selic, IPCA, prefixado), taxa bruta e líquida,
vencimento, liquidez (D+0, D+1, no vencimento), tributação, taxas, exposição a marcação a mercado,
risco de crédito, elegibilidade ao FGC e concentração no emissor.

## Comparações que importam

- **Retorno líquido real**, não taxa bruta de propaganda.
- Prefixado x pós x IPCA: qual risco cada um cobre (juro, inflação, ambos).
- Duration: prazo até o vencimento não é o mesmo que duration.
- Liquidez: Tesouro Selic resgata em D+1; CDB com liquidez diária tem condições; LCA/LCI costuma ter
  carência. Reserva de emergência precisa de liquidez real, não de promessa.

## Carry líquido: converta tudo para a mesma régua

Comparar 14,15% prefixado com 92% do CDI exige converter para **taxa líquida de IR**, porque o isento
não paga imposto e o tributado paga. Sem isso a comparação engana.

| Indexador | Taxa bruta | Líquida |
|---|---|---|
| CDI/Selic | `pct_do_indexador × CDI` | isento: igual · tributado: × (1 − IR) |
| Prefixado | `taxa` | × (1 − IR) |
| IPCA+ | `taxa real` | × (1 − IR) — só vira nominal com inflação assumida |

Equivalência prática: **isento a X% do CDI = tributado a X ÷ (1 − IR) do CDI.** Com IR de 15%,
92% do CDI isento equivale a 108,2% do CDI tributado. É comum uma LCA isenta render mais, líquida, do
que um CDB prefixado de taxa nominal mais alta — e é isso que decide qual papel vender primeiro.

`python3 scripts/maturity_ladder.py state/portfolio.json --cdi 13.90` calcula essa coluna. As taxas de
referência (CDI, Selic, inflação) são sempre informadas pelo investidor ou por fonte com data: o script
se recusa a inventar.

## Qual renda fixa vender primeiro

Quando o sleeve K1 está acima da banda e a decisão é vender (não apenas esperar vencimento):

1. **Nunca o papel de maior cupom se a tese é queda de juros.** Um prefixado de 14,4% captura a queda
   uma única vez (o cupom travado é o teto do ganho); vendê-lo para comprar ações é coerente, vendê-lo
   e recomprar juro menor depois não é.
2. Ordenar por **carry líquido crescente**: os de menor taxa líquida saem primeiro.
3. Preferir o **prazo mais longo entre os de menor cupom** — é o que trava capital por mais tempo com
   o pior retorno.
4. Preservar isentos (LCA/LCI/CRI/CRA) e IPCA+: o isento vence o tributado na régua líquida, e o IPCA+
   é o único hedge de inflação da carteira.
5. Calcular o **tamanho exato** da venda: `scripts/maturity_ladder.py --months N` informa quanto vender
   hoje para o caixa aterrissar no alvo em N meses. Vender mais que isso obriga a recomprar RF depois,
   possivelmente a taxa menor.
6. Custo real da venda: IR já provisionado (sai do saldo líquido do extrato), spread de resgate
   antecipado e a taxa contratada que se abre mão. Confirmar com a instituição se o resgate sai na curva.


## FGC e crédito

Cobertura é por CPF e por conglomerado financeiro, com limite e condições vigentes. Verificar a regra
atual no site do FGC na data da revisão. FGC cobre quebra da instituição, não cobre oportunidade,
liquidez nem inflação. Emissor pequeno pagando muito acima do mercado é sinal de risco, não de
esperteza.

## Papel do caixa

Separar três coisas: reserva de emergência (fora do modelo, se possível), caixa de oportunidade
(para aportes e rebalanceamento) e caixa estratégico (os 20% do sleeve). Se os três estiverem no mesmo
saldo, o desvio do sleeve fica subestimado.

## Dados

Taxas e preços: Tesouro Direto, extratos e instituições. Séries de CDI/Selic/IPCA: Banco Central.
Ver `data-sources.md`.
