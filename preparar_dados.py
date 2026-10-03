"""Prepara o recorte de despesas ES 2024; usa somente a biblioteca padrao.

Execucao: python preparar_dados.py --origem "C:\\Users\\bruno\\Downloads"
Os originais nao sao alterados. CPF, historico e dados bancarios nao sao exportados.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import random
import sqlite3
import statistics
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from zipfile import ZipFile


YEAR = 2024
NUMERIC_FIELDS = ("ValorEmpenho", "ValorLiquidado", "ValorPago", "ValorRap")
REQUIRED_FIELDS = ("Id", "Ano", "Data", "CodigoUnidadeGestora", "UnidadeGestora",
                   "ValorPago", "Documento")
MONTH_NAMES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
               "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")


def amount(raw: str, audit: dict) -> int | None:
    value = raw.strip()
    if not value:
        audit["ausentes"] += 1
        return None
    try:
        normalized = value.replace(".", "").replace(",", ".") if "," in value else value
        number = Decimal(normalized)
        if not number.is_finite():
            raise InvalidOperation
        cents = number * 100
        rounded = cents.to_integral_value(rounding=ROUND_HALF_UP)
        if rounded != cents:
            audit["valores_com_fracao_inferior_a_centavo"] += 1
        audit["validos"] += 1
        audit["zeros"] += int(number == 0)
        audit["negativos"] += int(number < 0)
        return int(rounded)
    except (InvalidOperation, ValueError, OverflowError):
        audit["invalidos"] += 1
        return None


def numeric_audit() -> dict:
    return dict(validos=0, ausentes=0, invalidos=0, zeros=0, negativos=0,
                valores_com_fracao_inferior_a_centavo=0)


def save_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--saida", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()
    files = [args.origem / f"despesas_es_{YEAR}_completo_parte_{i:02d}.zip"
             for i in range(1, 5)]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("Arquivos ausentes: " + ", ".join(missing))
    args.saida.mkdir(parents=True, exist_ok=True)
    database = args.saida / "pagamentos_2024.sqlite3"
    temporary_database = args.saida / "pagamentos_2024.sqlite3.tmp"
    if temporary_database.exists():
        temporary_database.unlink()
    connection = sqlite3.connect(temporary_database)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.executescript("""
        CREATE TABLE pagamentos (
            id INTEGER PRIMARY KEY,
            id_origem TEXT NOT NULL,
            ano INTEGER NOT NULL,
            data_pagamento TEXT,
            mes INTEGER CHECK (mes BETWEEN 1 AND 12),
            codigo_unidade_gestora TEXT NOT NULL,
            unidade_gestora TEXT NOT NULL,
            valor_centavos INTEGER,
            tipo_documento TEXT NOT NULL,
            numero_documento TEXT NOT NULL,
            arquivo_origem TEXT NOT NULL,
            linha_origem INTEGER NOT NULL
        );
        CREATE TABLE metadados (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
    """)
    insert = "INSERT INTO pagamentos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    audit = {
        "registros_totais_csv": 0, "registros_2024": 0, "linhas_vazias_ignoradas": 0,
        "registros_largura_invalida": 0, "registros_ano_invalido": 0,
        "registros_outros_anos": 0, "datas_validas": 0, "datas_ausentes": 0,
        "datas_invalidas": 0, "datas_fora_do_ano_2024": 0,
        "id_ausente": 0, "codigo_unidade_ausente": 0, "nome_unidade_ausente": 0,
        "documento_ausente": 0, "tipos_documento_nao_identificados": 0,
        "duplicatas_exatas_registros_adicionais": 0,
        "ids_repetidos_registros_adicionais": 0,
        "ids_repetidos_com_conteudo_diferente": 0,
        "numericos": {name: numeric_audit() for name in NUMERIC_FIELDS},
        "ausencias_por_coluna": {},
        "por_arquivo": [], "sobreposicao_entre_arquivos": [],
        "decisao_duplicatas": "Nenhuma linha deduplicada. Id repetido sozinho nao comprova duplicata; registros completos tambem foram comparados por hash temporario, sem exportar os campos pessoais.",
        "tratamento_ausencias": "Ano invalido ou largura diferente do cabecalho: excluido da base e contado. ValorPago ausente/invalido: NULL, nunca zero. Data ausente/invalida ou fora de 2024: mes NULL. Codigo/nome/documento ausente: string vazia.",
    }
    seen_hashes: dict[bytes, str] = {}
    seen_ids: dict[str, tuple[bytes, str]] = {}
    overlap: Counter = Counter()
    dates: list[str] = []
    header_reference = None
    row_id = 0
    for path in files:
        file_audit = dict(arquivo_zip=path.name, sha256_zip=digest_file(path),
                          tamanho_zip_bytes=path.stat().st_size, registros_totais=0,
                          registros_2024=0, linhas_vazias=0, largura_invalida=0,
                          ano_invalido=0, outros_anos=0, valor_pago_zeros=0,
                          valor_pago_negativos=0, valor_pago_ausente_ou_invalido=0,
                          duplicatas_exatas=0, ids_repetidos=0)
        file_dates = []
        with ZipFile(path) as archive:
            entries = [item for item in archive.infolist()
                       if not item.is_dir() and item.filename.lower().endswith(".csv")]
            if len(entries) != 1:
                raise ValueError(f"Esperado um CSV no ZIP: {path.name}")
            entry = entries[0]
            file_audit.update(arquivo_csv=entry.filename, tamanho_csv_bytes=entry.file_size)
            with archive.open(entry) as binary:
                reader = csv.reader(io.TextIOWrapper(binary, encoding="utf-8-sig", newline=""),
                                    delimiter=";")
                header = next(reader)
                if not all(name in header for name in REQUIRED_FIELDS + NUMERIC_FIELDS):
                    raise ValueError(f"Cabecalho incompleto em {entry.filename}")
                if header_reference is not None and header != header_reference:
                    raise ValueError("As partes possuem cabecalhos diferentes")
                header_reference = header
                if not audit["ausencias_por_coluna"]:
                    audit["ausencias_por_coluna"] = {name: 0 for name in header}
                file_audit["numero_colunas"] = len(header)
                indexes = {name: header.index(name) for name in header}
                batch = []
                while True:
                    start_line = reader.line_num + 1
                    try:
                        row = next(reader)
                    except StopIteration:
                        break
                    if not row:
                        audit["linhas_vazias_ignoradas"] += 1
                        file_audit["linhas_vazias"] += 1
                        continue
                    audit["registros_totais_csv"] += 1
                    file_audit["registros_totais"] += 1
                    if len(row) != len(header):
                        audit["registros_largura_invalida"] += 1
                        file_audit["largura_invalida"] += 1
                        continue
                    get = lambda name: row[indexes[name]].strip()
                    try:
                        year = int(get("Ano"))
                    except ValueError:
                        audit["registros_ano_invalido"] += 1
                        file_audit["ano_invalido"] += 1
                        continue
                    if year != YEAR:
                        audit["registros_outros_anos"] += 1
                        file_audit["outros_anos"] += 1
                        continue
                    row_id += 1
                    audit["registros_2024"] += 1
                    file_audit["registros_2024"] += 1
                    for name, value in zip(header, row):
                        audit["ausencias_por_coluna"][name] += int(not value.strip())
                    # Hash de todos os 71 campos originais: somente usado em memoria.
                    record_hash = hashlib.blake2b(json.dumps(row, ensure_ascii=False,
                                               separators=(",", ":")).encode("utf-8"),
                                               digest_size=16).digest()
                    if record_hash in seen_hashes:
                        audit["duplicatas_exatas_registros_adicionais"] += 1
                        file_audit["duplicatas_exatas"] += 1
                        prior_file = seen_hashes[record_hash]
                        if prior_file != entry.filename:
                            overlap[(prior_file, entry.filename, "registro_completo")] += 1
                    else:
                        seen_hashes[record_hash] = entry.filename
                    source_id = get("Id")
                    if not source_id:
                        audit["id_ausente"] += 1
                    elif source_id in seen_ids:
                        prior_hash, prior_file = seen_ids[source_id]
                        audit["ids_repetidos_registros_adicionais"] += 1
                        file_audit["ids_repetidos"] += 1
                        if prior_hash != record_hash:
                            audit["ids_repetidos_com_conteudo_diferente"] += 1
                        if prior_file != entry.filename:
                            overlap[(prior_file, entry.filename, "Id")] += 1
                    else:
                        seen_ids[source_id] = (record_hash, entry.filename)
                    raw_date = get("Data")
                    date_iso, month = None, None
                    if not raw_date:
                        audit["datas_ausentes"] += 1
                    else:
                        try:
                            date = datetime.strptime(raw_date, "%d/%m/%Y %H:%M:%S")
                            date_iso = date.date().isoformat()
                            dates.append(date_iso)
                            file_dates.append(date_iso)
                            audit["datas_validas"] += 1
                            if date.year == YEAR:
                                month = date.month
                            else:
                                audit["datas_fora_do_ano_2024"] += 1
                        except ValueError:
                            audit["datas_invalidas"] += 1
                    amounts = {name: amount(get(name), audit["numericos"][name])
                               for name in NUMERIC_FIELDS}
                    paid = amounts["ValorPago"]
                    file_audit["valor_pago_zeros"] += int(paid == 0)
                    file_audit["valor_pago_negativos"] += int(paid is not None and paid < 0)
                    file_audit["valor_pago_ausente_ou_invalido"] += int(paid is None)
                    code, unit, document = get("CodigoUnidadeGestora"), get("UnidadeGestora"), get("Documento")
                    audit["codigo_unidade_ausente"] += int(not code)
                    audit["nome_unidade_ausente"] += int(not unit)
                    audit["documento_ausente"] += int(not document)
                    document_match = re.match(r"^\d{4}([A-Za-z]+)\d+$", document)
                    document_type = document_match.group(1).upper() if document_match else ""
                    audit["tipos_documento_nao_identificados"] += int(bool(document) and not document_type)
                    batch.append((row_id, source_id, year, date_iso, month, code, unit, paid,
                                  document_type, document, entry.filename, start_line))
                    if len(batch) >= 10000:
                        connection.executemany(insert, batch)
                        batch.clear()
                if batch:
                    connection.executemany(insert, batch)
        file_audit.update(data_minima=min(file_dates) if file_dates else None,
                          data_maxima=max(file_dates) if file_dates else None)
        audit["por_arquivo"].append(file_audit)
        connection.commit()
        print(f"Lido {path.name}: {file_audit['registros_2024']:,} registros de 2024", flush=True)
    audit["sobreposicao_entre_arquivos"] = [
        dict(arquivo_anterior=a, arquivo_atual=b, criterio=criterion, registros_adicionais=n)
        for (a, b, criterion), n in sorted(overlap.items())]
    # Libera as estruturas de auditoria antes das agregacoes e do sorteio interno.
    seen_hashes.clear()
    seen_ids.clear()
    audit["cabecalhos_identicos"] = True
    audit["numero_colunas_fonte"] = len(header_reference)
    audit["alcance_auditoria_numericos"] = "Quatro campos monetarios e validade do Ano; codigos permanecem texto para preservar zeros iniciais. Ausencias de todos os 71 campos foram contadas, sem exportar seus conteudos."
    audit["encoding"] = "UTF-8 com ou sem BOM"
    audit["separador"] = ";"
    audit["conversao_monetaria"] = "Decimal, virgula decimal; centavos inteiros com ROUND_HALF_UP. Quantidade de valores subcentavo auditada."
    connection.executescript("""
        CREATE INDEX idx_pagamentos_mes_unidade ON pagamentos(mes, codigo_unidade_gestora, unidade_gestora);
        CREATE INDEX idx_pagamentos_unidade ON pagamentos(codigo_unidade_gestora, unidade_gestora);
        CREATE INDEX idx_pagamentos_id_origem ON pagamentos(id_origem);
    """)
    connection.row_factory = sqlite3.Row
    sum_row = connection.execute("""SELECT count(*) registros,
        coalesce(sum(valor_centavos), 0) total,
        coalesce(sum(CASE WHEN valor_centavos > 0 THEN valor_centavos ELSE 0 END), 0) positivos,
        coalesce(sum(CASE WHEN valor_centavos < 0 THEN valor_centavos ELSE 0 END), 0) negativos,
        sum(CASE WHEN valor_centavos <> 0 THEN 1 ELSE 0 END) nao_zero,
        coalesce(sum(CASE WHEN mes IS NULL THEN valor_centavos ELSE 0 END), 0) sem_mes
        FROM pagamentos""").fetchone()
    ranking = []
    for rank, row in enumerate(connection.execute("""SELECT codigo_unidade_gestora, unidade_gestora,
        count(*) registros, sum(CASE WHEN valor_centavos <> 0 THEN 1 ELSE 0 END) registros_com_valor_nao_zero,
        coalesce(sum(valor_centavos), 0) valor_pago_centavos FROM pagamentos
        GROUP BY codigo_unidade_gestora, unidade_gestora
        ORDER BY valor_pago_centavos DESC, codigo_unidade_gestora, unidade_gestora"""), 1):
        item = dict(posicao=rank, **dict(row))
        item.update(valor_pago_reais=item["valor_pago_centavos"] / 100,
                    participacao_percentual=item["valor_pago_centavos"] / sum_row["total"] * 100 if sum_row["total"] else None)
        ranking.append(item)
    monthly = []
    for row in connection.execute("""SELECT mes, count(*) registros,
        sum(CASE WHEN valor_centavos <> 0 THEN 1 ELSE 0 END) registros_com_valor_nao_zero,
        coalesce(sum(valor_centavos), 0) valor_pago_centavos FROM pagamentos
        WHERE mes IS NOT NULL GROUP BY mes ORDER BY mes"""):
        item = dict(row)
        item.update(nome_mes=MONTH_NAMES[item["mes"] - 1], ano_mes=f"{YEAR}-{item['mes']:02d}",
                    valor_pago_reais=item["valor_pago_centavos"] / 100)
        monthly.append(item)
    months = [item["mes"] for item in monthly]
    all_12_months = months == list(range(1, 13))
    monthly_values = [item["valor_pago_reais"] for item in monthly]
    descriptive = dict(n_meses=len(months), meses_observados=months, todos_12_meses_2024=all_12_months,
                       media_mensal_reais=statistics.mean(monthly_values) if monthly_values else None,
                       mediana_mensal_reais=statistics.median(monthly_values) if monthly_values else None,
                       desvio_padrao_amostral_mensal_reais=statistics.stdev(monthly_values) if len(months) > 1 else None,
                       minimo_mensal_reais=min(monthly_values) if monthly_values else None,
                       maximo_mensal_reais=max(monthly_values) if monthly_values else None)
    descriptive.update(variancia_amostral_mensal_reais_quadrados=statistics.variance(monthly_values) if len(months) > 1 else None,
                       desvio_padrao_populacional_mensal_reais=statistics.pstdev(monthly_values) if monthly_values else None)
    descriptive["natureza"] = "Estatisticas descritivas dos totais mensais observados; nao foi calculado IC mensal devido a possivel sazonalidade e dependencia temporal."
    eligible_ids = [row[0] for row in connection.execute(
        "SELECT id FROM pagamentos WHERE valor_centavos IS NOT NULL ORDER BY id")]
    population_n = len(eligible_ids)
    sample_n = min(10000, population_n)
    sample_ids = random.Random(2024).sample(eligible_ids, sample_n)
    sample_rows = []
    for start in range(0, sample_n, 500):
        block = sample_ids[start:start + 500]
        placeholders = ",".join("?" for _ in block)
        sample_rows.extend(dict(row) for row in connection.execute(f"""SELECT id,
            arquivo_origem, linha_origem, valor_centavos AS valor_pago_centavos,
            CASE WHEN valor_centavos > 0 THEN 1 ELSE 0 END AS pagamento_positivo
            FROM pagamentos WHERE id IN ({placeholders})""", block))
    sample_rows.sort(key=lambda item: item["id"])
    sample_k = sum(row["pagamento_positivo"] for row in sample_rows)
    population_k = connection.execute("SELECT count(*) FROM pagamentos WHERE valor_centavos > 0").fetchone()[0]
    sample_p = sample_k / sample_n if sample_n else None
    z = 1.96
    if sample_n:
        denominator = 1 + z * z / sample_n
        center = (sample_p + z * z / (2 * sample_n)) / denominator
        half_width = z * math.sqrt(sample_p * (1 - sample_p) / sample_n + z * z / (4 * sample_n * sample_n)) / denominator
        lower, upper = max(0.0, center - half_width), min(1.0, center + half_width)
    else:
        lower, upper = None, None
    sample_statistics = dict(
        N=population_n, n=sample_n, k=sample_k, positivos_na_base=population_k,
        p_amostral=sample_p, proporcao_exata_base=population_k / population_n if population_n else None,
        limite_inferior=lower, limite_superior=upper, z=z, nivel_confianca=0.95,
        seed=2024, metodo_sorteio="Amostra aleatoria simples sem reposicao por random.Random(2024).sample dos IDs ordenados com ValorPago valido.",
        metodo_intervalo="Wilson para proporcao, aproximacao binomial sem correcao de populacao finita; aproximacao conservadora em relacao a amostragem sem reposicao.",
        formula="(p + z^2/(2n) +/- z*sqrt(p*(1-p)/n + z^2/(4*n^2))) / (1 + z^2/n)",
        evento="ValorPago > 0 no registro; zeros e ajustes negativos nao sao pagamentos positivos.",
        populacao_alvo="Somente registros de 2024 com ValorPago valido nos quatro CSVs locais fornecidos pelo professor.",
        amostragem_original="Recorte fornecido pelo professor, sem amostragem probabilistica estadual documentada; nenhuma inferencia para todo o Espirito Santo.",
        amostragem_interna="Sorteio interno aleatorio a partir da base local, distinto da forma de selecao dos arquivos originais.",
        interpretacao="Exercicio de estimacao da proporcao de registros com ValorPago positivo dentro da base local. A proporcao exata tambem e conhecida; o IC demonstra a estimacao por amostra, nao estima total financeiro nem fraude.",
        fonte_metodo="https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm",
        arquivo_amostra="amostra_estatistica.csv")
    connection.execute("CREATE TABLE amostra_estatistica (id_pagamento INTEGER PRIMARY KEY REFERENCES pagamentos(id))")
    connection.executemany("INSERT INTO amostra_estatistica VALUES (?)", [(identifier,) for identifier in sample_ids])
    summary = dict(
        metadados=dict(projeto="grupo4 - Pagamentos ES 2024", turma="2ESPH-2026",
                       criado_em_utc=datetime.now(timezone.utc).isoformat(),
                       fonte="Quatro ZIPs de despesas de 2024 fornecidos pelo professor.",
                       banco="pagamentos_2024.sqlite3", tabela="pagamentos",
                       campo_data="Data do registro: referencia da realizacao da despesa no dicionario. data_pagamento e apenas nome tecnico; nao comprova data bancaria.",
                       fonte_dicionario="dicionario_despesas.pdf, versao 1.0, 13/07/2021, secao Despesa.",
                       portal_oficial_referencia="https://dados2.es.gov.br/dataset/portal-da-transparencia-despesas-execucao-orcamentaria-e-financeira/resource/b34ae52a-a739-412a-9bab-80f53ba72f4f?inner_span=True",
                       limite_cobertura="O portal oficial lista o recurso Despesas-2024.csv com 1,2 GiB; os quatro CSVs locais somam cerca de 480 MiB. Essa diferenca impede afirmar cobertura integral estadual com os arquivos fornecidos.",
                       registros="Cada linha representa um registro do arquivo fonte, nao necessariamente uma compra distinta ou um pagamento positivo.",
                       dados_pessoais="CPF/CNPJ/NIS, nomes de favorecidos, historico livre e dados bancarios nao exportados."),
        metrica=dict(campo="ValorPago", definicao="Soma liquida do ValorPago registrado no recorte de 2024, em centavos; inclui ajustes negativos.",
                     exclusoes="ValorEmpenho, ValorLiquidado e ValorRap nao entram na soma de pagamentos.",
                     agregacao_unidade="codigo_unidade_gestora + unidade_gestora, com espacos externos removidos.",
                     agregacao_tempo="Mes calendario do campo Data; registros sem mes valido ficam fora da serie e sao auditados."),
        cobertura=dict(ano=YEAR, meses_observados=months, todos_12_meses_2024=all_12_months,
                       data_minima=min(dates) if dates else None, data_maxima=max(dates) if dates else None,
                       quantidade_partes=4, unidades_gestoras=len(ranking),
                       alcance="Somente registros contidos nos quatro arquivos fornecidos. O nome completo dos arquivos nao comprova cobertura integral das despesas do Estado."),
        total_registros=sum_row["registros"], registros_com_valor_nao_zero=sum_row["nao_zero"],
        total_pago_centavos=sum_row["total"], total_pago_reais=sum_row["total"] / 100,
        soma_valores_positivos_centavos=sum_row["positivos"], soma_ajustes_negativos_centavos=sum_row["negativos"],
        soma_sem_mes_valido_centavos=sum_row["sem_mes"], auditoria=audit,
        estatisticas_mensais=descriptive, estatistica_amostral=sample_statistics,
        ranking_unidades=ranking, evolucao_mensal=monthly)
    if sum(item["valor_pago_centavos"] for item in ranking) != sum_row["total"]:
        raise AssertionError("Ranking nao reconcilia com total da base")
    if sum(item["valor_pago_centavos"] for item in monthly) + sum_row["sem_mes"] != sum_row["total"]:
        raise AssertionError("Serie mensal nao reconcilia com total da base")
    if row_id != connection.execute("SELECT count(*) FROM pagamentos").fetchone()[0]:
        raise AssertionError("Contagem da base diferente dos registros lidos")
    summary["verificacao"] = dict(contagem_base_reconciliada=True, ranking_reconciliado=True,
                                   meses_reconciliados=True, integridade_sqlite=connection.execute("PRAGMA integrity_check").fetchone()[0])
    if summary["verificacao"]["integridade_sqlite"] != "ok":
        raise AssertionError("Falha na verificacao do SQLite")
    connection.executemany("INSERT INTO metadados VALUES (?, ?)",
                           [(key, json.dumps(summary[key], ensure_ascii=False))
                            for key in ("metadados", "metrica", "cobertura", "total_pago_centavos", "total_registros", "estatistica_amostral")])
    connection.commit()
    connection.close()
    temporary_database.replace(database)
    (args.saida / "resumo_analise.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    save_csv(args.saida / "ranking_unidades.csv", ranking)
    save_csv(args.saida / "evolucao_mensal.csv", monthly)
    save_csv(args.saida / "auditoria_arquivos.csv", audit["por_arquivo"])
    save_csv(args.saida / "amostra_estatistica.csv", sample_rows)
    print(json.dumps({key: summary[key] for key in ("total_registros", "total_pago_centavos", "cobertura", "estatisticas_mensais", "estatistica_amostral", "verificacao")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
