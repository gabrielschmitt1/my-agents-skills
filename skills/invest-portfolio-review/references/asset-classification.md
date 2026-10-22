# Classificação de ativos por sleeve

Regra de ouro: classificar pelo **que o ativo é**, não pela aba em que o banco o colocou. "Renda
Variável" no extrato costuma juntar ações, ETFs de índices diferentes, ouro e FIIs.

## Árvore de decisão

1. É fundo imobiliário listado (FII)? → **R (real_estate_fiis)**
2. É ETF? → olhar o índice/cesta:
   - ações brasileiras (Ibovespa, IDIV, small caps BR, setorial BR) → **A**
   - ações/índices estrangeiros (S&P 500, Nasdaq, mundo, Europa) → **E**
   - ouro, commodity → **D (diversos)**
   - cripto → **K2**
3. É BDR? → **E**
4. É ação brasileira? → **A**
5. É renda fixa (CDB, LCA, LCI, CRI, CRA, Tesouro, fundo DI/RF)? → **K1**
6. É cripto (direta ou ETF de cripto)? → **K2**
7. É participação em negócio privado, private equity ou capital de oportunidade? → **D**
8. Não deu para identificar? → **não classificado**, perguntar. Nunca chutar para "fechar" a conta.

## Tabela de referência (confirmar quando material)

**Não confie no rótulo de mercado do extrato.** Corretoras marcam "BRA" ou "B3" para *onde o ativo é
negociado*, não para o que ele expõe. TECK11 negocia na B3 e é 100% exterior; GOLD11 negocia na B3 e é
commodity. O que define o sleeve é o índice ou a cesta replicada, não a bolsa nem a aba.

| Ticker | Nome típico | Sleeve | Observação |
|---|---|---|---|
| BBOV11 | BB ETF Ibovespa | A | Mesmo índice do BOVA11 → sobreposição |
| BOVA11 | iShares Ibovespa | A | Mesmo índice do BBOV11 → sobreposição |
| DIVD11 | IT Now IDIV | A | Índice de dividendos; sobrepõe ações BR |
| IVVB11 | iShares S&P 500 | E | Exposição cambial embutida |
| GOLD11 | Trend Ouro | D | Commodity/ouro; não é ação nem exterior |
| TECK11 | Itaú NYSE FANG+ | **E** | Replica as 10 big techs dos EUA, com variação cambial. Não é ação brasileira |
| BTLG11 | BTG Logística | R | Tijolo/logística |
| BTLG12 | BTG Logística (classe residual) | R | Saldo irrelevante: marcar "residual" |
| HGBS11 | Hedge Brasil Shopping | R | Shoppings |
| HGLG11 | Pátria Logística | R | Logística |
| HGRU11 | Pátria Renda Urbana | R | Renda urbana |
| IRIM11 | Iridium | R | Confirmar tijolo x papel no informe |
| KNCR11 | Kinea Crédito Imobiliário | R | Papel/CRI — concorre com RF de crédito |
| KNHF11 | Kinea Hedge Fund | R | Híbrido — confirmar estratégia |
| KNRI11 | Kinea Renda Imobiliária | R | Tijolo |
| KNSC11 | Kinea Securities | R | Papel — confirmar |
| MXRF11 | Maxi Renda | R | Papel |
| PVBI11 | VBI Prime Properties | R | Tijolo |
| RECR11 | REC Recebíveis | R | Papel |
| VISC11 | Vinci Shopping Centers | R | Shoppings |
| XPLG11 | XP Log | R | Logística |
| XPML11 | XP Malls | R | Shoppings |
| LCA/CDB/LCI | renda fixa bancária | K1 | Ver bruto x líquido e FGC |

Tickers mudam de estratégia, e nomes truncados enganam. Em dúvida com valor material, consultar o
informe mensal do fundo ou o regulamento do ETF (`data-sources.md`).

## Concentração que a tabela esconde

- **Mesmo índice:** BBOV11 + BOVA11 = uma aposta só no Ibovespa. Somar os dois para medir concentração.
- **Mesma gestora:** KNCR11 + KNHF11 + KNRI11 + KNSC11 = risco operacional e de crédito da mesma casa.
- **Mesmo segmento:** shoppings (HGBS11, VISC11, XPML11) e logística (BTLG11, HGLG11, XPLG11) são
  fatores de risco, não diversificação.
- **FII de papel x renda fixa:** KNCR11, RECR11, MXRF11 e IRIM11 têm risco de crédito parecido com
  CDB/CRI. Contar os dois no mesmo saco para medir exposição a crédito.
- **ETF x ações:** um ETF de Ibovespa já contém as ações que você tem na carteira.
- **TECK11 x IVVB11:** as 10 big techs do FANG+ são o topo do S&P 500. Quem tem os dois mede
  concentração em mega-cap dos EUA, não diversificação geográfica.
- **Aluguel de ações:** a posição continua sua, mas com risco de contraparte e devolução. Anotar.

## Diversos (D)

O KRAKED tem um sleeve para o que não é K1, R, A, K2 nem E: **D (diversos)**. Entram ali ouro,
commodities, negócio próprio, private equity, capital de oportunidade, derivativos e alternativos.

1. Classificar o ativo em D, não em “outros” nem em A/E por conveniência.
2. Reportar o percentual, a tese e o papel do ativo (hedge, aposta, reserva de valor).
3. O que não for identificável vai para `unmapped`, com motivo — nunca chutar para fechar a conta.

## Registro

Cada posição tem **um** sleeve primário. Exposição secundária (ex.: ETF de Brasil que tem Vale e Petro)
vai em nota, não em outro sleeve. Em caso de dúvida, perguntar — errar a classificação contamina todos
os desvios.
