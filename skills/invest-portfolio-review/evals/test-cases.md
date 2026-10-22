# Casos de teste da skill

Rodar manualmente ao alterar `SKILL.md` ou os scripts. Cada caso lista o que **precisa** acontecer e o
que **não pode** acontecer. Falha em qualquer item "não pode" é falha crítica.

## Caso 1 — Sem carteira organizada

**Prompt:** "Kraken, quero fazer a revisão mensal. Não tenho os dados organizados, mas tenho uns 80 mil
em FIIs, 30 mil em ações, 10 mil em cripto, 20 mil em ETF de fora e 40 mil em renda fixa. Aportei 3 mil."

**Precisa:**
- Declarar que a análise é de sleeve, não de ativo, e por quê.
- Pedir a **data de referência** dos saldos.
- Dizer se os 3 mil já estão dentro dos saldos.
- Perguntar se os 40 mil incluem reserva de emergência.
- Perguntar se há ouro, commodities, negócio próprio ou alternativas (sleeve **D**). Se não houver,
  registrar D = 0 e tratar o gap de 5% como pendência de política, não de classificação.
- Terminar com no máximo 5 perguntas priorizadas.

**Não pode:** assumir a data de hoje como data dos saldos; inventar preço ou ticker; inventar ativo para
D; garantir retorno.

## Caso 2 — Revisão completa com aporte

**Prompt:** "Revisão mensal. Carteira em 30/09: caixa/RF 40.000; FIIs 80.000; ações BR 30.000; cripto
10.000; internacional 20.000; diversos 0. Aporte novo: 5.000. Onde aporto?"

**Precisa:**
- Usar os dados de `assets/portfolio.example.json` como referência de formato, sem copiar valores.
- Deixar explícito que o denominador é pós-aporte (total 185.000).
- Rodar o equivalente de `portfolio_allocation.py` e `rebalance_contribution.py` (ou reproduzir o cálculo
  e conferir).
- Apontar FIIs (43,2%) acima da banda; ações (16,2%), exterior (10,8%) e Diversos (0%) abaixo; caixa
  (24,3%) e cripto (5,4%) dentro.
- Rodar o teste estrutural: FIIs só voltam ao teto de 25% com ~R$ 320 mil de patrimônio (27 meses com
  aporte de R$ 5 mil).
- Plano de aporte: ações R$ 1.570,05; exterior R$ 2.536,23; Diversos R$ 893,72; nada para caixa, FIIs
  ou cripto. Se não houver ativo elegível em D, o valor fica em liquidez com prazo.
- Respeitar ticket mínimo; dizer o que não fazer agora.
- Fechar com registro de decisão e próximo review.

**Não pode:** reportar pesos pré-aporte como se fossem os únicos; inventar ativo para D; recomendar
venda sem citar custo fiscal e de liquidez; preencher a seção de fontes com cotação inventada.

## Caso 3 — Desvio estrutural

**Prompt:** "Tenho 45% em FIIs, 20% em ações, 25% em exterior, 10% em caixa, 0 em cripto e 0 em diversos.
Aporto R$ 1.000 por mês. Consigo voltar ao alvo só aportando?"

**Precisa:** mostrar a aritmética (total necessário = valor dos FIIs / 0,25), concluir que leva muitos
anos e apresentar as três opções: aceitar, rever a política ou vender parte com custo. D está abaixo do
alvo, mas é pequeno e não muda a conclusão estrutural de FIIs.

**Não pode:** responder apenas "aporte nos sleeves abaixo do alvo"; esconder que o fluxo não corrige.

## Caso 4 — Venda e tributo

**Prompt:** "Vou vender R$ 20 mil de FIIs para aportar em ações. Quanto vou pagar de imposto?"

**Precisa:** carregar `brazil-tax-and-regulatory-checklist.md`; dizer o que precisa saber (custo de
aquisição, data, prejuízos acumulados, regra vigente); recomendar verificação em fonte oficial e, se
material, profissional habilitado.

**Não pode:** citar alíquota ou isenção de memória; calcular imposto com número inventado.

## Caso 5 — Aporte pequeno e ticket mínimo

**Prompt:** "Tenho R$ 300 para aportar este mês. Onde coloco?"

**Precisa:** considerar ticket mínimo (ex.: cripto R$ 100, FII R$ 500); concentrar em 1–2 destinos
executáveis; se não couber, sugerir acumular em liquidez com prazo.

**Não pode:** dividir R$ 300 em seis frações inexequíveis; sugerir compra fracionada onde não existe.

## Caso 6 — Não é revisão mensal

**Prompt:** "O que você acha de CDB de banco médio pagando 110% do CDI?"

**Precisa:** responder a pergunta com o conteúdo de `fixed-income-brazil.md` (crédito, FGC, liquidez,
comparação líquida) e oferecer a revisão da carteira.

**Não pode:** despejar o relatório mensal inteiro nem exigir a carteira para responder uma dúvida pontual.

## Caso 7 — Ingestão de extrato com bruto e líquido

**Prompt:** cola um extrato com "Renda Variável R$ 40.000,00" e "Renda Fixa R$ 94.000,00", LCA R$ 10.000,00, LCI R$ 4.000,00 e 16 CDBs
cujo subtotal é R$ 80.000,00. Cada CDB mostra saldo líquido e bruto; a soma dos líquidos dá R$ 78.000,00
e a dos brutos, R$ 80.000,00. Pede "avalie minha alocação".

**Precisa:**
- Testar as duas colunas antes de concluir qualquer coisa e identificar que o subtotal usa o **bruto**.
- Gravar com saldo bruto na alocação e reportar o líquido (R$ 92.000,00 na RF) como valor de resgate.
- Repetir a tabela normalizada e o total reconciliado (R$ 134.000,00).
- Declarar a cobertura (completa ou parcial) e o que ficou fora dos sleeves (linha não classificada).

**Não pode:** acusar linha faltante por ter somado a coluna errada; gravar sem conferir; misturar bruto e
líquido na mesma coluna; pedir ao investidor para editar JSON.

## Caso 8 — Divergência que não fecha

**Prompt:** cola posições que somam R$ 92.000,00, mas o extrato informa R$ 94.000,00 no subtotal e nem o
bruto nem o líquido fecham.

**Precisa:** mostrar extraído, extrato e diferença; pedir a linha ou o valor divergente; oferecer gravar
como **parcial** somente se o investidor confirmar que o extrato está incompleto.

**Não pode:** ratear a diferença entre posições; ajustar um valor "para fechar"; gravar silenciosamente;
inventar a linha faltante.

## Caso 9 — Decisão de compra com sleeve no teto

**Prompt:** "Devo comprar KNRI11? Tenho 29% em FIIs e 12% em KNRI11."

**Precisa:** classificar KNRI11 em FIIs; mostrar que o sleeve está acima do teto (29% > 25%); calcular
a concentração no ativo e a sobreposição com Kinea/outros FIIs; comparar preço (P/VP, DY) com fonte e
data; dar veredito objetivo — provavelmente "não comprar agora" ou "só se reduzir outra posição".

**Não pode:** recomendar compra só porque o ativo "é bom"; ignorar que o sleeve está no teto; inventar
P/VP ou dividend yield; responder sem olhar a carteira.

## Caso 10 — Carteira parcial

**Prompt:** cola apenas a seção de renda variável e pergunta "como está minha alocação total?".

**Precisa:** gravar com `data_coverage: "parcial"`; dizer que os percentuais não representam a carteira
inteira; analisar o que dá (composição da RV, sobreposição, concentração) e pedir as seções faltantes
(renda fixa, caixa, exterior, cripto).

**Não pode:** apresentar percentual de RF, cripto ou exterior como se fossem zero; concluir que a
carteira está desbalanceada sem os dados faltantes; pedir JSON.

## Caso 11 — Aporte a partir do extrato colado

**Prompt:** cola o extrato e diz "tenho R$ 5.000 para aportar; para onde vai?".

**Precisa:** ingerir e reconciliar primeiro; rodar o plano com ticket mínimo; dizer o valor por sleeve e
o resíduo; explicar o que não comprar; registrar a decisão.

**Não pode:** pedir para o investidor montar o JSON; distribuir o aporte para sleeve acima da banda;
ignorar ticket mínimo; prometer retorno.

## Critério de aprovação

- Todos os casos: formato de saída completo quando for revisão; nenhum dado inventado; D classificado;
  denominador declarado; ingestão reconciliada antes de qualquer conclusão.
- Rodar `python3 -m unittest discover -s tests` antes de publicar qualquer alteração nos scripts.
