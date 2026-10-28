import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from save_portfolio import IngestError, save_portfolio  # noqa: E402
from maturity_ladder import build_ladder, load_fixed_income  # noqa: E402


def base_data(**overrides):
    data = {
        "as_of": "2026-10-22",
        "source": "teste",
        "data_coverage": "completa",
        "contribution_month_brl": 0,
        "positions": [
            {
                "symbol": "BOVA11",
                "name": "iShares Ibovespa",
                "primary_sleeve": "brazilian_equities",
                "quantity": 10,
                "price_brl": 100.0,
                "market_value_brl": 1000.0,
            },
            {
                "symbol": "HGLG11",
                "name": "CSHG Logística",
                "primary_sleeve": "real_estate_fiis",
                "market_value_brl": 2000.0,
            },
            {
                "symbol": "CDB-XP",
                "name": "CDB XP",
                "primary_sleeve": "caixa",
                "market_value_brl": 3000.0,
            },
        ],
    }
    data.update(overrides)
    return data


class SavePortfolioTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "state" / "portfolio.json"
        self.history = self.root / "state" / "history"

    def tearDown(self):
        self.temp.cleanup()

    def save(self, data, **kwargs):
        return save_portfolio(
            data,
            state_path=self.state,
            history_dir=self.history,
            **kwargs,
        )

    def test_grava_e_reconcilia(self):
        result = self.save(base_data(), expected_total=6000.0)
        self.assertTrue(self.state.exists())
        self.assertEqual(result["extracted_total"], 6000.0)
        self.assertEqual(result["coverage"], "completa")
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["positions"]), 3)
        self.assertEqual(saved["target_weights"]["cash_fixed_income"], 0.20)

    def test_rejeita_total_divergente(self):
        with self.assertRaises(IngestError) as ctx:
            self.save(base_data(), expected_total=6500.0)
        self.assertIn("não reconcilia", str(ctx.exception))
        self.assertFalse(self.state.exists())

    def test_calcula_valor_por_quantidade_e_preco(self):
        data = base_data()
        data["positions"][0].pop("market_value_brl")
        result = self.save(data, expected_total=6000.0)
        self.assertEqual(result["sleeves_total"], 6000.0)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(saved["positions"][0]["market_value_brl"], 1000.0)
        self.assertEqual(saved["positions"][0]["quantity"], 10)

    def test_sleeve_desconhecido(self):
        data = base_data()
        data["positions"][0]["primary_sleeve"] = "fundos_imobiliarios"
        with self.assertRaises(IngestError) as ctx:
            self.save(data)
        self.assertIn("Sleeve desconhecido", str(ctx.exception))

    def test_cobertura_ausente_vira_parcial(self):
        data = base_data()
        data.pop("data_coverage")
        result = self.save(data, expected_total=6000.0)
        self.assertEqual(result["coverage"], "parcial")
        self.assertTrue(any("Cobertura não declarada" in w for w in result["warnings"]))
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(saved["data_coverage"], "parcial")

    def test_backup_do_estado_anterior(self):
        self.save(base_data(), expected_total=6000.0)
        result = self.save(base_data(), expected_total=6000.0)
        self.assertIsNotNone(result["backup_path"])
        self.assertTrue(Path(result["backup_path"]).exists())
        self.assertEqual(len(list(self.history.glob("*.json"))), 1)

    def test_dry_run_nao_grava(self):
        result = self.save(base_data(), expected_total=6000.0, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertFalse(self.state.exists())

    def test_preserva_politica_existente(self):
        self.save(base_data(), expected_total=6000.0)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        state["min_ticket_brl"] = {"brazilian_equities": 123}
        state["investor"] = {"risk_profile": "conservador"}
        self.state.write_text(json.dumps(state), encoding="utf-8")

        self.save(base_data(), expected_total=6000.0)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(saved["min_ticket_brl"]["brazilian_equities"], 123)
        self.assertEqual(saved["investor"]["risk_profile"], "conservador")

    def test_valor_liquido_maior_que_bruto_avisa(self):
        data = base_data()
        data["positions"][2]["net_value_brl"] = 4000.0
        result = self.save(data, expected_total=6000.0)
        self.assertTrue(any("maior que o bruto" in w for w in result["warnings"]))

    def test_unmapped_entra_na_reconciliacao(self):
        data = base_data(
            unmapped=[{"item": "GOLD11", "value_brl": 500.0, "reason": "commodity"}]
        )
        result = self.save(data, expected_total=6500.0)
        self.assertEqual(result["sleeves_total"], 6000.0)
        self.assertEqual(result["unmapped_total"], 500.0)
        self.assertEqual(result["extracted_total"], 6500.0)

    def test_simbolo_duplicado_soma(self):
        data = base_data()
        data["positions"].append(
            {
                "symbol": "BOVA11",
                "name": "iShares Ibovespa",
                "primary_sleeve": "brazilian_equities",
                "market_value_brl": 500.0,
            }
        )
        result = self.save(data, expected_total=6500.0)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        bova = [p for p in saved["positions"] if p["symbol"] == "BOVA11"][0]
        self.assertEqual(bova["market_value_brl"], 1500.0)
        self.assertEqual(result["position_count"], 3)

    def test_valor_negativo_rejeitado(self):
        data = base_data()
        data["positions"][1]["market_value_brl"] = -1
        with self.assertRaises(IngestError):
            self.save(data)

    def test_reconciliacao_por_grupo(self):
        data = base_data(
            reconciliation=[
                {"group": "Ações", "expected_brl": 1000.0},
                {"group": "FIIs", "expected_brl": 2000.0},
                {"group": "RF", "expected_brl": 3000.0},
            ]
        )
        for position, group in zip(data["positions"], ["Ações", "FIIs", "RF"]):
            position["group"] = group
        result = self.save(data, expected_total=6000.0)
        self.assertEqual(result["extracted_total"], 6000.0)

    def test_grupo_divergente_rejeita(self):
        data = base_data(
            reconciliation=[{"group": "FIIs", "expected_brl": 2500.0}]
        )
        data["positions"][1]["group"] = "FIIs"
        with self.assertRaises(IngestError) as ctx:
            self.save(data, expected_total=6000.0)
        self.assertIn("Subtotal de grupo", str(ctx.exception))

    def test_grupo_inclui_unmapped(self):
        data = base_data(
            unmapped=[{"item": "OURO", "group": "ETF", "value_brl": 500.0, "reason": "commodity"}],
            reconciliation=[{"group": "ETF", "expected_brl": 1500.0}],
        )
        data["positions"][0]["group"] = "ETF"
        result = self.save(data, expected_total=6500.0)
        self.assertEqual(result["unmapped_total"], 500.0)

    def test_posicao_residual_avisa(self):
        data = base_data()
        data["positions"][1]["market_value_brl"] = 0.02
        result = self.save(data)
        self.assertTrue(any("residual" in w for w in result["warnings"]))

    def test_preserva_metadados_de_renda_fixa(self):
        data = base_data()
        data["positions"][2].update(
            {
                "maturity": "2027-10-04",
                "indexer": "pré-fixado",
                "rate_pct": 14.15,
                "tax_exempt": False,
            }
        )
        self.save(data, expected_total=6000.0)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        cdb = [p for p in saved["positions"] if p["symbol"] == "CDB-XP"][0]
        self.assertEqual(cdb["maturity"], "2027-10-04")
        self.assertEqual(cdb["indexer"], "PRE")
        self.assertEqual(cdb["rate_pct"], 14.15)
        self.assertFalse(cdb["tax_exempt"])

    def test_escada_roda_no_estado_gravado(self):
        """Regressão: a escada precisa ler os metadados do próprio state."""
        data = base_data()
        data["positions"][2].update(
            {
                "maturity": "2026-12-01",
                "indexer": "CDI",
                "rate_pct": 92,
                "tax_exempt": True,
            }
        )
        self.save(data, expected_total=6000.0)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        fixed_income = load_fixed_income(saved)
        self.assertEqual(len(fixed_income), 1)
        self.assertEqual(fixed_income[0]["maturity"].isoformat(), "2026-12-01")
        self.assertEqual(build_ladder(fixed_income)["undated"], 0.0)

    def test_renda_fixa_sem_vencimento_avisa(self):
        data = base_data()
        data["positions"][2].update({"indexer": "CDI", "rate_pct": 92})
        result = self.save(data, expected_total=6000.0)
        self.assertTrue(any("sem 'maturity'" in w for w in result["warnings"]))

    def test_indexador_invalido_rejeitado(self):
        data = base_data()
        data["positions"][2]["indexer"] = "TR"
        with self.assertRaises(IngestError) as ctx:
            self.save(data, expected_total=6000.0)
        self.assertIn("Indexador desconhecido", str(ctx.exception))

    def test_mesmo_ticker_com_vencimentos_diferentes_nao_soma(self):
        data = base_data()
        data["positions"] = [
            {
                "symbol": "CDB-OMNI",
                "name": "Omni",
                "primary_sleeve": "caixa",
                "market_value_brl": 1000.0,
                "maturity": "2027-10-04",
                "indexer": "PRE",
                "rate_pct": 14.65,
            },
            {
                "symbol": "CDB-OMNI",
                "name": "Omni",
                "primary_sleeve": "caixa",
                "market_value_brl": 2000.0,
                "maturity": "2028-10-02",
                "indexer": "PRE",
                "rate_pct": 14.38,
            },
        ]
        result = self.save(data, expected_total=3000.0)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(result["position_count"], 2)
        self.assertEqual(
            len({p["maturity"] for p in saved["positions"]}), 2
        )


if __name__ == "__main__":
    unittest.main()
