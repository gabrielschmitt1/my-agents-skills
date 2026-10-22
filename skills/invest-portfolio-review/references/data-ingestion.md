# Ingestão de dados colados (extrato, posições, print transcrito)

O investidor **cola** os dados do banco/corretora. A skill extrai, confere, classifica e grava. Ele nunca
edita JSON.

## 1. Formato de entrada aceito

Qualquer texto com posições: extrato de custódia, tela de carteira, CSV colado, transcrição de print.
Formatos comuns no Brasil:

- **Renda variável:** bloco com subtotal (`29,9% Renda Variável R$ 40.000,00`), depois grupos
  (`ETFs`, `Fundos listados`, `Aluguel`) e linhas com ticker, nome, quantidade, preço médio, proventos,
  preço de mercado, resultado e saldo bruto.
- **Renda fixa:** subtotal (`70,1% Renda Fixa R$ 94.000,00`), grupos (`LCA`, `CDB`, `LCI`) e linhas com
  emissor, vencimento, taxa, "Preço e Qtd", saldo líquido e saldo bruto.
- **Caixa:** saldo em conta/corretora, muitas vezes fora das tabelas.

## 2. Extração — regras de leitura

| Campo | Como ler | Cuidado |
|---|---|---|
| Ticker | `[A-Z]{4}\d{2}` (B3), ou símbolo de cripto | Nome truncado com "…" não muda o ticker |
| Quantidade | inteiro; `3.000` = três mil | Separador de milhar é ponto |
| Preço | `R$ 1.234,56`; RF pode ter 4 casas (`R$ 1.134,2833`) | Ponto = milhar, vírgula = decimal |
| Preço médio | custo unitário | Não é o preço de mercado |
| Preço de mercado | valor unitário atual | É o que entra na alocação |
| Saldo bruto | quantidade × preço de mercado | **Valor usado na alocação** |
| Saldo líquido | após IR/IOF, quando o extrato mostra | Usar para liquidação e decisão de venda |
| Proventos | renda já recebida | Não soma no patrimônio; é histórico |
| Resultado c/ proventos | performance | Não é peso de carteira |
| Aluguel (doador) | ações emprestadas | A posição continua sua; anotar risco de contraparte |
| Linhas empoeiradas | saldo < R$ 1,00 | Manter, marcar "residual", não distorcer análise |

Números colados podem quebrar linha no meio (`R$ 19,80` e `R$ 415,90` em linhas separadas). Reconstruir
pela ordem das colunas do bloco, não pela posição na linha.

## 3. Reconciliação — obrigatória antes de gravar

1. Somar `market_value_brl` das posições extraídas, **por grupo** (ETFs, FIIs, LCA, CDB, LCI, Aluguel).
2. Comparar cada grupo com o subtotal do extrato e, depois, o total. O campo `reconciliation` do JSON faz
   essa checagem e recusa gravar se um grupo não fechar.
3. **Antes de acusar linha faltante, testar as duas colunas.** Extratos de renda fixa costumam
   subtotalizar pelo **saldo bruto**, enquanto a linha mostra líquido e bruto. Somar as duas colunas e
   ver qual fecha com o subtotal.
4. Tolerância: **R$ 1,00**.
5. Divergência maior → **não gravar**. Mostrar:

   ```
   Extraído:  R$ 92.000,00
   Extrato:   R$ 94.000,00
   Diferença: R$ 2.000,00
   ```

6. Pedir a linha faltante. **Nunca** ajustar uma posição, ratear a diferença ou arredondar para fechar.
7. Se o investidor confirmar que o extrato está incompleto, gravar com `data_coverage: "parcial"` e
   repetir o aviso em toda conclusão.

Exemplo: um extrato trazia LCA R$ 10.000,00 + CDB R$ 80.000,00 + LCI R$ 4.000,00 = R$ 94.000,00.
Somando o **líquido** dos CDBs o total dava R$ 78.000,00 e a diferença de R$ 2.000,00 parecia linha
faltante; somando o **bruto**, fechava exatamente. Conferir as duas colunas evita acusação falsa e
gravação com valor errado.

## 4. Bruto x líquido (renda fixa)

- **Alocação:** saldo **bruto** (valor de mercado).
- **Liquidação/venda:** saldo **líquido** (após IR), que pode ser menor em CDB prefixado, por exemplo.
- Registrar os dois quando existirem; não misturar na mesma coluna.
- LCA/LCI isentos normalmente têm líquido = bruto; ainda assim conferir.
- `net_value_brl` guarda o líquido; `market_value_brl` guarda o bruto.

## 5. Percentuais do extrato como pista de cobertura

Os percentuais por grupo (ex.: "54,4% Renda Variável", "40,9% Renda Fixa") permitem estimar o total
real da carteira e detectar se falta uma seção:

```
total implícito = soma das seções coladas / soma dos percentuais dessas seções
faltante = total implícito − soma das seções coladas
```

Se 60% + 35% = 95% e as seções somam R$ 100.000,00, o total implícito é R$ 105.263,16 e faltam cerca
de R$ 5.263,16 (5%) — provavelmente caixa ou outra conta. **Perguntar** o que é; não assumir que é zero
nem inventar a posição. Até a resposta, `data_coverage: "parcial"`.

## 6. Classificação por sleeve

A aba do banco **não** é o sleeve KRAKED. "Renda Variável" costuma misturar ETFs de ações, ETFs de
exterior, ouro e FIIs. Reclassificar por sleeve com `asset-classification.md`:

- ETF de Ibovespa/IDIV/ações BR → **A**
- ETF de S&P 500/exterior → **E**
- ETF de ouro/commodity → **D (diversos)**; nunca somar em A ou E por estar na mesma aba
- FII de tijolo ou papel → **R**
- CDB/LCA/LCI/Tesouro/fundo de RF → **K1**
- Cripto direta ou ETF de cripto → **K2**
- Negócio privado, private equity ou capital de oportunidade → **D**

## 7. JSON normalizado (entrada do `save_portfolio.py`)

```json
{
  "as_of": "2026-10-22",
  "source": "extrato BTG 22/10/2026 (colado)",
  "data_coverage": "completa",
  "contribution_month_brl": 0,
  "positions": [
    {
      "symbol": "BOVA11",
      "name": "iShares Ibovespa",
      "group": "ETFs",
      "primary_sleeve": "brazilian_equities",
      "quantity": 50,
      "price_brl": 200.99,
      "market_value_brl": 10049.50,
      "cost_basis_brl": 10046.50,
      "income_brl": 0,
      "liquid": true,
      "notes": "alugado como doador até 23/11/2026"
    },
    {
      "symbol": "GOLD11",
      "name": "ETF Ouro",
      "group": "ETFs",
      "primary_sleeve": "diversos",
      "quantity": 60,
      "price_brl": 82.41,
      "market_value_brl": 4944.42,
      "liquid": true,
      "notes": "ouro/commodity: hedge, não motor de retorno"
    }
  ],
  "unmapped": [
    {"item": "Aluguel de ações", "group": "Aluguel", "value_brl": 0.14, "reason": "renda residual, não é posição"}
  ],
  "reconciliation": [
    {"group": "ETFs", "expected_brl": 98955.44},
    {"group": "FIIs", "expected_brl": 32347.60},
    {"group": "CDB", "expected_brl": 84288.45}
  ]
}
```

- `group` é o bloco do extrato (ETFs, FIIs, LCA, CDB, LCI, Aluguel). `reconciliation` compara o
  subtotal de cada grupo com a soma das linhas daquele grupo — pega uma linha perdida que o total geral
  esconderia. Se um grupo não existir, o extraído é zero e a divergência aparece.
- `unmapped` é obrigatório quando algo fica fora do modelo: o total do extrato continua reconciliando,
  mas o valor não entra em nenhum sleeve. Nunca esconder.

## 8. Depois de gravar

1. `save_portfolio.py` valida, faz backup do estado anterior em `state/history/` e mostra o diff.
2. Repetir a tabela normalizada na resposta, com `Total extraído`, `Total do extrato` e `Diferença`.
3. Dizer a cobertura: completa ou parcial.
4. Só então responder ao pedido (alocação, aporte ou compra).

## 9. Perguntas que valem (e as que não valem)

Perguntar apenas o que muda a conclusão:

- data de referência dos saldos;
- se há caixa livre não listado;
- se a carteira colada é completa ou parcial;
- se existe posição em D (ouro, negócio próprio, alternativas) e como ela deve ser tratada;
- se o valor é bruto ou líquido quando o extrato mostra os dois.

Não perguntar o que dá para extrair do texto. Não pedir para o investidor preencher schema.
