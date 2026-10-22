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

### Quando o sleeve sobrepeso é a renda fixa

O teste acima é pessimista nesse caso: ele supõe o sleeve congelado. Títulos vencem, e **vencimento é
rebalanceamento sem venda, sem IR antecipado e sem spread** — o dinheiro sai do sleeve sozinho.

1. Rodar `python3 scripts/maturity_ladder.py state/portfolio.json --amount [aporte] --months 24`.
2. Ler a escada por ano e o caminho do peso: com vencimentos, o K1 cai mais rápido que a diluição pura.
3. Só então decidir entre **esperar** (fluxo + vencimentos), **vender** (com tamanho calculado) ou
   **aceitar** o desvio.
4. Uma carteira pode sair de 43% para 20% de renda fixa sem vender um papel, se a escada concentrar
   vencimentos nos próximos 12–24 meses. Verificar antes de propor venda.
5. Ao mesmo tempo, evitar o excesso oposto: se os vencimentos passarem do alvo, o sleeve fura o piso.
   Quando o K1 chega ao alvo, volta a receber parte do fluxo (modo manutenção).

O tamanho da venda, quando ela é necessária, tem fórmula fechada:
`venda = (caixa − vencimentos no horizonte) − alvo × (total + aporte × meses)`.
O script já devolve esse número; vender mais que isso obriga a recomprar RF depois.

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

Antes de vender, esgotar nesta ordem: **vencimentos** (saem sem custo), **aportes** (diluem),
**proventos** (redirecionar), e só então **venda**. Se a venda for o caminho:

- Calcular o **tamanho** que leva o sleeve ao alvo no horizonte desejado — não vender "para baixar o
  percentual". Vender a mais obriga a recomprar, possivelmente a preço pior.
- Escolher **qual** ativo sai por carry líquido e prazo, não pela cor da tela
  (`references/fixed-income-brazil.md`).
- Declarar o custo: IR, spread, taxa contratada perdida, e o efeito no risco de crédito.
- Registrar a venda como evento **de transição**, com data e critério. Sem isso, a carteira vira
  negociação recorrente em vez de política.
- Depois de corrigido o desvio, voltar ao modo manutenção: rebalancear por fluxo, vender só se um
  sleeve furar a banda por dois trimestres consecutivos e o fluxo não corrigir em seis meses.

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
