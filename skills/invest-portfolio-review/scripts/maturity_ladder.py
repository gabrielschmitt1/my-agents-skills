#!/usr/bin/env python3
"""Escada de vencimentos da renda fixa e caminho do peso do caixa.

Uso:
    python3 scripts/maturity_ladder.py state/portfolio.json --amount 5000
    python3 scripts/maturity_ladder.py state/portfolio.json --cdi 13.90 --sell 12601.54
    python3 scripts/maturity_ladder.py --example

Por que existe: `structural_drift.py` supõe que o sleeve sobrepeso fica congelado
e só cai por diluição. Quando o sleeve sobrepeso é a renda fixa isso é pessimista
demais — os vencimentos saem do sleeve sem venda, sem IR antecipado e sem spread.
Este script mostra a escada, o caminho real do peso e, se houver venda, o tamanho
que faz o caixa chegar ao alvo exatamente no prazo escolhido.

Premissas, sempre explícitas na saída: preços constantes, sem marcação a mercado,
aporte mensal recorrente, e nenhum reinvestimento em renda fixa enquanto o sleeve
estiver acima do alvo.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from portfolio_allocation import (  # noqa: E402
    BANDS,
    TARGETS,
    as_number,
    brl,
    load_sleeve_values,
    normalize_sleeve,
    pct,
    resolve_targets,
)

CASH = "cash_fixed_income"

INDEXER_ALIASES = {
    "cdi": "CDI",
    "pos": "CDI",
    "pos_fixado": "CDI",
    "pos-fixado": "CDI",
    "pós": "CDI",
    "pós-fixado": "CDI",
    "selic": "SELIC",
    "pre": "PRE",
    "pré": "PRE",
    "prefixado": "PRE",
    "pre_fixado": "PRE",
    "pré-fixado": "PRE",
    "ipca": "IPCA",
    "ipca+": "IPCA",
    "ipca_mais": "IPCA",
}

UNIT_BY_INDEXER = {
    "CDI": "% do CDI",
    "SELIC": "% da Selic",
    "PRE": "% a.a. bruto",
    "IPCA": "% a.a. real",
}


def normalize_indexer(raw: object) -> str | None:
    """Converte o indexador para CDI, SELIC, PRE ou IPCA."""
    if raw is None:
        return None
    key = str(raw).strip().lower().replace(" ", "_")
    if key in INDEXER_ALIASES:
        return INDEXER_ALIASES[key]
    raise ValueError(f"Indexador desconhecido: {raw!r}. Use CDI, Selic, pré ou IPCA.")


def parse_maturity(raw: object) -> date | None:
    """Aceita YYYY-MM-DD (e YYYY-MM). Sem data, o título fica fora da escada."""
    if raw in (None, ""):
        return None
    text = str(raw).strip()
    try:
        if len(text) == 7:
            year, month = text.split("-")
            return date(int(year), int(month), 1)
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"Vencimento inválido: {raw!r} (esperado YYYY-MM-DD).") from exc


def parse_bool(raw: object) -> bool:
    """LCA/LCI/CRI/CRA são isentos; o campo aceita true/false, sim/não, 1/0."""
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    return str(raw).strip().lower() in {"1", "true", "sim", "yes", "y", "s"}


def position_value(position: dict, index: int) -> float:
    """Valor de mercado da posição (bruto), igual à regra do portfólio."""
    if "market_value_brl" in position:
        return as_number(position["market_value_brl"], f"positions[{index}].market_value_brl")
    if "quantity" in position and "price_brl" in position:
        quantity = as_number(position["quantity"], f"positions[{index}].quantity")
        price = as_number(position["price_brl"], f"positions[{index}].price_brl")
        return quantity * price
    raise ValueError(f"Posição {index} precisa de 'market_value_brl' ou de 'quantity' + 'price_brl'.")


def load_fixed_income(data: dict) -> list[dict]:
    """Extrai as posições de renda fixa com vencimento, indexador e taxa."""
    positions = data.get("positions")
    if not isinstance(positions, list):
        raise ValueError(
            "A escada precisa de 'positions' (não de 'sleeves'): vencimento e taxa são "
            "propriedades do título, não do sleeve."
        )
    items: list[dict] = []
    for index, position in enumerate(positions):
        if not isinstance(position, dict):
            raise ValueError(f"Posição {index} inválida: esperado objeto.")
        if "primary_sleeve" not in position:
            raise ValueError(f"Posição {index} sem 'primary_sleeve'.")
        if normalize_sleeve(position["primary_sleeve"]) != CASH:
            continue
        items.append(
            {
                "symbol": str(position.get("symbol") or position.get("name") or f"RF-{index}"),
                "issuer": str(position.get("issuer") or ""),
                "value": position_value(position, index),
                "net_value": (
                    as_number(position["net_value_brl"], f"positions[{index}].net_value_brl")
                    if position.get("net_value_brl") is not None
                    else None
                ),
                "maturity": parse_maturity(position.get("maturity")),
                "indexer": normalize_indexer(position.get("indexer")),
                "rate_pct": (
                    as_number(position["rate_pct"], f"positions[{index}].rate_pct")
                    if position.get("rate_pct") is not None
                    else None
                ),
                "tax_exempt": parse_bool(position.get("tax_exempt")),
            }
        )
    return items


def add_months(reference: date, months: int) -> date:
    """Soma meses preservando o dia quando possível."""
    total = reference.month - 1 + months
    year = reference.year + total // 12
    month = total % 12 + 1
    day = reference.day
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1


def build_ladder(items: list[dict]) -> dict:
    """Agrupa os vencimentos por ano e separa o que não tem data."""
    total = sum(item["value"] for item in items)
    undated = sum(item["value"] for item in items if item["maturity"] is None)
    by_year: dict[int, float] = {}
    for item in items:
        if item["maturity"] is None:
            continue
        by_year[item["maturity"].year] = by_year.get(item["maturity"].year, 0.0) + item["value"]

    rows = []
    cumulative = 0.0
    for year in sorted(by_year):
        cumulative += by_year[year]
        rows.append(
            {
                "year": year,
                "value": by_year[year],
                "share_pct": (by_year[year] / total * 100) if total else 0.0,
                "cumulative_pct": (cumulative / total * 100) if total else 0.0,
            }
        )
    return {"total": total, "undated": undated, "rows": rows}


def maturities_within(items: list[dict], reference: date, months: int) -> float:
    """Soma o que vence entre a data de referência e o fim do horizonte."""
    limit = add_months(reference, months)
    return sum(
        item["value"]
        for item in items
        if item["maturity"] is not None and reference < item["maturity"] <= limit
    )


def month_buckets(items: list[dict], reference: date, months: int) -> dict[int, float]:
    """Distribui cada vencimento no mês em que cai, em índices 0-based.

    O mês `i` cobre `(referência + i meses, referência + (i+1) meses]`, então um
    vencimento a 12 meses do início entra no último mês do horizonte, não fora
    dele. Sem isso o caminho e `maturities_within` discordam por um mês.
    """
    limits = [add_months(reference, offset) for offset in range(months + 1)]
    buckets: dict[int, float] = {}
    for item in items:
        milestone = item["maturity"]
        if milestone is None or milestone <= reference:
            continue
        for offset in range(1, months + 1):
            if milestone <= limits[offset]:
                buckets[offset - 1] = buckets.get(offset - 1, 0.0) + item["value"]
                break
    return buckets


def simulate(
    values: dict[str, float],
    monthly_contribution: float,
    items: list[dict],
    reference: date,
    months: int,
    sale: float = 0.0,
    target: float | None = None,
) -> dict:
    """Caminho mensal do peso do caixa: aporte dilui, vencimento reduz sem vender."""
    # Vender renda fixa e comprar outro sleeve não muda o total: o dinheiro troca de sleeve.
    total = sum(as_number(value, key) for key, value in values.items())
    cash = as_number(values.get(CASH, 0.0), CASH) - as_number(sale, "sale")
    if cash < 0:
        raise ValueError(f"Venda de {brl(sale)} maior que o caixa disponível no sleeve.")
    buckets = month_buckets(items, reference, months)

    target = TARGETS[CASH] if target is None else target
    low, high = BANDS[CASH]
    path = []
    first_in_band = None
    first_at_target = None
    for index in range(months):
        cash -= buckets.get(index, 0.0)
        total += as_number(monthly_contribution, "monthly_contribution")
        weight = (cash / total * 100) if total else 0.0
        if first_in_band is None and low * 100 <= weight <= high * 100:
            first_in_band = index + 1
        if first_at_target is None and weight <= target * 100:
            first_at_target = index + 1
        path.append(
            {
                "month": index + 1,
                "period": add_months(reference, index + 1).strftime("%Y-%m"),
                "cash_value": cash,
                "total": total,
                "weight_pct": weight,
                "status": (
                    "abaixo da banda"
                    if weight < low * 100
                    else "acima da banda"
                    if weight > high * 100
                    else "na banda"
                ),
            }
        )
    return {
        "path": path,
        "first_in_band": first_in_band,
        "first_at_target": first_at_target,
        "target_pct": target * 100,
        "band_pct": (low * 100, high * 100),
    }


def sale_to_hit_target(
    values: dict[str, float],
    monthly_contribution: float,
    items: list[dict],
    reference: date,
    months: int,
    target: float = 0.20,
) -> dict:
    """Quanto vender hoje para o caixa aterrissar no alvo exatamente no horizonte."""
    total_horizon = sum(as_number(value, key) for key, value in values.items())
    total_horizon += as_number(monthly_contribution, "monthly_contribution") * months
    cash_horizon = as_number(values.get(CASH, 0.0), CASH) - maturities_within(items, reference, months)
    needed = cash_horizon - target * total_horizon
    return {
        "sale_brl": needed,
        "cash_at_horizon_without_sale": cash_horizon,
        "total_at_horizon": total_horizon,
        "target_value": target * total_horizon,
        "already_enough": needed <= 0,
    }


def net_carry(
    item: dict,
    cdi: float | None = None,
    selic: float | None = None,
    inflation: float | None = None,
    ir_pct: float = 15.0,
) -> tuple[float | None, str | None]:
    """Taxa líquida comparável. IPCA exige inflação assumida, sempre marcada."""
    indexer = item["indexer"]
    rate = item["rate_pct"]
    if indexer is None:
        return None, "indexador não informado"
    if rate is None:
        return None, "taxa não informada"
    if indexer == "CDI":
        if cdi is None:
            return None, "informe --cdi"
        gross = rate / 100 * cdi
    elif indexer == "SELIC":
        if selic is None:
            return None, "informe --selic"
        gross = rate / 100 * selic
    elif indexer == "PRE":
        gross = rate
    elif indexer == "IPCA":
        if inflation is None:
            return None, "informe --inflation para estimar"
        gross = ((1 + rate / 100) * (1 + inflation / 100) - 1) * 100
    else:
        return None, f"indexador {indexer} não suportado"
    net = gross if item["tax_exempt"] else gross * (1 - ir_pct / 100)
    return net, None


def format_ladder(ladder: dict) -> str:
    total = ladder["total"]
    lines = [
        f"Renda fixa na data de referência: R$ {brl(total)}",
        "",
        "| Ano | Vence (R$) | % da Renda Fixa | Acumulado |",
        "|---|---:|---:|---:|",
    ]
    for row in ladder["rows"]:
        lines.append(
            f"| {row['year']} | {brl(row['value'])} | "
            f"{pct(row['share_pct'])}% | {pct(row['cumulative_pct'])}% |"
        )
    if ladder["undated"]:
        lines.append(
            f"\nSem vencimento informado: **R$ {brl(ladder['undated'])}** "
            f"({pct(ladder['undated'] / total * 100 if total else 0.0)}% da Renda Fixa) — "
            "pedir a data ou marcar como liquidez diária."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Escada de vencimentos da renda fixa e caminho do peso do caixa."
    )
    parser.add_argument("portfolio", nargs="?", help="Caminho do JSON da carteira.")
    parser.add_argument("--example", action="store_true", help="Usa a carteira de exemplo.")
    parser.add_argument("--json", action="store_true", help="Saída em JSON.")
    parser.add_argument("--months", type=int, default=24, help="Horizonte em meses (padrão: 24).")
    parser.add_argument(
        "--amount", type=float, default=0.0, help="Aporte mensal recorrente considerado."
    )
    parser.add_argument("--sell", type=float, default=0.0, help="Venda de renda fixa no mês 1.")
    parser.add_argument("--cdi", type=float, help="CDI anual em %% (informe você: não inventamos taxa).")
    parser.add_argument("--selic", type=float, help="Selic anual em %%.")
    parser.add_argument("--inflation", type=float, help="Inflação anual assumida, para estimar IPCA+.")
    parser.add_argument("--ir", type=float, default=15.0, help="IR assumido para título tributado (padrão: 15).")
    args = parser.parse_args(argv)

    if args.example:
        path = Path(__file__).resolve().parent.parent / "assets" / "portfolio.example.json"
        data = json.loads(path.read_text(encoding="utf-8"))
    elif args.portfolio:
        path = Path(args.portfolio)
        if not path.exists():
            print(f"Arquivo não encontrado: {path}", file=sys.stderr)
            return 2
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"JSON inválido em {path}: {exc}", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 2

    try:
        targets = resolve_targets(data)
        values = load_sleeve_values(data)
        items = load_fixed_income(data)
        reference = parse_maturity(data.get("as_of")) if data.get("as_of") else date.today()
        ladder = build_ladder(items)
        if not items:
            print(
                "Nenhuma posição de renda fixa com metadados em 'positions'. "
                "A escada exige vencimento e indexador por título.",
                file=sys.stderr,
            )
            return 1
        simulation = simulate(
            values, args.amount, items, reference, args.months, sale=args.sell,
            target=targets.get(CASH),
        )
        sizing = sale_to_hit_target(
            values, args.amount, items, reference, args.months, targets.get(CASH, 0.20)
        )
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    carries = []
    for item in items:
        net, reason = net_carry(item, args.cdi, args.selic, args.inflation, args.ir)
        carries.append({"symbol": item["symbol"], "indexer": item["indexer"],
                        "rate_pct": item["rate_pct"], "tax_exempt": item["tax_exempt"],
                        "net_pct": net, "note": reason, "value": item["value"]})

    if args.json:
        print(json.dumps(
            {
                "as_of": reference.isoformat(),
                "ladder": ladder,
                "net_carry": carries,
                "simulation": simulation,
                "sale_sizing": sizing,
            },
            ensure_ascii=False, indent=2,
        ))
        return 0

    print(f"Data de referência: {reference.isoformat()}")
    print(format_ladder(ladder))
    print(f"\nVence em 12 meses: R$ {brl(maturities_within(items, reference, 12))}"
          f" | em 24 meses: R$ {brl(maturities_within(items, reference, 24))}")

    if any(row["net_pct"] is not None for row in carries):
        print("\n| Título | Indexador | Taxa | Líquido | Situação |")
        print("|---|---|---:|---:|---|")
        for row in carries:
            rate = "—" if row["rate_pct"] is None else pct(row["rate_pct"], 2)
            unit = UNIT_BY_INDEXER.get(row["indexer"] or "", "")
            net = "n/d" if row["net_pct"] is None else f"{pct(row['net_pct'], 2)}% a.a."
            note = row["note"] or ("isento" if row["tax_exempt"] else f"IR {pct(args.ir, 0)}%")
            if row["indexer"] == "IPCA" and row["net_pct"] is not None:
                note += f" · nominal com inflação {pct(args.inflation, 2)}%"
            print(f"| {row['symbol']} | {row['indexer'] or '—'} | {rate}{unit} | {net} | {note} |")
        print("\nLíquido é a taxa comparável: isento não desconta IR; tributado desconta.")
        if any(row["indexer"] == "IPCA" for row in carries):
            print("IPCA+ aparece em taxa real; a coluna líquida é uma **estimativa nominal** "
                  "com a inflação assumida, que é premissa sua — não projetamos inflação.")
    elif args.cdi or args.selic or args.inflation:
        print("\nCarry líquido não calculado: faltam taxa de referência ou dados por título.")

    print(f"\nCaminho do caixa (aporte R$ {brl(args.amount)}/mês"
          + (f", venda de R$ {brl(args.sell)}" if args.sell else "") + "):")
    print(f"| Mês | Período | Caixa (R$) | Total (R$) | Peso | Situação |")
    print("|---:|---|---:|---:|---:|---|")
    marks = {1, 3, 6, 9, 12, 15, 18, 21, 24, args.months}
    for row in simulation["path"]:
        if row["month"] in marks or row["month"] in {
            simulation["first_in_band"], simulation["first_at_target"]
        }:
            print(
                f"| {row['month']} | {row['period']} | {brl(row['cash_value'])} | "
                f"{brl(row['total'])} | {pct(row['weight_pct'])}% | {row['status']} |"
            )
    band_low, band_high = simulation["band_pct"]
    if simulation["first_in_band"]:
        print(f"\nEntra na banda ({pct(band_low, 0)}–{pct(band_high, 0)}%) no mês "
              f"{simulation['first_in_band']}.")
    else:
        print(f"\nNão entra na banda em {args.months} meses com esse fluxo. "
              "Reveja aporte, venda ou política.")
    if simulation["first_at_target"]:
        print(f"Atinge o alvo ({pct(simulation['target_pct'], 0)}%) no mês "
              f"{simulation['first_at_target']}.")

    print("\nVenda necessária para aterrissar no alvo no horizonte:")
    if sizing["already_enough"]:
        print(f"  Nenhuma. O fluxo e os vencimentos já levam o caixa a "
              f"R$ {brl(sizing['cash_at_horizon_without_sale'])}, abaixo do alvo de "
              f"R$ {brl(sizing['target_value'])}.")
    else:
        print(f"  R$ {brl(sizing['sale_brl'])} hoje. Sem venda, o caixa chega a "
              f"R$ {brl(sizing['cash_at_horizon_without_sale'])} contra alvo de "
              f"R$ {brl(sizing['target_value'])}.")
    print(
        "\nPremissas: preços constantes, sem marcação a mercado, aporte recorrente, "
        "nenhum reinvestimento em Renda Fixa enquanto o caixa estiver acima do alvo."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
