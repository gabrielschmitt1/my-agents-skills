#!/usr/bin/env python3
"""Testes dos cálculos da skill. Rode: python -m unittest discover -s tests -v"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from portfolio_allocation import (  # noqa: E402
    TARGETS,
    add_contribution_to_cash,
    analyze,
    load_sleeve_values,
    resolve_targets,
)
from rebalance_contribution import build_contribution_plan  # noqa: E402
from structural_drift import drift_report  # noqa: E402
from maturity_ladder import (  # noqa: E402
    build_ladder,
    load_fixed_income,
    maturities_within,
    month_buckets,
    net_carry,
    parse_maturity,
    sale_to_hit_target,
    simulate,
)


def portfolio_at_target(total: float = 100_000) -> dict[str, float]:
    return {sleeve: total * target for sleeve, target in TARGETS.items()}


class AllocationTests(unittest.TestCase):
    def test_targets_sum_to_one(self) -> None:
        self.assertAlmostEqual(sum(TARGETS.values()), 1.0)

    def test_portfolio_at_target_has_zero_deviation(self) -> None:
        rows = analyze(portfolio_at_target())
        for row in rows:
            self.assertAlmostEqual(row["deviation_pp"], 0.0, places=6)
            self.assertEqual(row["status"], "na banda")

    def test_gap_math(self) -> None:
        rows = {row["sleeve"]: row for row in analyze({"caixa": 100_000})}
        self.assertAlmostEqual(rows["cash_fixed_income"]["gap_to_target"], -80_000)
        self.assertAlmostEqual(rows["real_estate_fiis"]["gap_to_target"], 20_000)
        self.assertEqual(rows["cash_fixed_income"]["status"], "acima da banda")
        self.assertEqual(rows["real_estate_fiis"]["status"], "abaixo da banda")

    def test_portuguese_aliases(self) -> None:
        rows = analyze({"caixa": 20, "fiis": 20, "acoes": 25, "cripto": 5, "exterior": 25, "diversos": 5})
        self.assertEqual(len(rows), 6)

    def test_positions_are_aggregated_by_sleeve(self) -> None:
        data = {
            "positions": [
                {"primary_sleeve": "fiis", "market_value_brl": 1000},
                {"primary_sleeve": "real_estate_fiis", "market_value_brl": 500},
                {"primary_sleeve": "acoes", "quantity": 10, "price_brl": 50},
            ]
        }
        values = load_sleeve_values(data)
        self.assertAlmostEqual(values["real_estate_fiis"], 1500)
        self.assertAlmostEqual(values["brazilian_equities"], 500)

    def test_unknown_sleeve_raises(self) -> None:
        with self.assertRaises(ValueError):
            analyze({"caixa": 100, "imovel": 100})

    def test_non_numeric_raises_with_message(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            analyze({"cash_fixed_income": "10000"})
        self.assertIn("Valor inválido", str(ctx.exception))

    def test_negative_raises(self) -> None:
        with self.assertRaises(ValueError):
            analyze({"cash_fixed_income": -1})

    def test_empty_portfolio_raises(self) -> None:
        with self.assertRaises(ValueError):
            analyze({})

    def test_position_without_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_sleeve_values({"positions": [{"primary_sleeve": "fiis"}]})


class ContributionTests(unittest.TestCase):
    def test_contribution_is_fully_allocated(self) -> None:
        plan = build_contribution_plan(portfolio_at_target(), 5000)
        self.assertAlmostEqual(sum(plan.allocations.values()), 5000, places=6)
        self.assertAlmostEqual(plan.residual, 0.0, places=6)

    def test_allocation_is_proportional_to_deficit(self) -> None:
        plan = build_contribution_plan({"caixa": 100_000}, 1000)
        self.assertEqual(plan.allocations["cash_fixed_income"], 0.0)
        self.assertAlmostEqual(plan.allocations["real_estate_fiis"], 250.00, places=2)
        self.assertAlmostEqual(plan.allocations["cryptoassets"], 62.50, places=2)

    def test_overweight_sleeve_never_receives(self) -> None:
        values = {"cash_fixed_income": 90_000, "real_estate_fiis": 5_000, "brazilian_equities": 5_000}
        plan = build_contribution_plan(values, 5000)
        self.assertEqual(plan.allocations["cash_fixed_income"], 0.0)

    def test_min_ticket_redistributes_small_slices(self) -> None:
        plan = build_contribution_plan(
            {"cash_fixed_income": 100_000}, 1000, {"cryptoassets": 100}
        )
        self.assertEqual(plan.allocations["cryptoassets"], 0.0)
        self.assertAlmostEqual(sum(plan.allocations.values()), 1000, places=6)
        self.assertAlmostEqual(plan.residual, 0.0, places=6)

    def test_impossible_ticket_returns_residual(self) -> None:
        tickets = {sleeve: 100 for sleeve in TARGETS}
        plan = build_contribution_plan(portfolio_at_target(), 10, tickets)
        self.assertAlmostEqual(sum(plan.allocations.values()), 0.0, places=6)
        self.assertAlmostEqual(plan.residual, 10, places=6)
        self.assertTrue(any("liquidez" in note for note in plan.notes))

    def test_unknown_sleeve_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_contribution_plan({"caixa": 5000, "imovel": 1000}, 1000)

    def test_excluded_sleeve_receives_nothing(self) -> None:
        plan = build_contribution_plan(
            {"caixa": 1000, "diversos": 0},
            1000,
            targets=TARGETS,
            exclude={"diversos"},
        )
        self.assertEqual(plan.allocations["diversos"], 0.0)
        self.assertAlmostEqual(sum(plan.allocations.values()), 1000, places=6)

    def test_zero_contribution(self) -> None:
        plan = build_contribution_plan({"caixa": 1000}, 0)
        self.assertEqual(sum(plan.allocations.values()), 0.0)

    def test_empty_portfolio_uses_target_weights(self) -> None:
        plan = build_contribution_plan({}, 1000)
        for sleeve, target in TARGETS.items():
            self.assertAlmostEqual(plan.allocations[sleeve], 1000 * target, places=6)

    def test_post_weights_reflect_allocation(self) -> None:
        plan = build_contribution_plan(portfolio_at_target(), 100_000)
        self.assertAlmostEqual(sum(plan.post_weights.values()), 1.0, places=6)
        for sleeve, target in TARGETS.items():
            self.assertAlmostEqual(plan.post_weights[sleeve], target, places=6)

        overweight = build_contribution_plan({"cash_fixed_income": 100_000}, 100_000)
        self.assertAlmostEqual(overweight.post_weights["cash_fixed_income"], 0.5, places=6)


class PolicyTests(unittest.TestCase):
    def test_default_policy_has_six_sleeves(self) -> None:
        targets = resolve_targets({})
        self.assertEqual(set(targets), set(TARGETS))
        self.assertAlmostEqual(sum(targets.values()), 1.0)
        self.assertAlmostEqual(targets["cash_fixed_income"], 0.20)
        self.assertAlmostEqual(targets["real_estate_fiis"], 0.20)
        self.assertAlmostEqual(targets["diversos"], 0.05)

    def test_legacy_negocios_alias_maps_to_diversos(self) -> None:
        rows = analyze({"caixa": 20, "fiis": 20, "acoes": 25, "cripto": 5, "exterior": 25, "negocios": 5})
        self.assertEqual(len(rows), 6)
        self.assertIn("diversos", {row["sleeve"] for row in rows})

    def test_unknown_policy_field_is_ignored(self) -> None:
        targets = resolve_targets({"legacy_framework": "KRAKEN"})
        self.assertIn("diversos", targets)
        self.assertAlmostEqual(targets["diversos"], 0.05)
        self.assertAlmostEqual(sum(targets.values()), 1.0)

    def test_diversos_position_is_active(self) -> None:
        rows = analyze({"caixa": 20_000, "diversos": 5_000})
        self.assertAlmostEqual(float(rows[0]["total"]), 25_000)

    def test_custom_weights_must_sum_to_one(self) -> None:
        with self.assertRaises(ValueError):
            resolve_targets({"target_weights": {s: 0.2 for s in TARGETS}})

    def test_contribution_enters_cash(self) -> None:
        values = add_contribution_to_cash({"fiis": 1000}, 500)
        self.assertAlmostEqual(values["cash_fixed_income"], 500)
        self.assertAlmostEqual(values["real_estate_fiis"], 1000)


class DriftTests(unittest.TestCase):
    def test_overweight_sleeve_needs_dilution(self) -> None:
        values = {
            "cash_fixed_income": 40000,
            "real_estate_fiis": 80000,
            "brazilian_equities": 30000,
            "cryptoassets": 10000,
            "international_assets": 20000,
            "diversos": 0,
        }
        report = drift_report(values, 5000)
        fiis = next(row for row in report["rows"] if row["sleeve"] == "real_estate_fiis")
        self.assertAlmostEqual(fiis["required_total"], 80000 / 0.25, places=2)
        self.assertAlmostEqual(fiis["months"], (80000 / 0.25 - 180000) / 5000, places=4)

    def test_underweight_sleeve_uses_lower_band(self) -> None:
        report = drift_report({"cash_fixed_income": 100_000}, 1000)
        equities = next(row for row in report["rows"] if row["sleeve"] == "brazilian_equities")
        self.assertAlmostEqual(equities["gap"], 20_000, places=6)
        self.assertAlmostEqual(equities["months"], 20, places=6)


def fixed_income_data() -> dict:
    """Carteira mínima com vencimentos, incluindo um papel sem data."""
    return {
        "as_of": "2026-10-22",
        "positions": [
            {
                "symbol": "LCA-92",
                "primary_sleeve": "cash_fixed_income",
                "market_value_brl": 10_000,
                "maturity": "2026-12-01",
                "indexer": "CDI",
                "rate_pct": 92,
                "tax_exempt": True,
            },
            {
                "symbol": "CDB-PRE-14",
                "primary_sleeve": "cash_fixed_income",
                "market_value_brl": 20_000,
                "maturity": "2027-10-04",
                "indexer": "pré-fixado",
                "rate_pct": 14.15,
            },
            {
                "symbol": "CDB-IPCA-855",
                "primary_sleeve": "cash_fixed_income",
                "market_value_brl": 5_000,
                "maturity": "2028-06-01",
                "indexer": "IPCA+",
                "rate_pct": 8.55,
            },
            {
                "symbol": "RDB-LIQUIDEZ",
                "primary_sleeve": "cash_fixed_income",
                "market_value_brl": 2_000,
            },
            {"symbol": "FII-EXEMPLO", "primary_sleeve": "real_estate_fiis", "market_value_brl": 50_000},
        ],
    }


class LadderTests(unittest.TestCase):
    def test_ladder_groups_by_maturity_year(self) -> None:
        items = load_fixed_income(fixed_income_data())
        ladder = build_ladder(items)
        self.assertAlmostEqual(ladder["total"], 37_000, places=2)
        by_year = {row["year"]: row["value"] for row in ladder["rows"]}
        self.assertAlmostEqual(by_year[2026], 10_000, places=2)
        self.assertAlmostEqual(by_year[2027], 20_000, places=2)
        self.assertAlmostEqual(by_year[2028], 5_000, places=2)
        self.assertAlmostEqual(ladder["rows"][-1]["cumulative_pct"], (35_000 / 37_000) * 100, places=6)

    def test_position_without_maturity_is_reported_not_silently_dropped(self) -> None:
        ladder = build_ladder(load_fixed_income(fixed_income_data()))
        self.assertAlmostEqual(ladder["undated"], 2_000, places=2)
        self.assertAlmostEqual(ladder["total"], 37_000, places=2)

    def test_horizon_boundary_maturity_counts_inside_the_window(self) -> None:
        items = load_fixed_income(fixed_income_data())
        reference = parse_maturity("2026-10-22")
        # 2027-10-04 cai dentro de 12 meses de 2026-10-22: 10.000 + 20.000.
        self.assertAlmostEqual(maturities_within(items, reference, 12), 30_000, places=2)
        self.assertAlmostEqual(maturities_within(items, reference, 6), 10_000, places=2)

    def test_month_bucket_puts_horizon_maturity_in_last_month(self) -> None:
        items = load_fixed_income(fixed_income_data())
        buckets = month_buckets(items, parse_maturity("2026-10-22"), 12)
        self.assertAlmostEqual(buckets[1], 10_000, places=2)  # dez/2026 é o 2º mês
        self.assertAlmostEqual(buckets[11], 20_000, places=2)  # out/2027 fecha o horizonte
        self.assertEqual(sum(buckets.values()), 30_000)

    def test_sale_sizing_lands_exactly_on_target(self) -> None:
        values = {"cash_fixed_income": 100_000, "real_estate_fiis": 100_000}
        sizing = sale_to_hit_target(values, 1_000, [], parse_maturity("2026-10-22"), 12, 0.20)
        self.assertAlmostEqual(sizing["total_at_horizon"], 212_000, places=2)
        self.assertAlmostEqual(sizing["target_value"], 42_400, places=2)
        self.assertAlmostEqual(sizing["sale_brl"], 57_600, places=2)
        self.assertFalse(sizing["already_enough"])

    def test_sale_sizing_reports_when_flow_is_already_enough(self) -> None:
        values = {"cash_fixed_income": 10_000, "real_estate_fiis": 100_000}
        sizing = sale_to_hit_target(values, 0, [], parse_maturity("2026-10-22"), 12, 0.20)
        self.assertTrue(sizing["already_enough"])
        self.assertLess(sizing["sale_brl"], 0)

    def test_simulation_dilutes_with_contribution_and_maturity(self) -> None:
        values = {"cash_fixed_income": 100_000, "real_estate_fiis": 100_000}
        items = [
            {
                "symbol": "X",
                "value": 50_000,
                "maturity": parse_maturity("2026-11-15"),
                "indexer": "CDI",
                "rate_pct": 100,
                "tax_exempt": False,
                "net_value": None,
                "issuer": "",
            }
        ]
        result = simulate(values, 10_000, items, parse_maturity("2026-10-22"), 6)
        # mês 1: sai 50.000 do caixa e entra 10.000 de aporte.
        self.assertAlmostEqual(result["path"][0]["cash_value"], 50_000, places=2)
        self.assertAlmostEqual(result["path"][0]["total"], 210_000, places=2)
        self.assertAlmostEqual(result["path"][-1]["weight_pct"], 50_000 / 260_000 * 100, places=6)

    def test_net_carry_compares_isento_with_taxed(self) -> None:
        items = {item["symbol"]: item for item in load_fixed_income(fixed_income_data())}
        lca, _ = net_carry(items["LCA-92"], cdi=13.90)
        prefixado, _ = net_carry(items["CDB-PRE-14"], cdi=13.90, ir_pct=15)
        self.assertAlmostEqual(lca, 92 / 100 * 13.90, places=6)
        self.assertAlmostEqual(prefixado, 14.15 * 0.85, places=6)
        # 92% do CDI isento (12,79%) rende mais que 14,15% tributado (12,03%).
        self.assertGreater(lca, prefixado)

    def test_ipca_needs_explicit_inflation(self) -> None:
        items = {item["symbol"]: item for item in load_fixed_income(fixed_income_data())}
        net, reason = net_carry(items["CDB-IPCA-855"], cdi=13.90)
        self.assertIsNone(net)
        self.assertIn("inflation", reason)
        net, reason = net_carry(items["CDB-IPCA-855"], cdi=13.90, inflation=4.5)
        self.assertIsNone(reason)
        self.assertAlmostEqual(net, ((1.0855 * 1.045) - 1) * 100 * 0.85, places=6)

    def test_unknown_indexer_raises(self) -> None:
        data = fixed_income_data()
        data["positions"][0]["indexer"] = "TR"
        with self.assertRaises(ValueError):
            load_fixed_income(data)

    def test_invalid_maturity_raises(self) -> None:
        data = fixed_income_data()
        data["positions"][0]["maturity"] = "31/12/2026"
        with self.assertRaises(ValueError):
            load_fixed_income(data)

    def test_sleeves_only_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            load_fixed_income({"sleeves": {"caixa": 1000}})


if __name__ == "__main__":
    unittest.main()
