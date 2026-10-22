#!/usr/bin/env python3
"""Calcula o peso de cada sleeve da carteira contra o baseline KRAKED.

Uso:
    python scripts/portfolio_allocation.py state/portfolio.json
    python scripts/portfolio_allocation.py state/portfolio.json --json
    python scripts/portfolio_allocation.py --example

Entrada aceita dois formatos (ver assets/portfolio-schema.json):
  1. {"as_of": "...", "sleeves": {"cash_fixed_income": 40000, ...}}
  2. {"as_of": "...", "positions": [{"primary_sleeve": "...", "market_value_brl": ...}, ...]}

Aceita também nomes de sleeve em português (caixa, fiis, acoes, cripto,
exterior, diversos). Saída em português; valores em BRL.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

TARGETS: dict[str, float] = {
    "cash_fixed_income": 0.20,
    "real_estate_fiis": 0.20,
    "brazilian_equities": 0.25,
    "cryptoassets": 0.05,
    "international_assets": 0.25,
    "diversos": 0.05,
}

LABELS: dict[str, str] = {
    "cash_fixed_income": "Caixa / Renda fixa (K1)",
    "real_estate_fiis": "FIIs / Imóveis (R)",
    "brazilian_equities": "Ações Brasil (A)",
    "cryptoassets": "Criptoativos (K2)",
    "international_assets": "Exterior (E)",
    "diversos": "Diversos (D)",
}

# Bandas de revisão: (mínimo, máximo). Disparo de análise, não ordem de trade.
BANDS: dict[str, tuple[float, float]] = {
    "cash_fixed_income": (0.15, 0.25),
    "real_estate_fiis": (0.15, 0.25),
    "brazilian_equities": (0.20, 0.30),
    "cryptoassets": (0.00, 0.07),
    "international_assets": (0.20, 0.30),
    "diversos": (0.02, 0.08),
}

ALIASES: dict[str, str] = {
    # caixa
    "caixa": "cash_fixed_income",
    "renda_fixa": "cash_fixed_income",
    "rf": "cash_fixed_income",
    "cash": "cash_fixed_income",
    "k1": "cash_fixed_income",
    # fiis
    "fiis": "real_estate_fiis",
    "fii": "real_estate_fiis",
    "imoveis": "real_estate_fiis",
    "reits": "real_estate_fiis",
    "r": "real_estate_fiis",
    # acoes br
    "acoes": "brazilian_equities",
    "acoes_br": "brazilian_equities",
    "acoes_brasil": "brazilian_equities",
    "brazil": "brazilian_equities",
    "a": "brazilian_equities",
    # cripto
    "cripto": "cryptoassets",
    "criptoativos": "cryptoassets",
    "crypto": "cryptoassets",
    "k2": "cryptoassets",
    # exterior
    "exterior": "international_assets",
    "internacional": "international_assets",
    "international": "international_assets",
    "e": "international_assets",
    # diversos (inclui o antigo N de negócios)
    "diversos": "diversos",
    "d": "diversos",
    "outros": "diversos",
    "alternativos": "diversos",
    "commodities": "diversos",
    "negocios": "diversos",
    "oportunidades": "diversos",
    "business": "diversos",
    "n": "diversos",
}


def normalize_sleeve(key: str) -> str:
    """Converte nome de sleeve (EN ou PT) para a chave canônica."""
    raw = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    if raw in TARGETS:
        return raw
    if raw in ALIASES:
        return ALIASES[raw]
    valid = ", ".join(TARGETS)
    raise ValueError(f"Sleeve desconhecido: {key!r}. Use um de: {valid} (ou os apelidos em português).")


def as_number(value: object, field: str) -> float:
    """Valida e converte um valor numérico não negativo e finito."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Valor inválido em {field!r}: {value!r} (esperado número).")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Valor inválido em {field!r}: {value!r} (esperado número finito).")
    if number < 0:
        raise ValueError(f"Valor negativo em {field!r}: {number}.")
    return number


def resolve_targets(data: dict | None = None) -> dict[str, float]:
    """Alvos efetivos da política KRAKED.

    Os seis sleeves são sempre parte da política; D (Diversos) não é "não
    aplicável" e não há renormalização. O relatório usa exatamente os alvos
    declarados, que precisam somar 100%.
    """
    data = data or {}
    raw = data.get("target_weights") or TARGETS
    if not isinstance(raw, dict):
        raise ValueError("'target_weights' deve ser um objeto sleeve -> peso.")
    targets = {
        normalize_sleeve(key): as_number(value, f"target_weights.{key}")
        for key, value in raw.items()
    }
    missing = set(TARGETS) - set(targets)
    if missing:
        raise ValueError(f"Faltam alvos para: {', '.join(sorted(missing))}")
    total = sum(targets.values())
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ValueError(f"Os alvos devem somar 1.0 (100%); somam {total:.4f}.")
    return targets


def load_sleeve_values(data: dict) -> dict[str, float]:
    """Extrai valores por sleeve de um dicionário de carteira."""
    if not isinstance(data, dict):
        raise ValueError("A carteira deve ser um objeto JSON.")

    values: dict[str, float] = {}

    if "sleeves" in data:
        if not isinstance(data["sleeves"], dict):
            raise ValueError("O campo 'sleeves' deve ser um objeto.")
        for key, value in data["sleeves"].items():
            canonical = normalize_sleeve(key)
            values[canonical] = values.get(canonical, 0.0) + as_number(value, key)
        return values

    if "positions" in data:
        positions = data["positions"]
        if not isinstance(positions, list):
            raise ValueError("O campo 'positions' deve ser uma lista.")
        for index, position in enumerate(positions):
            if not isinstance(position, dict):
                raise ValueError(f"Posição {index} inválida: esperado objeto.")
            if "primary_sleeve" not in position:
                raise ValueError(f"Posição {index} sem 'primary_sleeve'.")
            canonical = normalize_sleeve(position["primary_sleeve"])
            if "market_value_brl" in position:
                value = as_number(position["market_value_brl"], f"positions[{index}].market_value_brl")
            elif "quantity" in position and "price_brl" in position:
                quantity = as_number(position["quantity"], f"positions[{index}].quantity")
                price = as_number(position["price_brl"], f"positions[{index}].price_brl")
                value = quantity * price
            else:
                raise ValueError(
                    f"Posição {index} precisa de 'market_value_brl' ou de 'quantity' + 'price_brl'."
                )
            values[canonical] = values.get(canonical, 0.0) + value
        return values

    raise ValueError("A carteira precisa ter 'sleeves' ou 'positions'.")


def add_contribution_to_cash(values: dict[str, float], contribution: float) -> dict[str, float]:
    """Visão pós-aporte: o aporte ainda não investido entra no caixa."""
    contribution = as_number(contribution, "contribution")
    result: dict[str, float] = {}
    for key, value in values.items():
        canonical = normalize_sleeve(key)
        result[canonical] = result.get(canonical, 0.0) + as_number(value, key)
    if contribution:
        result["cash_fixed_income"] = result.get("cash_fixed_income", 0.0) + contribution
    return result


def analyze(values: dict[str, float], targets: dict[str, float] | None = None) -> list[dict[str, float | str]]:
    """Compara a carteira com os alvos. Retorna uma linha por sleeve ativo."""
    targets = targets or TARGETS
    normalized: dict[str, float] = {}
    for key, value in values.items():
        canonical = normalize_sleeve(key)
        amount = as_number(value, key)
        if canonical not in targets:
            if amount == 0:
                continue
            raise ValueError(
                f"Há posição no sleeve {canonical!r}, que não está ativo na política. "
                "Reclassifique a posição ou revise 'target_weights'."
            )
        normalized[canonical] = normalized.get(canonical, 0.0) + amount

    total = sum(normalized.values())
    if total <= 0:
        raise ValueError("O valor total da carteira precisa ser positivo.")

    rows: list[dict[str, float | str]] = []
    for name, target in targets.items():
        value = normalized.get(name, 0.0)
        current = value / total
        target_value = total * target
        low, high = BANDS[name]
        if current < low:
            status = "abaixo da banda"
        elif current > high:
            status = "acima da banda"
        else:
            status = "na banda"
        rows.append(
            {
                "sleeve": name,
                "label": LABELS[name],
                "value": value,
                "current_pct": current * 100,
                "target_pct": target * 100,
                "band_low_pct": low * 100,
                "band_high_pct": high * 100,
                "deviation_pp": (current - target) * 100,
                "target_value": target_value,
                "gap_to_target": target_value - value,
                "total": total,
                "status": status,
            }
        )
    return rows


def brl(value: float, decimals: int = 2) -> str:
    """Formata número no padrão brasileiro: 1.234,56."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float, decimals: int = 1) -> str:
    """Formata percentual com vírgula decimal."""
    return f"{value:.{decimals}f}".replace(".", ",")


def format_table(rows: list[dict[str, float | str]]) -> str:
    """Tabela markdown em pt-BR."""
    total = float(rows[0]["total"]) if rows else 0.0
    lines = [
        f"Total investido: R$ {brl(total)}",
        "",
        "| Classe | Valor (R$) | Atual | Alvo | Desvio | Gap (R$) | Banda | Situação |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {label} | {value} | {current}% | {target}% | {dev} p.p. | {gap} | {low}–{high}% | {status} |".format(
                label=row["label"],
                value=brl(float(row["value"])),
                current=pct(float(row["current_pct"])),
                target=pct(float(row["target_pct"])),
                dev=("0,0" if abs(float(row["deviation_pp"])) < 0.05 else f"{float(row['deviation_pp']):+.1f}".replace(".", ",")),
                gap=f"{float(row['gap_to_target']):+,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                low=pct(float(row["band_low_pct"]), 0),
                high=pct(float(row["band_high_pct"]), 0),
                status=row["status"],
            )
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pesos da carteira contra o baseline KRAKED.")
    parser.add_argument("portfolio", nargs="?", help="Caminho do JSON da carteira.")
    parser.add_argument("--example", action="store_true", help="Usa uma carteira de exemplo.")
    parser.add_argument("--json", action="store_true", help="Saída em JSON.")
    parser.add_argument(
        "--contribution",
        type=float,
        help="Aporte do mês ainda não investido (padrão: contribution_month_brl do JSON).",
    )
    parser.add_argument(
        "--no-contribution",
        action="store_true",
        help="Ignora o aporte do mês e calcula pesos pré-aporte.",
    )
    args = parser.parse_args(argv)

    as_of = None
    if args.example:
        path = Path(__file__).resolve().parent.parent / "assets" / "portfolio.example.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        as_of = data.get("as_of")
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
        as_of = data.get("as_of")
    else:
        parser.print_help()
        return 2

    try:
        targets = resolve_targets(data)
        contribution = 0.0 if args.no_contribution else (
            args.contribution if args.contribution is not None
            else as_number(data.get("contribution_month_brl", 0) or 0, "contribution_month_brl")
        )
        values = add_contribution_to_cash(load_sleeve_values(data), contribution)
        rows = analyze(values, targets)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"as_of": as_of, "rows": rows}, ensure_ascii=False, indent=2))
        return 0

    if as_of:
        print(f"Data de referência: {as_of}")
    if contribution:
        print(f"Denominador pós-aporte: inclui R$ {brl(contribution)} ainda não investido (no caixa).")
    else:
        print("Denominador: pré-aporte (nenhum aporte pendente).")
    print(format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
