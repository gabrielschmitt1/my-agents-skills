#!/usr/bin/env python3
"""Grava a carteira extraída do extrato em state/portfolio.json.

Valida, reconcilia o total com o extrato, faz backup do estado anterior e
mostra o que mudou. É o único caminho para escrever o estado: o investidor
nunca edita o JSON à mão.

Uso:
    python scripts/save_portfolio.py --input /tmp/carteira.json --expected-total 134000.00
    python scripts/save_portfolio.py --input /tmp/carteira.json --dry-run
    cat /tmp/carteira.json | python scripts/save_portfolio.py --stdin --expected-total 134000.00
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from maturity_ladder import normalize_indexer, parse_bool, parse_maturity
from portfolio_allocation import (
    BANDS,
    TARGETS,
    as_number,
    brl,
    normalize_sleeve,
    resolve_targets,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE = SKILL_ROOT / "state" / "portfolio.json"
DEFAULT_HISTORY = SKILL_ROOT / "state" / "history"
TOLERANCE = 1.00
POLICY_KEYS = ("target_weights", "bands", "min_ticket_brl", "investor", "currency", "framework")
COVERAGE_VALUES = {"completa", "parcial"}


class IngestError(ValueError):
    """Erro de validação da carteira extraída."""


def _number(value: object, field: str) -> float:
    """Converte número validando; erros viram IngestError com mensagem útil."""
    try:
        return as_number(value, field)
    except ValueError as exc:
        raise IngestError(str(exc)) from exc


def _normalize_position(raw: dict, index: int) -> dict:
    if not isinstance(raw, dict):
        raise IngestError(f"Posição {index}: esperado objeto.")

    symbol = str(raw.get("symbol") or "").strip()
    if not symbol:
        raise IngestError(f"Posição {index}: 'symbol' é obrigatório.")

    sleeve_raw = raw.get("primary_sleeve") or raw.get("sleeve")
    if not sleeve_raw:
        raise IngestError(f"Posição {index} ({symbol}): informe 'primary_sleeve'.")
    try:
        sleeve = normalize_sleeve(str(sleeve_raw))
    except ValueError as exc:
        raise IngestError(f"Posição {index} ({symbol}): {exc}") from exc

    quantity = raw.get("quantity")
    price = raw.get("price_brl")
    value = raw.get("market_value_brl")

    market_value: float
    if value is not None:
        market_value = _number(value, f"positions[{index}].market_value_brl")
    elif quantity is not None and price is not None:
        market_value = _number(quantity, f"positions[{index}].quantity") * _number(
            price, f"positions[{index}].price_brl"
        )
    else:
        raise IngestError(
            f"Posição {index} ({symbol}): informe 'market_value_brl' ou 'quantity' + 'price_brl'."
        )

    return {
        "symbol": symbol.upper(),
        "name": str(raw.get("name") or symbol).strip(),
        "group": str(raw.get("group") or "").strip() or None,
        "primary_sleeve": sleeve,
        "quantity": _number(quantity, f"positions[{index}].quantity") if quantity is not None else None,
        "price_brl": _number(price, f"positions[{index}].price_brl") if price is not None else None,
        "market_value_brl": round(market_value, 2),
        "net_value_brl": (
            _number(raw["net_value_brl"], f"positions[{index}].net_value_brl")
            if raw.get("net_value_brl") is not None
            else None
        ),
        "cost_basis_brl": (
            _number(raw["cost_basis_brl"], f"positions[{index}].cost_basis_brl")
            if raw.get("cost_basis_brl") is not None
            else None
        ),
        "income_brl": (
            _number(raw["income_brl"], f"positions[{index}].income_brl")
            if raw.get("income_brl") is not None
            else 0.0
        ),
        "maturity": _optional_maturity(raw.get("maturity"), symbol),
        "indexer": _optional_indexer(raw.get("indexer"), symbol),
        "rate_pct": (
            _number(raw["rate_pct"], f"positions[{index}].rate_pct")
            if raw.get("rate_pct") is not None
            else None
        ),
        "tax_exempt": _optional_bool(raw.get("tax_exempt"), symbol),
        "liquid": bool(raw.get("liquid", True)),
        "notes": str(raw.get("notes") or "").strip(),
    }


def _optional_maturity(raw: object, symbol: str) -> str | None:
    """Vencimento em ISO (YYYY-MM-DD). Sem data, a posição fica fora da escada."""
    try:
        parsed = parse_maturity(raw)
    except ValueError as exc:
        raise IngestError(f"{symbol}: {exc}") from exc
    return parsed.isoformat() if parsed else None


def _optional_indexer(raw: object, symbol: str) -> str | None:
    """Indexador normalizado para CDI, SELIC, PRE ou IPCA."""
    try:
        return normalize_indexer(raw)
    except ValueError as exc:
        raise IngestError(f"{symbol}: {exc}") from exc


def _optional_bool(raw: object, symbol: str) -> bool:
    """Isenção tributária (LCA/LCI/CRI/CRA). Ausente = não isento."""
    try:
        return parse_bool(raw)
    except ValueError as exc:
        raise IngestError(f"{symbol}: {exc}") from exc


def normalize_positions(raw_positions: list) -> list[dict]:
    if not isinstance(raw_positions, list) or not raw_positions:
        raise IngestError("'positions' deve ser uma lista com pelo menos uma posição.")

    merged: dict[tuple[str, str], dict] = {}
    for index, raw in enumerate(raw_positions):
        position = _normalize_position(raw, index)
        # Mesmo ticker com vencimentos diferentes são títulos distintos: não somar.
        key = (position["symbol"], position["maturity"] or "")
        if key in merged:
            existing = merged[key]
            existing["market_value_brl"] = round(
                existing["market_value_brl"] + position["market_value_brl"], 2
            )
            if existing["quantity"] is not None and position["quantity"] is not None:
                existing["quantity"] += position["quantity"]
            if existing["net_value_brl"] is not None and position["net_value_brl"] is not None:
                existing["net_value_brl"] = round(
                    existing["net_value_brl"] + position["net_value_brl"], 2
                )
            else:
                existing["net_value_brl"] = None
            existing["notes"] = "; ".join(filter(None, [existing["notes"], position["notes"]]))
        else:
            merged[key] = position
    return list(merged.values())


def _validate_unmapped(raw_unmapped) -> list[dict]:
    if not raw_unmapped:
        return []
    if not isinstance(raw_unmapped, list):
        raise IngestError("'unmapped' deve ser uma lista.")
    result = []
    for index, item in enumerate(raw_unmapped):
        if not isinstance(item, dict):
            raise IngestError(f"unmapped[{index}]: esperado objeto.")
        result.append(
            {
                "item": str(item.get("item") or "não classificado"),
                "group": str(item.get("group") or "").strip() or None,
                "value_brl": _number(item.get("value_brl", 0), f"unmapped[{index}].value_brl"),
                "reason": str(item.get("reason") or ""),
            }
        )
    return result


def _validate_date(value: object) -> str:
    text = str(value or "").strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise IngestError(f"Data inválida: {value!r}. Use AAAA-MM-DD.") from exc
    return text


def _sleeve_totals(positions: list[dict]) -> dict[str, float]:
    totals = {sleeve: 0.0 for sleeve in TARGETS}
    for position in positions:
        totals[position["primary_sleeve"]] += position["market_value_brl"]
    return totals


def _state_sleeve_totals(state: dict) -> dict[str, float]:
    """Totais por sleeve de um estado antigo, tolerando formatos anteriores."""
    totals: dict[str, float] = {}
    for position in state.get("positions", []) or []:
        raw = position.get("primary_sleeve") or position.get("sleeve")
        try:
            sleeve = normalize_sleeve(str(raw))
        except (ValueError, TypeError):
            continue
        value = position.get("market_value_brl")
        if value is None and position.get("quantity") is not None and position.get("price_brl") is not None:
            value = float(position["quantity"]) * float(position["price_brl"])
        totals[sleeve] = totals.get(sleeve, 0.0) + float(value or 0)
    return totals


def _read_state(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IngestError(f"Estado existente inválido em {path}: {exc}") from exc


def _backup(path: Path, history: Path) -> Path:
    history.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = history / f"{stamp}.json"
    shutil.copy2(path, destination)
    return destination


def save_portfolio(
    data: dict,
    state_path: Path | str = DEFAULT_STATE,
    history_dir: Path | str = DEFAULT_HISTORY,
    expected_total: float | None = None,
    tolerance: float = TOLERANCE,
    dry_run: bool = False,
) -> dict:
    """Valida, reconcilia e grava a carteira. Retorna um resumo para impressão."""
    if not isinstance(data, dict):
        raise IngestError("O arquivo de entrada deve ser um objeto JSON.")

    as_of = _validate_date(data.get("as_of"))
    coverage = str(data.get("data_coverage") or "").lower()
    warnings: list[str] = []
    reference_date = datetime.strptime(as_of, "%Y-%m-%d").date()
    if reference_date > datetime.now().date():
        warnings.append(f"Data de referência no futuro: {as_of}. Conferir.")
    elif (datetime.now().date() - reference_date).days > 45:
        warnings.append(f"Estado defasado: {as_of} tem mais de 45 dias. Atualizar antes de decidir.")
    if coverage not in COVERAGE_VALUES:
        coverage = "parcial"
        warnings.append("Cobertura não declarada: assumindo 'parcial'. Declare 'data_coverage'.")

    positions = normalize_positions(data.get("positions"))
    unmapped = _validate_unmapped(data.get("unmapped"))
    sleeves_total = sum(position["market_value_brl"] for position in positions)
    net_total = sum(
        position["net_value_brl"] for position in positions if position["net_value_brl"] is not None
    )
    has_net = any(position["net_value_brl"] is not None for position in positions)
    unmapped_total = sum(item["value_brl"] for item in unmapped)
    extracted_total = sleeves_total + unmapped_total

    reconciliation = data.get("reconciliation") or []
    if reconciliation:
        if not isinstance(reconciliation, list):
            raise IngestError("'reconciliation' deve ser uma lista de grupos.")
        group_totals: dict[str, float] = {}
        for position in positions:
            if position["group"]:
                group_totals[position["group"]] = (
                    group_totals.get(position["group"], 0.0) + position["market_value_brl"]
                )
        for item in unmapped:
            if item["group"]:
                group_totals[item["group"]] = group_totals.get(item["group"], 0.0) + item["value_brl"]
        group_errors: list[str] = []
        declared_groups: set[str] = set()
        for index, group in enumerate(reconciliation):
            if not isinstance(group, dict):
                raise IngestError(f"reconciliation[{index}]: esperado objeto.")
            name = str(group.get("group") or "").strip()
            if not name:
                raise IngestError(f"reconciliation[{index}]: informe 'group'.")
            declared_groups.add(name)
            expected_group = _number(group.get("expected_brl"), f"reconciliation[{index}].expected_brl")
            actual_group = group_totals.get(name, 0.0)
            if abs(actual_group - expected_group) > tolerance:
                group_errors.append(
                    f"  {name}: extraído R$ {brl(actual_group)} | extrato R$ {brl(expected_group)} "
                    f"| diferença R$ {brl(actual_group - expected_group)}"
                )
        undeclared = sorted(set(group_totals) - declared_groups)
        if undeclared:
            warnings.append(
                "Grupos sem subtotal declarado em 'reconciliation': " + ", ".join(undeclared) + "."
            )
        if group_errors:
            raise IngestError(
                "Subtotal de grupo não reconcilia com o extrato.\n"
                + "\n".join(group_errors)
                + "\n  Não gravar: revise as linhas do grupo antes de continuar."
            )
    if expected_total is not None:
        expected = _number(expected_total, "expected_total")
        difference = extracted_total - expected
        if abs(difference) > tolerance:
            detail = "\n".join(
                f"  {item['item']}: R$ {brl(item['value_brl'])} ({item['reason']})"
                for item in unmapped
            )
            raise IngestError(
                "Total não reconcilia com o extrato.\n"
                f"  Extraído (posições): R$ {brl(sleeves_total)}\n"
                f"  Extraído (fora dos sleeves): R$ {brl(unmapped_total)}\n"
                f"  Extraído (total): R$ {brl(extracted_total)}\n"
                f"  Extrato: R$ {brl(expected)}\n"
                f"  Diferença (extraído − extrato): R$ {brl(difference)}\n"
                f"  → {'Faltam' if difference < 0 else 'Sobram'} R$ {brl(abs(difference))} no que foi extraído.\n"
                + (f"  Fora dos sleeves:\n{detail}\n" if detail else "")
                + "  Não gravar: localize a linha faltante ou o valor divergente."
            )
    else:
        warnings.append("Sem --expected-total: o total do extrato não foi conferido.")

    for position in positions:
        if position["quantity"] and position["price_brl"]:
            calculated = position["quantity"] * position["price_brl"]
            if abs(calculated - position["market_value_brl"]) > max(1.0, calculated * 0.005):
                warnings.append(
                    f"{position['symbol']}: saldo informado R$ {brl(position['market_value_brl'])} "
                    f"difere de quantidade × preço (R$ {brl(calculated)})."
                )
        if position["primary_sleeve"] == "cash_fixed_income" and position["maturity"] is None:
            warnings.append(
                f"{position['symbol']}: renda fixa sem 'maturity'. O título fica fora da escada "
                "de vencimentos, que é o principal mecanismo de rebalanceamento do caixa."
            )
        if position["market_value_brl"] < 1.0:
            warnings.append(f"{position['symbol']}: posição residual (< R$ 1,00).")
        if (
            position["net_value_brl"] is not None
            and position["net_value_brl"] > position["market_value_brl"] + 1.0
        ):
            warnings.append(
                f"{position['symbol']}: saldo líquido R$ {brl(position['net_value_brl'])} "
                f"maior que o bruto R$ {brl(position['market_value_brl'])}. Conferir."
            )

    state_path = Path(state_path)
    history_dir = Path(history_dir)
    previous = _read_state(state_path)

    state = {
        "schema_version": "4.0",
        "as_of": as_of,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "source": str(data.get("source") or "não informado"),
        "data_coverage": coverage,
        "currency": "BRL",
        "framework": "KRAKED",
        "contribution_month_brl": _number(
            data.get("contribution_month_brl") or 0, "contribution_month_brl"
        ),
        "positions": positions,
        "unmapped": unmapped,
    }

    # A entrada pode trazer uma política nova; o que não vier, herda do estado anterior.
    for key in POLICY_KEYS:
        if key in data and data[key] is not None:
            state[key] = data[key]
    if previous:
        for key in POLICY_KEYS:
            if key in previous and (state.get(key) is None):
                state[key] = previous[key]
    if "target_weights" not in state:
        state["target_weights"] = dict(TARGETS)
    if "bands" not in state:
        state["bands"] = {sleeve: list(BANDS[sleeve]) for sleeve in TARGETS}
    if "min_ticket_brl" not in state:
        state["min_ticket_brl"] = {sleeve: 0 for sleeve in TARGETS}
    if "investor" not in state:
        state["investor"] = {}

    try:
        effective_targets = resolve_targets(state)
    except ValueError as exc:
        raise IngestError(str(exc)) from exc
    state["effective_targets"] = effective_targets

    backup_path = None
    if not dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        if state_path.exists():
            backup_path = _backup(state_path, history_dir)
        tmp_path = state_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp_path, state_path)

    before_total = None
    before_totals = None
    if previous:
        before_totals = _state_sleeve_totals(previous)
        before_total = sum(before_totals.values())

    after_totals = _sleeve_totals(positions)
    added = sorted(
        set(p["symbol"] for p in positions)
        - set(p.get("symbol", "") for p in (previous or {}).get("positions", []))
    )
    removed = sorted(
        set(p.get("symbol", "") for p in (previous or {}).get("positions", []))
        - set(p["symbol"] for p in positions)
    )

    return {
        "state_path": str(state_path),
        "backup_path": str(backup_path) if backup_path else None,
        "dry_run": dry_run,
        "as_of": as_of,
        "coverage": coverage,
        "sleeves_total": sleeves_total,
        "net_total": net_total if has_net else None,
        "unmapped_total": unmapped_total,
        "extracted_total": extracted_total,
        "expected_total": expected_total,
        "warnings": warnings,
        "before_total": before_total,
        "before_totals": before_totals,
        "after_totals": after_totals,
        "added": added,
        "removed": removed,
        "position_count": len(positions),
        "effective_targets": effective_targets,
    }


def format_summary(result: dict) -> str:
    lines = []
    if result["dry_run"]:
        lines.append("DRY-RUN: nada foi gravado.")
    lines.append(f"Data de referência: {result['as_of']} | Cobertura: {result['coverage']}")
    lines.append(
        f"Posições: {result['position_count']} | Total em sleeves: R$ {brl(result['sleeves_total'])}"
    )
    if result["unmapped_total"]:
        lines.append(f"Fora dos sleeves: R$ {brl(result['unmapped_total'])}")
    lines.append(f"Total extraído: R$ {brl(result['extracted_total'])}")
    if result.get("net_total") is not None:
        lines.append(
            f"Valor líquido estimado (só posições que informam): R$ {brl(result['net_total'])}"
        )
    if result["expected_total"] is not None:
        lines.append(f"Total do extrato: R$ {brl(result['expected_total'])} (reconciliado)")

    lines.append("")
    lines.append("| Classe | Antes (R$) | Depois (R$) | Δ (R$) |")
    lines.append("|---|---:|---:|---:|")
    before = result["before_totals"] or {}
    for sleeve, label in (
        ("cash_fixed_income", "Renda Fixa e Caixa (K1)"),
        ("real_estate_fiis", "Fundos Imobiliários (R)"),
        ("brazilian_equities", "Ações Brasil (A)"),
        ("cryptoassets", "Criptoativos (K2)"),
        ("international_assets", "Exterior (E)"),
        ("diversos", "Diversos (D)"),
    ):
        old = before.get(sleeve)
        new = result["after_totals"].get(sleeve, 0.0)
        delta = "" if old is None else f"{new - old:+,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        lines.append(
            f"| {label} | {'—' if old is None else brl(old)} | {brl(new)} | {delta} |"
        )
    if result["before_total"] is not None:
        lines.append(
            f"\nTotal antes: R$ {brl(result['before_total'])} → depois: R$ {brl(result['sleeves_total'])}"
        )
    if result["added"]:
        lines.append(f"Adicionadas: {', '.join(result['added'])}")
    if result["removed"]:
        lines.append(f"Removidas: {', '.join(result['removed'])}")
    for warning in result["warnings"]:
        lines.append(f"AVISO: {warning}")
    if result["backup_path"]:
        lines.append(f"Backup do estado anterior: {result['backup_path']}")
    if not result["dry_run"]:
        lines.append(f"Gravado em: {result['state_path']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida e grava a carteira em state/portfolio.json.")
    parser.add_argument("--input", help="JSON normalizado da carteira.")
    parser.add_argument("--stdin", action="store_true", help="Lê o JSON da entrada padrão.")
    parser.add_argument("--expected-total", type=float, help="Total informado pelo extrato.")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE, help="Tolerância da reconciliação.")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="Caminho do estado.")
    parser.add_argument("--history", default=str(DEFAULT_HISTORY), help="Diretório de backups.")
    parser.add_argument("--dry-run", action="store_true", help="Valida e mostra o diff sem gravar.")
    args = parser.parse_args(argv)

    try:
        if args.stdin:
            data = json.loads(sys.stdin.read())
        elif args.input:
            path = Path(args.input)
            if not path.exists():
                print(f"Arquivo não encontrado: {path}", file=sys.stderr)
                return 2
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            parser.print_help()
            return 2
    except json.JSONDecodeError as exc:
        print(f"JSON inválido: {exc}", file=sys.stderr)
        return 2

    try:
        result = save_portfolio(
            data,
            state_path=args.state,
            history_dir=args.history,
            expected_total=args.expected_total,
            tolerance=args.tolerance,
            dry_run=args.dry_run,
        )
    except IngestError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(format_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
