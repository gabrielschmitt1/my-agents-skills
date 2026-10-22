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
