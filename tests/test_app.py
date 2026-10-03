"""Casos de cálculo, filtros, rastreabilidade, paginação e API em uma base pequena."""
import csv
import gzip
import io
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import Repository, make_handler, ensure_database


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temporary.name) / "test.sqlite3"
        with sqlite3.connect(cls.database) as connection:
            connection.execute("""CREATE TABLE pagamentos (id INTEGER PRIMARY KEY, id_origem TEXT, ano INTEGER,
                data_pagamento TEXT, mes INTEGER, codigo_unidade_gestora TEXT, unidade_gestora TEXT,
                valor_centavos INTEGER, tipo_documento TEXT, numero_documento TEXT,
                arquivo_origem TEXT, linha_origem INTEGER)""")
            rows = [
                (1, "origem1", 2024, "2024-01-01", 1, "10", "Saúde", 1000, "Pagamento", "1", "parte_01.csv", 2),
                (2, "origem1", 2024, "2024-01-02", 1, "10", "Saúde", -250, "Ajuste", "2", "parte_01.csv", 3),
                (3, "origem3", 2024, "2024-02-03", 2, "20", "Educação", 0, "Pagamento", "3", "parte_02.csv", 2),
                (4, "=2+2", 2024, "2024-02-04", 2, "10", "=UNIDADE_TESTE", -500, "Pagamento", "@DOC", "parte_02.csv", 3),
                (5, "origem5", 2025, "2025-01-01", 1, "10", "Saúde", 999999, "Pagamento", "5", "outro.csv", 2),
            ]
            rows.extend((index + 6, f"origem{index + 6}", 2024, "2024-03-01", 3, "30", "Gestão", 100,
                         "Pagamento", str(index), "parte_03.csv", index + 2) for index in range(22))
            connection.executemany("INSERT INTO pagamentos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
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

    def get_json(self, path, params=None):
        with urlopen(self.base + path + "?" + urlencode(params or {}), timeout=10) as response:
            return json.load(response)

    def test_centavos_negativos_zeros_e_ano(self):
        summary = self.repository.summary({"mes": None, "unidade": None})
        self.assertEqual(summary["total_centavos"], 2450)
        self.assertEqual(summary["registros"], 26)
        self.assertEqual(summary["ajustes"], 2)
        self.assertEqual(summary["ajustes_centavos"], -750)
        self.assertEqual(summary["zeros"], 1)
        self.assertEqual(summary["unidades"], 4)

    def test_filtro_mes_unidade_e_nome(self):
        filters = {"mes": 1, "unidade": ["10", "Saúde"]}
        summary = self.repository.summary(filters)
        self.assertEqual(summary["total_centavos"], 750)
        self.assertEqual(summary["registros"], 2)
        self.assertEqual(self.repository.monthly(filters)[0]["mes"], 1)
        self.assertEqual(len(self.repository.monthly(filters)), 1)
        self.assertEqual(self.repository.summary({"mes": 2, "unidade": ["10", "Saúde"]})["registros"], 0)

    def test_mes_sem_registro_distingue_zero(self):
        months = self.repository.monthly({"mes": None, "unidade": ["20", "Educação"]})
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0]["registros"], 0)
        self.assertEqual(months[1]["registros"], 1)
        self.assertEqual(months[0]["total_centavos"], months[1]["total_centavos"])

    def test_ranking_ordenado_e_total_conciliado(self):
        ranking = self.repository.ranking({"mes": None, "unidade": None}, limit=None)
        self.assertEqual([row["total_centavos"] for row in ranking], [2200, 750, 0, -500])
        monthly = self.repository.monthly({"mes": None, "unidade": None})
        self.assertEqual(sum(row["total_centavos"] for row in monthly), 2450)
        self.assertEqual(sum(row["total_centavos"] for row in ranking), 2450)

    def test_paginacao_estavel_sem_perder_registros(self):
        filters = {"mes": None, "unidade": None}
        first, second = self.repository.records(filters, 1), self.repository.records(filters, 2)
        self.assertEqual((len(first["linhas"]), len(second["linhas"])), (20, 6))
        self.assertEqual(len({row["id"] for row in first["linhas"] + second["linhas"]}), 26)
        self.assertEqual(first["paginas"], 2)
        self.assertEqual(self.repository.records(filters, 3)["linhas"], [])

    def test_rastreabilidade_e_ids_repetidos_preservados(self):
        rows = self.repository.records({"mes": 1, "unidade": None})["linhas"]
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["id_origem"] for row in rows}, {"origem1"})
        self.assertEqual({(row["arquivo_origem"], row["linha_origem"]) for row in rows}, {("parte_01.csv", 2), ("parte_01.csv", 3)})

    def test_api_filtros_invalidos_recebem_400(self):
        invalid_queries = ["mes=13", "mes=-1", "mes=abc", "mes=1&mes=2", "pagina=0", "pagina=abc",
                           "unidade=abc", "unidade=%5B1%2C2%5D", "desconhecido=1"]
        for query in invalid_queries:
            with self.subTest(query=query), self.assertRaises(HTTPError) as error:
                urlopen(self.base + "/api/registros?" + query, timeout=10)
            self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/api/exportar?tipo=invalido", timeout=10)
        self.assertEqual(error.exception.code, 400)

    def test_sql_parametrizado_unidade_inexistente(self):
        data = self.get_json("/api/resumo", {"unidade": json.dumps(["10' OR 1=1 --", "Saúde"])})
        self.assertEqual(data["registros"], 0)
        self.assertEqual(data["total_centavos"], 0)

    def test_csv_filtro_formula_e_numero_negativo(self):
        params = urlencode({"mes": 2, "tipo": "detalhes"})
        with urlopen(self.base + "/api/exportar?" + params, timeout=10) as response:
            self.assertIn("attachment", response.headers["Content-Disposition"])
            body = response.read().decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(body), delimiter=";"))
        self.assertEqual(len(rows), 2)
        malicious = next(row for row in rows if row["IdOrigem"].endswith("2+2"))
        self.assertEqual(malicious["IdOrigem"], "'=2+2")
        self.assertEqual(malicious["UnidadeGestora"], "'=UNIDADE_TESTE")
        self.assertEqual(malicious["NumeroDocumento"], "'@DOC")
        self.assertEqual(malicious["ValorPago_R$"], "-5,00")
        self.assertNotIn("CPF", body)

    def test_csv_ranking_completo_e_mensal_conciliam(self):
        for kind in ("ranking", "mensal"):
            with self.subTest(kind=kind), urlopen(self.base + "/api/exportar?tipo=" + kind, timeout=10) as response:
                rows = list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig")), delimiter=";"))
            cents = sum(int(row["ValorPagoLiquido_R$"].replace(",", "")) for row in rows)
            self.assertEqual(cents, 2450)
        self.assertEqual(len(rows), 12)

    def test_opcoes_chaves_e_arquivo_nao_encontrado(self):
        options = self.get_json("/api/opcoes")
        self.assertEqual(len(options["unidades"]), 4)
        self.assertEqual(json.loads(options["unidades"][0]["chave"]), ["10", "=UNIDADE_TESTE"])
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/arquivo-inexistente", timeout=10)
        self.assertEqual(error.exception.code, 404)

    def test_base_inexistente_recebe_503(self):
        missing_server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Path(self.temporary.name) / "missing.sqlite3"))
        thread = threading.Thread(target=missing_server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(HTTPError) as error:
                urlopen(f"http://127.0.0.1:{missing_server.server_port}/api/resumo", timeout=10)
            self.assertEqual(error.exception.code, 503)
        finally:
            missing_server.shutdown()
            missing_server.server_close()
            thread.join()

    def test_recuperacao_gzip_sem_sobrescrever_base(self):
        target = Path(self.temporary.name) / "recovered.sqlite3"
        compressed = target.with_suffix(".sqlite3.gz")
        with gzip.open(compressed, "wb") as destination:
            destination.write(self.database.read_bytes())
        self.assertTrue(ensure_database(target))
        self.assertEqual(Repository(target).summary({})["total_centavos"], 2450)
        original_bytes = target.read_bytes()
        compressed.write_bytes(b"gzip invalido")
        self.assertFalse(ensure_database(target))
        self.assertEqual(target.read_bytes(), original_bytes)

    def test_gzip_corrompido_nao_cria_base_parcial(self):
        target = Path(self.temporary.name) / "corrupted.sqlite3"
        with gzip.open(target.with_suffix(".sqlite3.gz"), "wb") as destination:
            destination.write(b"conteudo que nao e SQLite")
        with self.assertRaises(sqlite3.DatabaseError):
            ensure_database(target)
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.glob("corrupted.sqlite3-*.tmp")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
