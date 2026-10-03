"""Painel local de pagamentos públicos. Requer apenas Python 3.10+.

Todos os valores monetários são mantidos em centavos inteiros. A base é aberta
em modo somente leitura; nenhum endpoint altera os registros de origem.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
import gzip
import io
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "data" / "pagamentos_2024.sqlite3"
PAGE_SIZE = 20
MONTH_NAMES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


class InputError(ValueError):
    """Parâmetro de consulta inválido."""


def parse_filters(query: dict[str, list[str]], extra: set[str] | None = None) -> dict:
    allowed = {"mes", "unidade"} | (extra or set())
    if set(query) - allowed:
        raise InputError("A consulta contém um filtro desconhecido.")
    if any(len(values) != 1 for values in query.values()):
        raise InputError("Informe cada filtro apenas uma vez.")
    month = query.get("mes", [""])[0]
    if month and (len(month) > 2 or not month.isascii() or not month.isdigit() or not 1 <= int(month) <= 12):
        raise InputError("O mês precisa ser um número de 1 a 12.")
    unit_raw = query.get("unidade", [""])[0]
    unit = None
    if unit_raw:
        if len(unit_raw) > 1000:
            raise InputError("O filtro de unidade é muito longo.")
        try:
            unit = json.loads(unit_raw)
        except (ValueError, TypeError):
            raise InputError("Escolha uma unidade disponível na lista.") from None
        if not isinstance(unit, list) or len(unit) != 2 or not all(isinstance(item, str) for item in unit):
            raise InputError("Escolha uma unidade disponível na lista.")
    return {"mes": int(month) if month else None, "unidade": unit}


def csv_safe(value):
    """Impede que identificadores textuais sejam interpretados como fórmulas."""
    if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))):
        return "'" + value
    return value


def cents_decimal(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100},{cents % 100:02d}"


def ensure_database(database: Path) -> bool:
    """Recupera a cópia gzip ao lado da base, sem sobrescrever uma base existente.

    A extração ocorre em um arquivo temporário na mesma pasta. Sua integridade
    SQLite é verificada antes de publicar o arquivo de destino.
    """
    database = Path(database)
    if database.exists():
        return False
    compressed = database.with_suffix(database.suffix + ".gz")
    if not compressed.is_file():
        return False
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix=database.name + "-", suffix=".tmp",
                                         dir=database.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with gzip.open(compressed, "rb") as source:
                shutil.copyfileobj(source, temporary, length=1024 * 1024)
        connection = sqlite3.connect(temporary_path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            connection.execute("SELECT id, ano, mes, valor_centavos FROM pagamentos LIMIT 1")
            if integrity != "ok":
                raise sqlite3.DatabaseError("A base compactada não passou na verificação de integridade.")
        finally:
            connection.close()
        try:
            if sys.platform == "win32":
                # No Windows, rename falha se o destino já existir.
                temporary_path.rename(database)
            else:
                # Link publica atomicamente sem sobrescrita também em POSIX.
                os.link(temporary_path, database)
        except FileExistsError:
            return False
        return True
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


class Repository:
    def __init__(self, database: Path):
        self.database = Path(database)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.database.resolve().as_uri() + "?mode=ro", uri=True, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def where(filters: dict):
        clauses, parameters = ["ano = ?"], [2024]
        if filters.get("mes") is not None:
            clauses.append("mes = ?")
            parameters.append(filters["mes"])
        if filters.get("unidade") is not None:
            clauses.extend(["COALESCE(codigo_unidade_gestora, '') = ?", "COALESCE(unidade_gestora, '') = ?"])
            parameters.extend(filters["unidade"])
        return " AND ".join(clauses), parameters

    def options(self):
        with self.connect() as connection:
            rows = connection.execute("""SELECT DISTINCT COALESCE(codigo_unidade_gestora, '') AS codigo,
                COALESCE(unidade_gestora, '') AS nome FROM pagamentos WHERE ano = 2024
                ORDER BY nome COLLATE NOCASE, codigo""").fetchall()
        return {"ano": 2024, "meses": [{"valor": i + 1, "nome": name} for i, name in enumerate(MONTH_NAMES)],
                "unidades": [{"chave": json.dumps([row["codigo"], row["nome"]], ensure_ascii=False, separators=(",", ":")),
                              "codigo": row["codigo"], "nome": row["nome"] or "Unidade não informada"} for row in rows]}

    def summary(self, filters):
        where, params = self.where(filters)
        with self.connect() as connection:
            row = connection.execute(f"""SELECT COUNT(*) AS registros,
                COALESCE(SUM(valor_centavos), 0) AS total_centavos,
                COALESCE(SUM(CASE WHEN valor_centavos < 0 THEN 1 ELSE 0 END), 0) AS ajustes,
                COALESCE(SUM(CASE WHEN valor_centavos < 0 THEN valor_centavos ELSE 0 END), 0) AS ajustes_centavos,
                COALESCE(SUM(CASE WHEN valor_centavos = 0 THEN 1 ELSE 0 END), 0) AS zeros,
                MIN(data_pagamento) AS primeira_data, MAX(data_pagamento) AS ultima_data
                FROM pagamentos WHERE {where}""", params).fetchone()
            units = connection.execute(f"""SELECT COUNT(*) FROM (SELECT codigo_unidade_gestora, unidade_gestora
                FROM pagamentos WHERE {where} GROUP BY codigo_unidade_gestora, unidade_gestora)""", params).fetchone()[0]
        return dict(row) | {"unidades": units, "ano": 2024}

    def ranking(self, filters, limit=10):
        where, params = self.where(filters)
        sql = f"""SELECT COALESCE(codigo_unidade_gestora, '') AS codigo,
            COALESCE(unidade_gestora, '') AS nome, SUM(valor_centavos) AS total_centavos,
            COUNT(*) AS registros FROM pagamentos WHERE {where}
            GROUP BY codigo_unidade_gestora, unidade_gestora
            ORDER BY total_centavos DESC, nome, codigo"""
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def monthly(self, filters):
        where, params = self.where(filters)
        with self.connect() as connection:
            rows = connection.execute(f"""SELECT mes, SUM(valor_centavos) AS total_centavos,
                COUNT(*) AS registros FROM pagamentos WHERE {where} GROUP BY mes ORDER BY mes""", params).fetchall()
        available = {row["mes"]: dict(row) for row in rows}
        months = [filters["mes"]] if filters.get("mes") else range(1, 13)
        return [available.get(month, {"mes": month, "total_centavos": 0, "registros": 0}) | {"nome": MONTH_NAMES[month - 1]}
                for month in months]

    def records(self, filters, page=1):
        where, params = self.where(filters)
        with self.connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM pagamentos WHERE {where}", params).fetchone()[0]
            rows = connection.execute(f"""SELECT id, id_origem, data_pagamento, codigo_unidade_gestora,
                unidade_gestora, valor_centavos, tipo_documento, numero_documento, arquivo_origem, linha_origem
                FROM pagamentos WHERE {where} ORDER BY data_pagamento DESC, id DESC LIMIT ? OFFSET ?""",
                params + [PAGE_SIZE, (page - 1) * PAGE_SIZE]).fetchall()
        return {"linhas": [dict(row) for row in rows], "pagina": page, "tamanho": PAGE_SIZE,
                "total": total, "paginas": max(1, math.ceil(total / PAGE_SIZE))}

    def csv_rows(self, filters, kind):
        if kind == "mensal":
            yield ["Mes", "NomeMes", "ValorPagoLiquido_R$", "Registros"]
            for row in self.monthly(filters):
                yield [row["mes"], row["nome"], cents_decimal(row["total_centavos"]), row["registros"]]
        elif kind == "ranking":
            yield ["CodigoUnidadeGestora", "UnidadeGestora", "ValorPagoLiquido_R$", "Registros"]
            for row in self.ranking(filters, limit=None):
                yield [row["codigo"], row["nome"], cents_decimal(row["total_centavos"]), row["registros"]]
        elif kind == "detalhes":
            yield ["IdLocal", "IdOrigem", "DataRegistro", "CodigoUnidadeGestora", "UnidadeGestora",
                   "ValorPago_R$", "TipoDocumento", "NumeroDocumento", "ArquivoOrigem", "LinhaOrigem"]
            where, params = self.where(filters)
            with self.connect() as connection:
                cursor = connection.execute(f"""SELECT id, id_origem, data_pagamento, codigo_unidade_gestora,
                    unidade_gestora, valor_centavos, tipo_documento, numero_documento, arquivo_origem, linha_origem
                    FROM pagamentos WHERE {where} ORDER BY data_pagamento DESC, id DESC""", params)
                for row in cursor:
                    values = list(row)
                    values[5] = cents_decimal(values[5]) if values[5] is not None else ""
                    yield values


def make_handler(database=DEFAULT_DATABASE, static_dir=ROOT / "static"):
    repository = Repository(Path(database))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format_string, *args):
            # Evita imprimir filtros e identificadores no terminal.
            if args and isinstance(args[0], str) and args[0].startswith("GET /api/"):
                return
            super().log_message(format_string, *args)

        def json_response(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            static = {"/": "index.html", "/index.html": "index.html",
                      "/static/style.css": "style.css", "/static/app.js": "app.js"}
            if url.path in static:
                path = Path(static_dir) / static[url.path]
                try:
                    body = path.read_bytes()
                except OSError:
                    self.json_response({"erro": "Arquivo da aplicação não encontrado."}, 404)
                    return
                types = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}
                self.send_response(200)
                self.send_header("Content-Type", types[path.suffix] + "; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(body)
                return
            endpoints = {"/api/opcoes", "/api/resumo", "/api/ranking", "/api/mensal", "/api/registros", "/api/exportar"}
            if url.path not in endpoints:
                self.json_response({"erro": "Página ou consulta não encontrada."}, 404)
                return
            try:
                query = parse_qs(url.query, keep_blank_values=True)
                extra = {"pagina"} if url.path == "/api/registros" else {"tipo"} if url.path == "/api/exportar" else set()
                if url.path == "/api/opcoes" and query:
                    raise InputError("A lista de opções não recebe filtros.")
                filters = parse_filters(query, extra)
                if url.path == "/api/opcoes":
                    self.json_response(repository.options())
                elif url.path == "/api/resumo":
                    self.json_response(repository.summary(filters))
                elif url.path == "/api/ranking":
                    self.json_response({"linhas": repository.ranking(filters)})
                elif url.path == "/api/mensal":
                    self.json_response({"linhas": repository.monthly(filters)})
                elif url.path == "/api/registros":
                    raw_page = query.get("pagina", ["1"])[0]
                    if len(raw_page) > 7 or not raw_page.isascii() or not raw_page.isdigit() or not 1 <= int(raw_page) <= 1000000:
                        raise InputError("A página precisa ser um número inteiro positivo.")
                    self.json_response(repository.records(filters, int(raw_page)))
                else:
                    kind = query.get("tipo", ["mensal"])[0]
                    if kind not in {"mensal", "ranking", "detalhes"}:
                        raise InputError("Escolha a exportação mensal, ranking ou detalhes.")
                    # Testa a disponibilidade da base antes de enviar o cabeçalho.
                    repository.summary(filters)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", f'attachment; filename="pagamentos_2024_{kind}.csv"')
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(b"\xef\xbb\xbf")
                    buffer = io.StringIO(newline="")
                    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
                    for row in repository.csv_rows(filters, kind):
                        monetary_column = 5 if kind == "detalhes" else 2
                        writer.writerow([value if index == monetary_column else csv_safe(value)
                                         for index, value in enumerate(row)])
                        if buffer.tell() >= 65536:
                            self.wfile.write(buffer.getvalue().encode("utf-8"))
                            buffer.seek(0)
                            buffer.truncate(0)
                    if buffer.tell():
                        self.wfile.write(buffer.getvalue().encode("utf-8"))
            except InputError as error:
                self.json_response({"erro": str(error)}, 400)
            except sqlite3.Error:
                self.json_response({"erro": "A base de dados não está disponível. Confira o arquivo na pasta data e tente novamente."}, 503)
            except (BrokenPipeError, ConnectionResetError):
                # Cancelar uma exportação no navegador não interrompe o servidor.
                return

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Painel local de pagamentos do Espírito Santo em 2024")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        if ensure_database(args.database):
            print("Base compactada recuperada e integridade verificada.")
    except (OSError, EOFError, sqlite3.Error) as error:
        print(f"Não foi possível recuperar a base compactada: {error}")
        return 2
    if not args.database.is_file():
        print(f"Base não encontrada: {args.database}\nMantenha a pasta data junto de app.py.")
        return 2
    try:
        server = ThreadingHTTPServer((args.host, args.port), make_handler(args.database))
    except OSError as error:
        print(f"Não foi possível iniciar a aplicação: {error}\nSe a porta estiver ocupada, use --port 8766.")
        return 2
    url = f"http://{args.host}:{args.port}"
    print(f"Painel disponível em {url}\nPara encerrar, pressione Ctrl+C nesta janela.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAplicação encerrada.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
