#!/usr/bin/env python3
"""Distribui um aporte entre os sleeves abaixo do alvo, sem julgamento de valuation.

Uso:
    python scripts/rebalance_contribution.py state/portfolio.json --amount 5000
    python scripts/rebalance_contribution.py state/portfolio.json --amount 5000 --min-ticket 100
    python scripts/rebalance_contribution.py --example

Regra: alocação proporcional ao déficit de cada sleeve no total PÓS-aporte,
respeitando ticket mínimo por sleeve. O que sobra volta como resíduo
(manter em liquidez), nunca é empurrado para um sleeve já sobrepeso.

Planejamento, não sinal automático de compra: antes de executar, revise
adequação, valuation, risco, liquidez, custos e impostos.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from portfolio_allocation import (
    BANDS,
    LABELS,
    TARGETS,
    as_number,
    brl,
    load_sleeve_values,
    normalize_sleeve,
    pct,
    resolve_targets,
)


@dataclass
class ContributionPlan:
    allocations: dict[str, float]
    residual: float
    post_weights: dict[str, float]
    post_total: float
    notes: list[str] = field(default_factory=list)


def _min_tickets(raw: dict | None, default: float = 0.0) -> dict[str, float]:
    tickets = {sleeve: default for sleeve in TARGETS}  # todos os sleeves possíveis
    if not raw:
        return tickets
    if not isinstance(raw, dict):
        raise ValueError("'min_ticket_brl' deve ser um objeto sleeve -> valor.")
    for key, value in raw.items():
        tickets[normalize_sleeve(key)] = as_number(value, f"min_ticket_brl.{key}")
    return tickets


def build_contribution_plan(
    values: dict[str, float],
    contribution: float,
    min_ticket_brl: dict | None = None,
    default_min_ticket: float = 0.0,
    targets: dict[str, float] | None = None,
    exclude: set[str] | None = None,
) -> ContributionPlan:
    """Calcula o plano de aporte com déficit pós-aporte e ticket mínimo."""
    targets = targets or TARGETS
    exclude = exclude or set()
    contribution = as_number(contribution, "contribution")
    normalized: dict[str, float] = {}
    for key, value in values.items():
        canonical = normalize_sleeve(key)
        amount = as_number(value, key)
        if canonical not in targets:
            if amount == 0:
                continue
            raise ValueError(f"Posição no sleeve {canonical!r}, que não está ativo na política.")
        normalized[canonical] = normalized.get(canonical, 0.0) + amount

    total = sum(normalized.values())
    post_total = total + contribution
    tickets = _min_tickets(min_ticket_brl, default_min_ticket)

    if post_total <= 0:
        raise ValueError("A carteira somada ao aporte precisa ser positiva.")

    deficits = {
        sleeve: max(0.0, post_total * target - normalized.get(sleeve, 0.0))
        for sleeve, target in targets.items()
    }
    total_deficit = sum(deficits.values())

    allocations = {sleeve: 0.0 for sleeve in targets}
    notes: list[str] = []
    if contribution > 0 and total_deficit > 0:
        for sleeve, target in targets.items():
            allocations[sleeve] = contribution * deficits[sleeve] / total_deficit

    if contribution > 0 and total_deficit <= 0:
        notes.append("Carteira já está no alvo ou acima em todos os sleeves: nada a alocar.")

    # Sleeves excluídos explicitamente da alocação: valor vai para o pool.
    pool = 0.0
    for sleeve in sorted(exclude):
        if sleeve in allocations and allocations[sleeve] > 0:
            notes.append(
                f"{LABELS.get(sleeve, sleeve)}: R$ {brl(allocations[sleeve])} não alocado "
                "(sleeve sem definição ou fora da política)."
            )
            pool += allocations[sleeve]
            allocations[sleeve] = 0.0

    # Ticket mínimo: zera alocações pequenas e redistribui o pool.
    for sleeve in targets:
        minimum = tickets.get(sleeve, 0.0)
        if 0 < allocations[sleeve] < minimum:
            notes.append(
                f"{LABELS[sleeve]}: R$ {brl(allocations[sleeve])} ficou abaixo do ticket mínimo "
                f"de R$ {brl(minimum)}; valor realocado."
            )
            pool += allocations[sleeve]
            allocations[sleeve] = 0.0

    if pool > 0:
        order = sorted(
            (s for s in targets if s not in exclude),
            key=lambda s: deficits[s] - allocations[s],
            reverse=True,
        )
        for sleeve in order:
            if pool <= 0:
                break
            room = deficits[sleeve] - allocations[sleeve]
            if room <= 0:
                continue
            give = min(room, pool)
            if allocations[sleeve] == 0 and give < tickets.get(sleeve, 0.0):
                continue
            allocations[sleeve] += give
            pool -= give

    residual = pool
    if residual > 0:
        notes.append(
            f"Sobra de R$ {brl(residual)} sem destino que respeite o ticket mínimo. "
            "Manter em liquidez e acumular para o próximo aporte."
        )

    if post_total > 0:
        post_weights = {
            sleeve: (normalized.get(sleeve, 0.0) + allocations[sleeve]) / post_total
            for sleeve in targets
        }
    else:
        post_weights = {sleeve: 0.0 for sleeve in targets}

    return ContributionPlan(
        allocations=allocations,
        residual=residual,
        post_weights=post_weights,
        post_total=post_total,
        notes=notes,
    )


def allocate_contribution(
    values: dict[str, float], contribution: float, min_ticket_brl: dict | None = None
) -> dict[str, float]:
    """Compatibilidade: retorna apenas o dicionário sleeve -> valor do aporte."""
    return build_contribution_plan(values, contribution, min_ticket_brl).allocations


def format_plan(plan: ContributionPlan) -> str:
    lines = ["| Destino | Aporte (R$) | Peso pós-aporte | Banda | Situação |", "|---|---:|---:|---|---|"]
    for sleeve in plan.allocations:
        low, high = BANDS[sleeve]
        weight = plan.post_weights[sleeve]
        if weight < low:
            status = "abaixo da banda"
        elif weight > high:
            status = "acima da banda"
        else:
            status = "na banda"
        lines.append(
            "| {label} | {amount} | {weight}% | {low}–{high}% | {status} |".format(
                label=LABELS[sleeve],
                amount=brl(plan.allocations[sleeve]),
                weight=pct(weight * 100),
                low=pct(low * 100, 0),
                high=pct(high * 100, 0),
                status=status,
            )
        )
    lines.append(f"\nTotal pós-aporte: R$ {brl(plan.post_total)}")
    if plan.residual > 0:
        lines.append(f"Resíduo em liquidez: R$ {brl(plan.residual)}")
    for note in plan.notes:
        lines.append(f"- {note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plano de aporte por sleeve (KRAKED).")
    parser.add_argument("portfolio", nargs="?", help="Caminho do JSON da carteira.")
    parser.add_argument("--amount", type=float, help="Valor do aporte em BRL.")
    parser.add_argument("--min-ticket", type=float, default=0.0, help="Ticket mínimo padrão por sleeve.")
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
            print("Informe o aporte: --amount ou 'contribution_month_brl' no JSON.", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 2

    try:
        targets = resolve_targets(data)
        plan = build_contribution_plan(
            load_sleeve_values(data),
            amount,
            data.get("min_ticket_brl"),
            args.min_ticket,
            targets,
        )
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "allocations": plan.allocations,
                    "residual": plan.residual,
                    "post_total": plan.post_total,
                    "post_weights": plan.post_weights,
                    "notes": plan.notes,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(format_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
