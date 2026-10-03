"""Distingue valores ausentes, zeros verdadeiros e valores fora do calendário."""
import csv
import io
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import Repository, make_handler


class IncompleteDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temporary.name) / "incomplete.sqlite3"
        connection = sqlite3.connect(cls.database)
        try:
            connection.execute("""CREATE TABLE pagamentos (id INTEGER PRIMARY KEY, id_origem TEXT, ano INTEGER,
                data_pagamento TEXT, mes INTEGER, codigo_unidade_gestora TEXT, unidade_gestora TEXT,
                valor_centavos INTEGER, tipo_documento TEXT, numero_documento TEXT,
                arquivo_origem TEXT, linha_origem INTEGER)""")
            rows = [
                (1, "origem1", 2024, "2024-01-10", 1, "10", "Saúde", 10000, "OB", "DOC1", "origem.csv", 2),
                (2, "origem2", 2024, "2024-01-11", 1, "10", "Saúde", None, "OB", "DOC2", "origem.csv", 3),
                (3, "origem3", 2024, "2024-02-01", 2, "20", "Sem valores", None, "OB", "DOC3", "origem.csv", 4),
                (4, "origem4", 2024, None, None, "10", "Saúde", -2500, "OB", "DOC4", "origem.csv", 5),
                (5, "origem5", 2024, None, None, "20", "Sem valores", None, "OB", "DOC5", "origem.csv", 6),
                (6, "origem6", 2024, "2024-03-01", 3, "30", "Zero verdadeiro", 0, "OB", "DOC6", "origem.csv", 7),
                # A preparação mantém Data fora do ano, mas não lhe atribui mês de 2024.
                (7, "origem7", 2024, "2025-01-01", None, "40", "Data fora do ano", 500, "OB", "DOC7", "origem.csv", 8),
            ]
            connection.executemany("INSERT INTO pagamentos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            connection.commit()
        finally:
            connection.close()
        cls.repository = Repository(cls.database)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.database))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temporary.cleanup()

    def get_json(self, endpoint, params=None):
        with urlopen(self.base + endpoint + "?" + urlencode(params or {}), timeout=10) as response:
            return json.load(response)

    def get_csv(self, kind, params=None):
        parameters = {"tipo": kind} | (params or {})
        with urlopen(self.base + "/api/exportar?" + urlencode(parameters), timeout=10) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(body), delimiter=";"))

    def test_recorte_so_com_valores_ausentes_nao_vira_zero(self):
        summary = self.repository.summary({"unidade": ["20", "Sem valores"]})
        self.assertEqual(summary["registros"], 2)
        self.assertIsNone(summary["total_centavos"])
        self.assertEqual(summary["registros_com_valor"], 0)
        self.assertEqual(summary["registros_sem_valor"], 2)
        self.assertEqual(summary["zeros"], 0)
        empty = self.repository.summary({"unidade": ["inexistente", "Sem linhas"]})
        self.assertEqual(empty["registros"], 0)
        self.assertEqual(empty["total_centavos"], 0)

    def test_total_disponivel_e_diferenca_mensal_sao_explicitados(self):
        summary = self.repository.summary({})
        self.assertEqual(summary["registros"], 7)
        self.assertEqual(summary["total_centavos"], 8000)
        self.assertEqual(summary["registros_com_valor"], 4)
        self.assertEqual(summary["registros_sem_valor"], 3)
        self.assertEqual(summary["registros_sem_data"], 2)
        self.assertEqual(summary["registros_sem_mes"], 3)
        self.assertEqual(summary["total_com_mes_centavos"], 10000)
        self.assertEqual(summary["total_sem_mes_centavos"], -2000)
        self.assertEqual(summary["diferenca_serie_centavos"], -2000)
        self.assertEqual(summary["total_centavos"], summary["total_com_mes_centavos"] + summary["diferenca_serie_centavos"])

    def test_ranking_preserva_null_apos_totais_conhecidos(self):
        ranking = self.repository.ranking({}, limit=None)
        self.assertEqual([row["total_centavos"] for row in ranking], [7500, 500, 0, None])
        unavailable = ranking[-1]
        self.assertEqual(unavailable["nome"], "Sem valores")
        self.assertEqual(unavailable["registros_com_valor"], 0)
        self.assertEqual(unavailable["registros_sem_valor"], 2)

    def test_mes_sem_valor_mes_zerado_e_mes_sem_linhas_sao_distintos(self):
        months = self.repository.monthly({})
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0]["total_centavos"], 10000)
        self.assertEqual(months[0]["registros_sem_valor"], 1)
        self.assertIsNone(months[1]["total_centavos"])
        self.assertEqual(months[1]["registros"], 1)
        self.assertEqual(months[1]["registros_com_valor"], 0)
        self.assertEqual(months[2]["total_centavos"], 0)
        self.assertEqual(months[2]["registros_com_valor"], 1)
        self.assertEqual(months[3]["total_centavos"], 0)
        self.assertEqual(months[3]["registros"], 0)
        available_monthly = sum(row["total_centavos"] for row in months if row["total_centavos"] is not None)
        self.assertEqual(available_monthly, 10000)

    def test_csv_agregado_sem_valores_fica_vazio_e_nao_quebra(self):
        ranking = self.get_csv("ranking")
        unknown = next(row for row in ranking if row["CodigoUnidadeGestora"] == "20")
        self.assertEqual(unknown["ValorPagoLiquido_R$"], "")
        self.assertEqual(unknown["RegistrosComValor"], "0")
        self.assertEqual(unknown["RegistrosSemValor"], "2")
        months = self.get_csv("mensal")
        self.assertEqual(months[1]["ValorPagoLiquido_R$"], "")
        self.assertEqual(months[1]["RegistrosSemValor"], "1")
        self.assertEqual(months[2]["ValorPagoLiquido_R$"], "0,00")
        self.assertEqual(len(months), 12)

    def test_csv_detalhes_distingue_ausencia_zero_e_negativo(self):
        rows = {row["IdOrigem"]: row for row in self.get_csv("detalhes")}
        self.assertEqual(rows["origem2"]["ValorPago_R$"], "")
        self.assertEqual(rows["origem6"]["ValorPago_R$"], "0,00")
        self.assertEqual(rows["origem4"]["ValorPago_R$"], "-25,00")
        self.assertEqual(rows["origem4"]["DataRegistro"], "")
        self.assertEqual(rows["origem4"]["ArquivoOrigem"], "origem.csv")
        self.assertEqual(rows["origem4"]["LinhaOrigem"], "5")

    def test_api_serializa_null_e_contagens_sem_esconder_a_origem(self):
        unit = json.dumps(["20", "Sem valores"])
        summary = self.get_json("/api/resumo", {"unidade": unit})
        self.assertIsNone(summary["total_centavos"])
        self.assertEqual(summary["registros_sem_valor"], 2)
        rows = self.get_json("/api/registros", {"unidade": unit})["linhas"]
        self.assertTrue(all(row["valor_centavos"] is None for row in rows))
        self.assertTrue(any(row["data_pagamento"] is None for row in rows))
        self.assertEqual({row["linha_origem"] for row in rows}, {4, 6})


if __name__ == "__main__":
    unittest.main(verbosity=2)
