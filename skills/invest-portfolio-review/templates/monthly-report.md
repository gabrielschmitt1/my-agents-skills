# Revisão mensal — [AAAA-MM]

> Regra: dado ausente vira "não informado" + pergunta. Nunca estimar preço, saldo ou alíquota para preencher tabela.
> Salvar a versão preenchida em `output/AAAA-MM-revisao.md` (não versionar) e o registro da decisão em `state/decisions.md`.

## 1. Cabeçalho

- **Data da revisão:** [AAAA-MM-DD]
- **Data de referência dos saldos:** [AAAA-MM-DD] (se diferente de hoje, dizer a defasagem)
- **Fonte dos dados:** [extrato do banco/corretora colado em AAAA-MM-DD]
- **Cobertura:** [completa | parcial] — se parcial, o que falta: [ ]
- **Reconciliação da ingestão:** extraído R$ [ ] × extrato R$ [ ] → diferença R$ [ ]
- **Moeda:** BRL
- **Denominador:** ativos financeiros investíveis, **pós-aporte do mês**
- **Fora do modelo:** reserva de emergência R$ [ ], imóvel próprio, previdência, dívidas
- **ID do review:** [AAAA-MM-01]

## 2. Snapshot

- **Total investido nos seis sleeves (pós-aporte):** R$ [ ]
- **Fora dos sleeves (`unmapped`, ex.: linha não classificada):** R$ [ ] — [motivo]
- **Aporte/retirada do mês:** R$ [ ] (entrada: [data])
- **Qualidade dos dados:** [alta | média | baixa] — critério usado: [ ]
- **Ativos sem cotação atual:** [lista ou "nenhum"]

| Classe | Valor (R$) | Peso | Alvo | Desvio | Gap (R$) | Banda | Situação |
|---|---:|---:|---:|---:|---:|---|---|
| Caixa / RF (K1) | | | 20% | | | 15–25% | |
| FIIs (R) | | | 20% | | | 15–25% | |
| Ações BR (A) | | | 25% | | | 20–30% | |
| Cripto (K2) | | | 5% | | | 0–7% | |
| Exterior (E) | | | 25% | | | 20–30% | |
| Diversos (D) | | | 5% | | | 2–8% | |

> Gap negativo = acima do alvo; positivo = falta para o alvo. Os seis sleeves são sempre ativos; D é o
> catch-all (ouro, commodities, negócio próprio, alternativas) e não há renormalização.

## 3. Mudanças desde o último review

- Aportes/retiradas: [ ]
- Ativos comprados/vendidos: [ ]
- Mudanças de preço relevantes (>10%): [ ]
- Sleeves que cruzaram banda: [ ]
- Decisões anteriores que venceram ou foram invalidadas: [ ]

## 4. Teste de desvio estrutural

> `python3 scripts/structural_drift.py state/portfolio.json --amount [aporte]`

| Classe acima da banda | Peso | Total necessário | Crescimento | Meses |
|---|---:|---:|---:|---:|
| [ ] | | | | |

**Conclusão:** [o fluxo corrige em X meses | desvio estrutural — decidir entre aceitar ou rever a política/vender]

## 5. Riscos

- Concentração por ativo/setor: [ ]
- Sobreposição entre sleeves (ETF x ações, BDR x exterior, FII de papel x RF): [ ]
- Crédito/emissor (RF, FII de papel): [ ]
- Liquidez e reserva de emergência: [ ]
- Câmbio: [ ]
- Tributário (só com fonte verificada na data): [ ]
- Estresse: carteira com ações −30%, FIIs −20%, cripto −60%, exterior −30% + câmbio → perda aproximada R$ [ ] ([ ]% do total). Tolerável sem venda forçada? [ ]

## 6. Plano de aporte (se houver aporte no mês)

> `python3 scripts/rebalance_contribution.py state/portfolio.json --amount [aporte]`

| Destino | Valor (R$) | Ativo/candidato | Ticket mínimo ok? | Por quê |
|---|---:|---|---|---|
| | | | | |

- Resíduo em liquidez: R$ [ ]
- Condições que mudam o plano: [ ]
- O que **não** fazer agora: [ ]

## 7. Performance do mês

- Variação da carteira no mês (ajustada por aportes): [ ]% — fórmula `(V_fim − aportes) / V_início − 1`
- V_início (data): R$ [ ] | V_fim (data): R$ [ ] | Aportes líquidos: R$ [ ]
- Benchmarks: CDI [ ]%, Ibovespa [ ]%, IFIX [ ]%, S&P 500 em BRL [ ]%
- Primeiro review sem snapshot anterior: "não calculável" (não estimar).
- Ressalva: [ ] meses é prazo curto para julgar a estratégia; comparar sleeves em janelas equivalentes.

## 8. Decisão registrada

- Decisão: [ ]
- Sleeve/ativo e valor: [ ]
- Tese e evidência: [ ]
- Riscos principais e o que invalidaria: [ ]
- Revisar em: [AAAA-MM-DD] ou se [gatilho]

## 9. Fontes e perguntas abertas

- Fontes usadas (com data de consulta): [ ]
- Fatos vs. premissas vs. julgamento: [ ]
- Perguntas para o investidor: [ ]
- Próximo review: [AAAA-MM-DD]

## 10. Decisão de compra (se houver)

- **Ativo e sleeve:** [ ]
- **Peso atual do sleeve / alvo / banda:** [ ] / [ ] / [ ]
- **Sobreposição com o que já tenho:** [ ]
- **Preço e valuation (fonte + data):** [ ]
- **Tamanho, ticket e liquidez:** [ ]
- **Veredito:** [comprar | comprar parcialmente | não comprar agora | só se ...]
- **O que mudaria a resposta:** [ ]
