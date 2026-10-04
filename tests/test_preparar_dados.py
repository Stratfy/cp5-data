"""Regressao da carga real de quatro ZIPs, sem usar ou alterar os dados da entrega."""
import csv
from contextlib import closing
import hashlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import Repository


class PreparationTests(unittest.TestCase):
    FIELDS = ("Id", "Ano", "Data", "CodigoUnidadeGestora", "UnidadeGestora",
              "ValorPago", "Documento", "ValorEmpenho", "ValorLiquidado", "ValorRap")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cp5-preparo-teste-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "origem"
        self.source.mkdir()
        self.output = self.root / "saida"
        self.database = self.output / "pagamentos_2024.sqlite3"

    def row(self, identifier, value="10,00", date="10/01/2024 00:00:00", unit="Saude", code="001", year="2024"):
        return dict(zip(self.FIELDS, (str(identifier), year, date, code, unit, value,
                                     "2024OB0001", "0,00", "0,00", "0,00")))

    def prepare(self, rows):
        # Partes vazias ainda possuem um CSV e cabecalho valido, como exige a carga.
        for number in range(1, 5):
            content = io.StringIO(newline="")
            writer = csv.DictWriter(content, fieldnames=self.FIELDS, delimiter=";")
            writer.writeheader()
            writer.writerows(rows if number == 1 else [])
            path = self.source / f"despesas_es_2024_completo_parte_{number:02d}.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr(f"parte_{number:02d}.csv", content.getvalue().encode("utf-8-sig"))
        source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in self.source.iterdir()}
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "preparar_dados.py"),
             "--origem", str(self.source), "--saida", str(self.output)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(source_hashes, {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                        for path in self.source.iterdir()})
        summary = json.loads((self.output / "resumo_analise.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["verificacao"], {
            "contagem_base_reconciliada": True, "ranking_reconciliado": True,
            "meses_reconciliados": True, "integridade_sqlite": "ok"})
        return summary

    def read_csv(self, name):
        with (self.output / name).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter=";")
            return reader.fieldnames, list(reader)

    def test_valores_totalmente_ausentes_permanecem_null_em_todos_os_artefatos(self):
        summary = self.prepare([self.row(1, value=""), self.row(2, value="NaN")])
        self.assertEqual(summary["total_registros"], 2)
        self.assertIsNone(summary["total_pago_centavos"])
        self.assertIsNone(summary["total_pago_reais"])
        self.assertIsNone(summary["ranking_unidades"][0]["valor_pago_centavos"])
        self.assertIsNone(summary["ranking_unidades"][0]["participacao_percentual"])
        self.assertIsNone(summary["evolucao_mensal"][0]["valor_pago_centavos"])
        self.assertIsNone(summary["estatisticas_mensais"]["media_mensal_reais"])
        self.assertIsNone(summary["estatisticas_mensais"]["desvio_padrao_populacional_mensal_reais"])
        self.assertEqual(summary["estatistica_amostral"]["n"], 0)
        self.assertIsNone(summary["estatistica_amostral"]["limite_inferior"])
        self.assertIsNone(Repository(self.database).summary({})["total_centavos"])
        for filename in ("ranking_unidades.csv", "evolucao_mensal.csv"):
            _, rows = self.read_csv(filename)
            self.assertEqual(rows[0]["valor_pago_centavos"], "")
            self.assertEqual(rows[0]["valor_pago_reais"], "")

    def test_ausencia_zero_negativo_e_valor_sem_mes_conciliam_sem_perder_distincao(self):
        summary = self.prepare([
            self.row(1, value="100,00"),
            self.row(2, value=""),
            self.row(3, value="", date="10/02/2024 00:00:00", unit="Sem valor", code="002"),
            self.row(4, value="0,00", date="10/03/2024 00:00:00", unit="Zero", code="003"),
            self.row(5, value="-25,00", date="10/04/2024 00:00:00", unit="Ajuste", code="004"),
            self.row(6, value="5,00", date="10/01/2025 00:00:00"),
        ])
        self.assertEqual(summary["total_pago_centavos"], 8000)
        self.assertEqual(summary["soma_sem_mes_valido_centavos"], 500)
        self.assertEqual([row["valor_pago_centavos"] for row in summary["evolucao_mensal"]],
                         [10000, None, 0, -2500])
        self.assertEqual([row["valor_pago_centavos"] for row in summary["ranking_unidades"]],
                         [10500, 0, -2500, None])
        stats = summary["estatisticas_mensais"]
        self.assertEqual(stats["n_meses"], 4)
        self.assertEqual(stats["media_mensal_reais"], 25)
        self.assertEqual(stats["mediana_mensal_reais"], 0)
        self.assertIn("[2]", stats["natureza"])
        self.assertEqual(summary["estatistica_amostral"]["N"], 4)
        self.assertEqual(summary["estatistica_amostral"]["k"], 2)
        self.assertEqual(Repository(self.database).summary({})["total_centavos"], 8000)

    def test_um_mes_com_valor_e_varios_ausentes_nao_gera_desvio_amostral(self):
        summary = self.prepare([
            self.row(1, value="0,00"),
            self.row(2, value="", date="10/02/2024 00:00:00"),
            self.row(3, value="", date="10/03/2024 00:00:00"),
        ])
        stats = summary["estatisticas_mensais"]
        self.assertEqual(summary["total_pago_centavos"], 0)
        self.assertEqual(stats["media_mensal_reais"], 0)
        self.assertIsNone(stats["desvio_padrao_amostral_mensal_reais"])
        self.assertIsNone(stats["variancia_amostral_mensal_reais_quadrados"])
        self.assertEqual(stats["desvio_padrao_populacional_mensal_reais"], 0)

    def test_reconstrucao_sem_amostra_ou_meses_substitui_csv_antigo_por_cabecalho(self):
        self.prepare([self.row(1)])
        previous_headers = {}
        for name in ("amostra_estatistica.csv", "evolucao_mensal.csv"):
            previous_headers[name], rows = self.read_csv(name)
            self.assertEqual(len(rows), 1)
        summary = self.prepare([self.row(2, value="", date="")])
        self.assertIsNone(summary["total_pago_centavos"])
        self.assertEqual(summary["evolucao_mensal"], [])
        self.assertEqual(summary["estatistica_amostral"]["n"], 0)
        for name, previous_header in previous_headers.items():
            header, rows = self.read_csv(name)
            self.assertEqual(header, previous_header)
            self.assertEqual(rows, [])

    def test_reconstrucao_sem_linhas_de_2024_limpa_ranking_e_preserva_total_vazio(self):
        self.prepare([self.row(1)])
        previous_header, _ = self.read_csv("ranking_unidades.csv")
        summary = self.prepare([self.row(2, year="2025")])
        self.assertEqual(summary["total_registros"], 0)
        self.assertEqual(summary["total_pago_centavos"], 0)
        self.assertEqual(summary["registros_com_valor_nao_zero"], 0)
        self.assertEqual(summary["ranking_unidades"], [])
        self.assertEqual(self.read_csv("ranking_unidades.csv"), (previous_header, []))
        self.assertEqual(summary["auditoria"]["registros_outros_anos"], 1)

    def test_carga_completa_preserva_centavos_auditoria_rastreabilidade_e_colunas(self):
        summary = self.prepare([
            self.row(1, value="1.234,56"),
            self.row(1, value="-234,56"),
            self.row(3, value="0,00", date="10/02/2024 00:00:00", unit="Educacao", code="002"),
            self.row(4, value="1,005", date="10/02/2024 00:00:00", unit="Educacao", code="002"),
        ])
        self.assertEqual(summary["total_pago_centavos"], 100101)
        self.assertEqual(summary["registros_com_valor_nao_zero"], 3)
        self.assertEqual(summary["auditoria"]["ids_repetidos_registros_adicionais"], 1)
        self.assertEqual(summary["auditoria"]["numericos"]["ValorPago"]["valores_com_fracao_inferior_a_centavo"], 1)
        self.assertEqual(summary["estatistica_amostral"]["N"], 4)
        self.assertEqual(summary["estatistica_amostral"]["k"], 2)
        header, ranking = self.read_csv("ranking_unidades.csv")
        self.assertEqual(header, ["posicao", "codigo_unidade_gestora", "unidade_gestora", "registros",
                                  "registros_com_valor_nao_zero", "valor_pago_centavos", "valor_pago_reais",
                                  "participacao_percentual"])
        self.assertEqual([row["valor_pago_centavos"] for row in ranking], ["100000", "101"])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute(
                "SELECT id_origem, valor_centavos, arquivo_origem, linha_origem FROM pagamentos ORDER BY id"
            ).fetchall(), [("1", 123456, "parte_01.csv", 2), ("1", -23456, "parte_01.csv", 3),
                          ("3", 0, "parte_01.csv", 4), ("4", 101, "parte_01.csv", 5)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
