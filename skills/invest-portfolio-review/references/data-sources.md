# Fontes e disciplina de dados

Regra central: **preço, cota, taxa ou alíquota não se improvisa.** Se não há fonte acessível na hora,
pedir o valor ao investidor e registrar que o dado veio dele.

## Hierarquia

1. **Dado do investidor** (extrato, nota de corretagem, informe de rendimentos) — melhor para saldo e custo.
2. **Fonte primária** — B3, Tesouro Direto, Banco Central, Receita Federal, CVM, administrador do fundo,
   RI da empresa, exchange usada pelo investidor.
3. **Agregador** (Yahoo, brapi, CoinGecko, investidor10 etc.) — aceitável para preço de tela, nunca para
   fundamento, tributo ou regra regulatória.
4. **Notícia, vídeo, post, resumo de terceiro** — pista, não fonte. Nunca baseia número.

## Onde buscar cada coisa

| Dado | Fonte preferida | Observação |
|---|---|---|
| Ação/BDR/ETF na B3 | Home broker, extrato, site da B3 | Fechamento oficial; registrar data e hora |
| FII | Cota no site da B3 e informe mensal do fundo | P/VP e DY do informe, não de "site de FIIs" |
| Tesouro Direto | Site oficial do Tesouro | Preço e taxa do dia; título e vencimento |
| Renda fixa privada | Extrato/instituição | Marcar se é marcação a mercado ou curva |
| Câmbio | PTAX (Banco Central) | **Venda do dia útil anterior**; registrar a taxa usada |
| Cripto | Exchange do investidor; CoinGecko como referência | Registrar exchange e horário |
| CDI/Selic/IPCA | Banco Central | Série e data |
| Tributo/regra | Receita Federal, CVM, B3, FGC | Ver `brazil-tax-and-regulatory-checklist.md` |
| Fundamentos (ações/FIIs) | RI, informe mensal, CVM | Trimestral; não mensal |

## Regras de validade

- **Preço de mercado:** válido para o dia útil. Se a data de referência dos saldos for anterior,
  o relatório precisa dizer "pesos com preços de DD/MM".
- **Cota de fundo:** a do último fechamento divulgado.
- **Fundamento:** trimestral; nunca tratar como "atual" sem data.
- **Alíquota/tributo:** só com verificação na data da revisão. Se a regra mudou, dizer o que mudou.
- **Estimativa** (negócio privado, imóvel, ativo sem mercado): marcar como estimativa, com método e data.
  Estimativa nunca entra na mesma coluna de um preço de mercado sem aviso.

## Quando não há acesso a dados

1. Perguntar o valor e a data ao investidor.
2. Se ele não tiver, rodar a análise em nível de sleeve com os valores informados e declarar
   que a análise é de alocação, não de ativo.
3. Nunca preencher lacuna com número plausível. Uma tabela com "não informado" é aceitável;
   uma tabela inventada não é.

## Registro

No relatório, toda linha de fonte deve ter: **fonte + data/hora da consulta + valor**. Exemplo:
`HGLG11 — fechamento B3 30/09/2026 — R$ 154,20`.

Se a mesma informação aparecer em duas fontes com valores diferentes, registrar a divergência e
usar a mais primária.
