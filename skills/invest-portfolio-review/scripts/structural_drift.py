#!/usr/bin/env python3
"""Teste de desvio estrutural: o fluxo de aporte corrige a carteira? Em quanto tempo?

Para sleeves ACIMA da banda, o peso cai por diluição conforme o patrimônio cresce
(sem vender). O total necessário é `valor_do_sleeve / limite_superior_da_banda`.
Para sleeves ABAIXO da banda, o tempo é o gap dividido pelo aporte mensal,
assumindo que 100% do aporte vá para aquele sleeve.

Premissas explícitas: preços constantes, aporte só nos sleeves abaixo do alvo,
sem venda. Serve para decidir entre "aceitar o desvio" e "vender".

Uso:
    python scripts/structural_drift.py state/portfolio.json --amount 5000
    python scripts/structural_drift.py --example
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from portfolio_allocation import (
    BANDS,
    LABELS,
    add_contribution_to_cash,
    analyze,
    brl,
    load_sleeve_values,
    pct,
    resolve_targets,
)


def drift_report(
    values: dict[str, float],
    monthly_contribution: float,
    targets: dict[str, float] | None = None,
    pending_contribution: float = 0.0,
) -> dict:
    rows = analyze(add_contribution_to_cash(values, pending_contribution), targets)
    total = float(rows[0]["total"])
    results = []
    for row in rows:
        sleeve = str(row["sleeve"])
        value = float(row["value"])
        low, high = BANDS[sleeve]
        current = float(row["current_pct"]) / 100
        item = {
            "sleeve": sleeve,
            "label": LABELS[sleeve],
            "current_pct": current * 100,
            "band": f"{pct(low * 100, 0)}–{pct(high * 100, 0)}%",
            "status": row["status"],
            "months": None,
            "required_total": None,
            "gap": None,
        }
        if current > high:
            required_total = value / high
            gap = max(0.0, required_total - total)
            item["required_total"] = required_total
            item["gap"] = gap
            item["months"] = gap / monthly_contribution if monthly_contribution > 0 else None
        elif current < low:
            gap = max(0.0, low * total - value)
            item["gap"] = gap
            item["months"] = gap / monthly_contribution if monthly_contribution > 0 else None
        results.append(item)
    return {
        "total": total,
        "monthly_contribution": monthly_contribution,
        "rows": results,
    }


def format_report(report: dict) -> str:
    monthly = report["monthly_contribution"]
    lines = [
        f"Total atual: R$ {brl(report['total'])} | Aporte mensal considerado: R$ {brl(monthly)}",
        "",
        "| Classe | Peso | Banda | Situação | Gap (R$) | Meses | Leitura |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for row in report["rows"]:
        months = row["months"]
        if months is None:
            months_text = "—"
            reading = "sem aporte mensal informado" if monthly <= 0 else "no alvo"
        else:
            months_text = pct(months, 0)
            if months > 36:
                reading = "estrutural — fluxo não resolve"
            elif months > 12:
                reading = "lento"
            else:
                reading = "viável no fluxo"
        lines.append(
            f"| {row['label']} | {pct(row['current_pct'])}% | {row['band']} | {row['status']} | "
            f"{brl(row['gap']) if row['gap'] is not None else '—'} | {months_text} | {reading} |"
        )
    over = [
        r
        for r in report["rows"]
        if r["months"] is not None and r["months"] > 36
    ]
    if over:
        lines.append(
            "\nClasses que não fecham a banda em 3 anos nem com 100% do aporte: "
            + ", ".join(r["label"] for r in over)
            + ". O fluxo não resolve sozinho: decidir entre aceitar o desvio ou rever a política."
        )
    lines.append(
        "\nGap em R$: se acima da banda, é quanto o patrimônio precisa crescer (o sleeve fica parado); "
        "se abaixo, é quanto falta no sleeve. Premissas: preços constantes, aporte só em sleeves abaixo "
        "do alvo, sem venda."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Teste de desvio estrutural (KRAKED).")
    parser.add_argument("portfolio", nargs="?", help="Caminho do JSON da carteira.")
    parser.add_argument("--amount", type=float, help="Aporte mensal em BRL.")
    parser.add_argument("--example", action="store_true", help="Usa uma carteira de exemplo.")
    parser.add_argument("--json", action="store_true", help="Saída em JSON.")
    args = parser.parse_args(argv)

    if args.example:
        path = Path(__file__).resolve().parent.parent / "assets" / "portfolio.example.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        amount = args.amount if args.amount is not None else data.get("contribution_month_brl", 5000.0)
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
        amount = args.amount if args.amount is not None else data.get("contribution_month_brl")
        if amount is None:
            print("Informe o aporte mensal: --amount ou 'contribution_month_brl'.", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 2

    try:
        pending = data.get("contribution_month_brl", 0) or 0
        report = drift_report(
            load_sleeve_values(data), amount, resolve_targets(data), pending
        )
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
