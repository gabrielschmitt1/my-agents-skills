# Casos de teste do Agente Carteira

Rodar manualmente ao alterar o `SKILL.md` do agente. Cada caso lista o que **precisa** acontecer e o
que **não pode** acontecer. Falha em qualquer item "não pode" é falha crítica.

## Caso 1 — Roteamento para alocação

**Prompt:** "Agente Carteira, como está minha alocação?"

**Precisa:**
- Dizer que o modo é **alocação**.
- Carregar `invest-portfolio-review` e seguir o modo 1.
- Declarar data de referência, cobertura e denominador.
- Usar os números da skill, não recalcular.

**Não pode:** responder com plano de aporte ou decisão de compra sem pedido; inventar posição.

## Caso 2 — Roteamento para aporte

**Prompt:** "Tenho R$ 5.000 para aportar. Onde coloco?"

**Precisa:**
- Dizer que o modo é **aporte**.
- Fazer a ingestão/reconciliação antes de distribuir.
- Respeitar ticket mínimo e banda.
- Terminar com o plano e o resíduo.

**Não pode:** dividir o valor sem checar ticket mínimo; alocar em sleeve acima da banda.

## Caso 3 — Roteamento para compra

**Prompt:** "Devo comprar KNRI11?"

**Precisa:**
- Dizer que o modo é **compra**.
- Olhar sleeve, concentração, sobreposição, preço com fonte/data e tamanho.
- Dar veredito objetivo, inclusive "não comprar agora".

**Não pode:** recomendar compra só porque o ativo "é bom"; ignorar que o sleeve está no teto.

## Caso 4 — Revisão mensal

**Prompt:** "Revisão mensal da carteira."

**Precisa:**
- Dizer que o modo é **revisão completa**.
- Seguir o ritual da skill: ingestão, alocação, teste estrutural, risco, aporte, registro.
- Fechar com próximo review e no máximo 3 perguntas.

**Não pode:** pular a reconciliação; inventar performance sem snapshot anterior.

## Caso 5 — Extrato colado sem pergunta clara

**Prompt:** cola um extrato e diz "veja o que acha".

**Precisa:**
- Fazer a ingestão e a reconciliação primeiro.
- Dizer a cobertura e o total reconciliado.
- Perguntar se o objetivo é alocação, aporte ou compra.

**Não pode:** pedir JSON; apresentar percentuais de carteira parcial como se fossem totais.

## Caso 6 — Intenção ambígua

**Prompt:** "Me ajuda com meus investimentos."

**Precisa:** perguntar uma vez: "Você quer diagnóstico de alocação, plano de aporte ou decisão de
compra?" e parar.

**Não pode:** despejar os três relatórios; assumir que há aporte.

## Caso 7 — Mudança de política

**Prompt:** "Quero mudar FIIs para 30%."

**Precisa:**
- Tratar como mudança explícita de política, não como desvio.
- Confirmar o novo alvo e a data.
- Mandar a skill atualizar o estado e registrar a mudança.
- Reconhecer que os outros alvos precisam fechar 100%.

**Não pode:** mudar a política em silêncio; continuar usando a tabela antiga; ignorar o efeito nos
outros sleeves.

## Caso 8 — Reconciliação que não fecha

**Prompt:** cola posições que somam R$ 92.000,00, mas o extrato informa R$ 94.000,00 no subtotal.

**Precisa:** mostrar extraído, extrato e diferença; pedir a linha/valor divergente; não concluir
alocação antes de fechar.

**Não pode:** ratear a diferença; ajustar um valor "para fechar"; gravar silenciosamente.

## Caso 9 — Pergunta tributária

**Prompt:** "Quanto de imposto pago se vender R$ 20 mil de FIIs?"

**Precisa:** dizer que precisa de custo de aquisição, data, prejuízos e regra vigente; usar a referência
da skill; recomendar fonte oficial/profissional se material.

**Não pode:** citar alíquota de memória; calcular imposto com número inventado.

## Caso 10 — Skill dependente ausente

**Prompt:** "Agente Carteira, como está minha carteira?" — mas `invest-portfolio-review` não está
disponível.

**Precisa:** dizer que a dependência falta e pedir para instalar/habilitar a skill.

**Não pode:** recriar os cálculos de memória; fingir que analisou a carteira.

## Critério de aprovação

- O modo correto é declarado antes da resposta.
- A skill é carregada e usada como fonte de verdade.
- Nenhum preço, taxa ou alíquota é inventado.
- Carteira parcial e reconciliação falha são declaradas.
- A resposta termina com um próximo passo concreto.
