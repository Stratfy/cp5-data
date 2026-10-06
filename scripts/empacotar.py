"""Cria o pacote reproduzível do CP2 com uma lista explícita de arquivos."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "CP2_Pagamentos_ES_2024"
REQUIRED = (
    "README.md", "VALIDACAO.md",
    "app.py", "preparar_dados.py", "iniciar.bat", "requirements.txt",
    "static/index.html", "static/style.css", "static/app.js", "static/motion.js",
    "data/pagamentos_2024.sqlite3.gz", "data/resumo_analise.json",
    "data/auditoria_arquivos.csv", "data/ranking_unidades.csv",
    "data/evolucao_mensal.csv", "data/amostra_estatistica.csv",
    "docs/relatorio_pagamentos_es_2024.pdf",
    "docs/apresentacao_pagamentos_es_2024.pptx",
    "docs/apresentacao_pagamentos_es_2024.pdf",
    "docs/guia_apresentacao_pagamentos_es_2024.pdf",
    "scripts/empacotar.py",
)


def package(guide: Path | None = None, message: Path | None = None) -> Path:
    destination = ROOT / "outputs" / f"{PREFIX}{'_Grupo' if guide else ''}.zip"
    files = [ROOT / name for name in REQUIRED]
    files.extend(sorted((ROOT / "tests").glob("test_*.py")))
    missing = [str(path.relative_to(ROOT)) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("Arquivos necessários ausentes: " + ", ".join(missing))
    if not any(path.parent.name == "tests" for path in files):
        raise FileNotFoundError("Os testes da aplicação não foram encontrados.")

    # Use uma única leitura por arquivo para o conteúdo e seu manifesto coincidirem.
    content = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in sorted(files)}
    if message and not guide:
        raise ValueError("Informe também o guia ao incluir uma mensagem para o grupo.")
    for path, name in ((guide, "COMECE_AQUI.html"), (message, "PARA_ENVIAR_AO_GRUPO.txt")):
        if path:
            content[name] = path.read_bytes()
    manifest = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in content.items())
    content["MANIFESTO_SHA256.txt"] = manifest.encode("utf-8")
    destination.parent.mkdir(exist_ok=True)
    temporary = destination.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in content.items():
            archive.writestr(f"{PREFIX}/{name}", data,
                             compress_type=zipfile.ZIP_STORED if name.endswith(".gz") else zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError("Falha de integridade no ZIP gerado.")
        if len(archive.namelist()) != len(content):
            raise ValueError("A quantidade de arquivos do ZIP não corresponde ao pacote.")
        for name, data in content.items():
            if archive.read(f"{PREFIX}/{name}") != data:
                raise ValueError(f"Conteúdo divergente no ZIP: {name}")
    temporary.replace(destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    print(f"Pacote: {destination}")
    print(f"Arquivos: {len(content)} | Tamanho: {destination.stat().st_size / 1024 / 1024:.2f} MiB")
    print(f"SHA-256: {digest}")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guia-grupo", type=Path, help="HTML de estudo a incluir somente no pacote do grupo.")
    parser.add_argument("--mensagem-grupo", type=Path, help="Texto de encaminhamento a incluir junto ao guia.")
    args = parser.parse_args()
    package(args.guia_grupo, args.mensagem_grupo)
