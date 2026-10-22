# Gestão da carteira e rebalanceamento

## Processo mensal

O passo a passo completo está em `monthly-review.md`. Resumo:

1. Atualizar valores e registrar a data de referência.
2. Registrar aportes/retiradas do mês.
3. Classificar cada posição em um sleeve primário.
4. Calcular pesos **pós-aporte**: `peso = valor do sleeve / total pós-aporte`.
5. Comparar com alvo: desvio em p.p. e gap em R$.
6. Rodar o teste de desvio estrutural.
7. Revisar risco, concentração, sobreposição e tributo.
8. Decidir aporte, registrar e marcar o próximo review.

## Denominador

Sempre **pós-aporte do mês**, e sempre declarado. Se o aporte ainda não foi investido, ele entra no
caixa. Comparar pré-aporte com alvo pós-aporte produz desvio falso.

## Teste de desvio estrutural

Antes de dizer "aporte mais no sleeve X", verificar se o fluxo realmente corrige:

- Sleeve **acima** da banda, sem vender: o peso cai por diluição.
  `total necessário = valor do sleeve / limite superior da banda`.
  `meses ≈ (total necessário − total atual) / aporte mensal`.
- Sleeve **abaixo** da banda: `gap = limite inferior × total − valor do sleeve`;
  `meses ≈ gap / aporte mensal` (só se 100% do aporte for para ele).

Se a correção levar mais de ~36 meses, é **desvio estrutural**: a decisão real é aceitar o desvio,
rever a política (ex.: assumir 35% em FIIs porque a renda mensal é objetivo) ou vender parte,
com custo fiscal e de liquidez calculado. "Continue aportando" não é resposta quando a aritmética
mostra que não fecha.

## Priorização de aporte

1. Ordenar por gravidade: fora da banda > distância até o alvo > valor em R$.
2. Alocar proporcionalmente ao déficit pós-aporte, respeitando ticket mínimo.
3. Não alocar em sleeve sobrepeso, mesmo que o ativo esteja barato — nesse caso o sleeve não é o
   problema, o ativo é.
4. Se não houver candidato adequado no sleeve carente, manter em liquidez com prazo para decidir.
   Forçar compra ruim para bater percentual é pior que ficar temporariamente fora do alvo.

## Bandas

Faixas de revisão, não comandos de trade:

| Sleeve | Banda |
|---|---|
| K1 Caixa | 15–25% |
| R FIIs | 15–25% |
| A Ações BR | 20–30% |
| K2 Cripto | 0–7% |
| E Exterior | 20–30% |
| D Diversos | 2–8% |

A banda de cripto é assimétrica de propósito (piso 0, teto 7): a ausência de cripto é uma escolha
válida; o excesso não é. As demais são simétricas em torno do alvo.

## Venda

Considerar venda apenas quando: o fluxo não corrige em prazo razoável; a concentração é material;
a tese do ativo se deteriorou; a necessidade de liquidez mudou; ou o benefício supera custo fiscal,
corretagem e spread. Venda parcial é preferível a zerar posição por desvio de percentual.

## Performance

- Usar retorno total (com proventos), não variação de preço.
- Separar performance de efeito de aportes e retiradas.
- Comparar sleeve com benchmark adequado e em janelas iguais (CDI para caixa, IFIX para FIIs,
  Ibovespa/IDIV para ações, S&P 500 em BRL para exterior, BTC para cripto).
- Um mês não avalia estratégia de longo prazo. Olhar 12m/36m e o desvio-padrão.

## Estresse (premissas, não previsões)

Testar no mínimo: ações −30%, FIIs −20%, cripto −60%, exterior −30% com movimento cambial adverso,
evento de crédito/liquidez na renda fixa. Calcular a perda combinada em R$ e em % do patrimônio e
responder: o investidor aguentaria sem venda forçada? Se não, a alocação está agressiva para ele,
independentemente de estar "no alvo".
