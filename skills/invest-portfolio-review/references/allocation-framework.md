# KRAKED: sleeves e política de alocação

## Os seis sleeves

**KRAKED** é a adaptação pessoal do KRAKEN: o antigo **N de Negócios** vira **D de Diversos**.

| Letra | Sleeve | Alvo | Banda | Papel |
|---|---|---:|---|---|
| K1 | Caixa / renda fixa | 20% | 15–25% | Liquidez, estabilidade, opcionalidade |
| R | Real Estate / FIIs | 20% | 15–25% | Exposição imobiliária e renda |
| A | Ações brasileiras | 25% | 20–30% | Crescimento local e dividendos |
| K2 | Criptoativos | 5% | 0–7% | Alternativo de alta volatilidade |
| E | Internacional | 25% | 20–30% | Diversificação geográfica e cambial |
| D | Diversos | 5% | 2–8% | Ouro, commodities, negócio próprio, alternativas |
| | **Total** | **100%** | | |

Duas sleeves usam a letra K. Em qualquer relatório, use **K1 (caixa)** e **K2 (cripto)** ou o nome
completo — nunca "K" sozinho.

## O que entra em D (Diversos)

D é o **catch-all dos seis sleeves**: entra ali o que não é K1, R, A, K2 nem E.

1. **Ouro e commodities** — GOLD11, exposição a ouro físico, ETFs de commodities.
2. **Negócio próprio / participação privada** — capital em empresa, sociedade, private equity.
3. **Capital de oportunidade** — aposta concentrada, alternativa ilíquida, Venture.
4. **Derivativos e estratégias estruturadas** — só se o investidor decidir operar; exigem payoff,
   perda máxima, margem e liquidez.
5. **Outros ativos alternativos** — o que não couber nos cinco sleeves anteriores.

**D não é lixeira.** Cada posição precisa de tese, valor conservador, limite de perda, prazo e critério
de saída. Ouro é hedge, não motor de retorno. Negócio próprio é ilíquido e não é reserva de emergência.

## Política pessoal x faixas públicas

Materiais públicos atribuídos a Leonardo Alves / Geração Dividendos descrevem: caixa **10–15%**,
FIIs **25%**, ações BR **25%**, cripto **1–5%**, exterior **25%**, negócios (o antigo N) **1–10%**. Essas faixas não
formam uma carteira única e somam mais de 100% nos limites superiores.

A política **KRAKED** é uma escolha pessoal declarada e **não** tenta caber nas faixas públicas:
caixa em 20% (acima da faixa original), FIIs em 20% (abaixo do original) e Diversos em 5%. O importante
é que os alvos somem 100% e que a política seja registrada no `state/portfolio.json`.

Nunca apresentar a política pessoal como "a alocação oficial do KRAKEN". Se o investidor quiser mudar
de novo, alterar `target_weights` e `bands` e registrar a data da mudança.

## Regras de cálculo

- Mesmo denominador para todos: **ativos financeiros investíveis, pós-aporte do mês**. Declarar o que
  ficou fora (reserva de emergência, imóvel, previdência, dívidas).
- Uma posição, um sleeve primário. Exposição secundária só em nota.
- Não contar caixa de corretora duas vezes (se já está no sleeve, não entra em outro).
- Reserva de emergência pode viver fora do modelo. Se estiver dentro de K1, separar
  "caixa de emergência" de "caixa de investimento" e dizer o valor de cada um.
- Os seis sleeves são **sempre ativos**. Não existe "N não aplicável" nem renormalização; D é um sleeve
  normal, com alvo de 5%.

## Dupla contagem

O material original fala em 80% "previdenciárias" / 20% "oportunidade" *dentro* de ações. Se você usar D
para ações de oportunidade listadas, o 80/20 dentro de A cria dupla contagem: o mesmo ativo não pode
estar em A e em D. Escolher um enquadramento e registrar.

## Leitura do portfólio

KRAKED é um framework de classificação e alocação, não uma garantia de correlação negativa nem uma
carteira ótima universal. Correlações mudam, especialmente em estresse: FIIs, ações BR, exterior,
cripto e ouro podem cair juntos. Alocação por sleeve não substitui análise de ativo.
