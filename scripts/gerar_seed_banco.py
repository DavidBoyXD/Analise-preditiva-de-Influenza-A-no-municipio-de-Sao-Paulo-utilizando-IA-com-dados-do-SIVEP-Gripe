"""Gera o arquivo ``database/seed.sql`` a partir dos artefatos do ETL (FEAT-001).

Le ``data/processed/serie_temporal_semanal.csv`` e emite comandos DML
(INSERT) idempotentes para popular o banco relacional (RF003):

* ``fonte_dados`` .......... SIVEP-Gripe / SINAN (DATASUS);
* ``arquivo_dados`` ........ ficha de rastreabilidade do CSV consolidado;
* ``unidade_notificacao`` .. municipio de Sao Paulo (NM_UN_INTE ainda NAO
  populado pela fonte - fonte_populada = FALSE);
* ``semana_epidemiologica`` . uma linha por (ano, semana) presente na serie;
* ``serie_temporal`` ....... a serie semanal consolidada, com a flag de
  exclusao das 8 semanas mais recentes.

O SQL gerado nao contem credenciais e e valido tanto em PostgreSQL quanto em
SQLite (usa apenas INSERT com colunas explicitas e literais ANSI).

Uso (a partir da raiz do repositorio):
    uv --directory backend run python ../scripts/gerar_seed_banco.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from etl_utils import (
    ARQUIVO_BRUTO,
    CODIGO_MUNICIPIO_SP,
    caminho_serie_semanal,
    configurar_log,
    raiz_repositorio,
)

LOGGER = configurar_log("gerar_seed_banco")

# Identificadores fixos usados no seed (chaves substitutas deterministas).
ID_FONTE_SIVEP = 1
ID_ARQUIVO_BRUTO = 1
ID_ARQUIVO_TRATADO = 2
ID_UNIDADE_SP = 1


def caminho_seed() -> Path:
    """Caminho de saida do arquivo ``database/seed.sql``."""
    destino = raiz_repositorio() / "database"
    destino.mkdir(parents=True, exist_ok=True)
    return destino / "seed.sql"


def _sql_str(valor: str) -> str:
    """Escapa aspas simples para literal SQL."""
    return "'" + valor.replace("'", "''") + "'"


def _bool_sql(valor: str) -> str:
    """Converte o texto booleano do CSV ('True'/'False') em literal SQL."""
    return "TRUE" if str(valor).strip().lower() == "true" else "FALSE"


def ler_serie() -> list[dict[str, str]]:
    """Le a serie temporal semanal gerada pelo ETL."""
    caminho = caminho_serie_semanal()
    if not caminho.exists():
        raise FileNotFoundError(
            f"Serie temporal nao encontrada em {caminho}. "
            "Rode o ETL (etl_coleta.py + etl_tratamento.py) antes."
        )
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    LOGGER.info("Serie temporal lida: %d semanas.", len(linhas))
    return linhas


def gerar_sql(linhas: list[dict[str, str]]) -> str:
    """Monta o conteudo completo do seed.sql a partir da serie."""
    # Semanas distintas (ano, numero) preservando a ordem de ocorrencia.
    semanas: list[tuple[int, int]] = []
    vistos: set[tuple[int, int]] = set()
    for linha in linhas:
        chave = (int(linha["ANO"]), int(linha["SEMANA_EPI"]))
        if chave not in vistos:
            vistos.add(chave)
            semanas.append(chave)

    ano_ini = min(a for a, _ in semanas)
    ano_fim = max(a for a, _ in semanas)

    partes: list[str] = []
    partes.append(
        "-- =============================================================================\n"
        "-- seed.sql - Carga inicial (DML) do banco relacional (RF003).\n"
        "--\n"
        "-- GERADO AUTOMATICAMENTE por scripts/gerar_seed_banco.py a partir de\n"
        "-- data/processed/serie_temporal_semanal.csv (artefato do ETL - FEAT-001).\n"
        "-- NAO editar manualmente: regenere com\n"
        "--   uv --directory backend run python ../scripts/gerar_seed_banco.py\n"
        "--\n"
        "-- Nao contem credenciais. Valido em PostgreSQL 16 e SQLite.\n"
        "-- Aplicar apos schema.sql (e, opcionalmente, indexes.sql).\n"
        "-- =============================================================================\n"
    )

    # fonte_dados
    descricao_fonte = (
        "Sistema de Informacao de Vigilancia Epidemiologica da Gripe (SRAG). "
        "Dados publicos do Ministerio da Saude / DATASUS."
    )
    partes.append("\n-- Fonte publica dos dados epidemiologicos.")
    partes.append(
        "INSERT INTO fonte_dados (id_fonte_dados, nome_fonte, descricao, url_fonte) VALUES\n"
        f"    ({ID_FONTE_SIVEP}, {_sql_str('SIVEP-Gripe / SINAN - DATASUS')}, "
        f"{_sql_str(descricao_fonte)}, "
        f"{_sql_str('https://opendatasus.saude.gov.br/')});"
    )

    # arquivo_dados (bruto + tratado) - ficha de rastreabilidade do CSV.
    caminho_origem = (
        "Documentos_Para_Desenv_TCC/"
        "Dados consolidados e padronizados 2009 a 2019 e 2022 a 2026.csv"
    )
    partes.append(
        "\n-- Arquivos de dados (ficha de rastreabilidade do CSV consolidado)."
    )
    partes.append(
        "INSERT INTO arquivo_dados (id_arquivo_dados, id_fonte_dados, nome_arquivo, "
        "formato_arquivo, tipo_arquivo, ano_referencia_inicio, ano_referencia_fim, "
        "caminho_origem, caminho_armazenamento, quantidade_registros, status_arquivo) VALUES\n"
        f"    ({ID_ARQUIVO_BRUTO}, {ID_FONTE_SIVEP}, {_sql_str(ARQUIVO_BRUTO)}, "
        f"{_sql_str('CSV')}, {_sql_str('bruto')}, {ano_ini}, {ano_fim}, "
        f"{_sql_str(caminho_origem)}, {_sql_str('data/raw/' + ARQUIVO_BRUTO)}, "
        f"48775, {_sql_str('importado')}),\n"
        f"    ({ID_ARQUIVO_TRATADO}, {ID_FONTE_SIVEP}, {_sql_str('base_tratada.csv')}, "
        f"{_sql_str('CSV')}, {_sql_str('tratado')}, {ano_ini}, {ano_fim}, "
        f"{_sql_str('data/raw/' + ARQUIVO_BRUTO)}, {_sql_str('data/processed/base_tratada.csv')}, "
        f"13139, {_sql_str('processado')});"
    )

    # unidade_notificacao - municipio de SP; NM_UN_INTE NAO populado pela fonte.
    partes.append(
        "\n-- Unidade de notificacao (municipal). A fonte atual NAO popula NM_UN_INTE\n"
        "-- (nm_un_inte = NULL, fonte_populada = FALSE) - pendencia documentada."
    )
    partes.append(
        "INSERT INTO unidade_notificacao (id_unidade_notificacao, nm_un_inte, "
        "co_mun_res, nome_municipio, sg_uf, fonte_populada) VALUES\n"
        f"    ({ID_UNIDADE_SP}, NULL, {_sql_str(CODIGO_MUNICIPIO_SP)}, "
        f"{_sql_str('Sao Paulo')}, {_sql_str('SP')}, FALSE);"
    )

    # semana_epidemiologica
    partes.append("\n-- Dimensao temporal: semanas epidemiologicas presentes na serie.")
    valores_semana = []
    id_semana: dict[tuple[int, int], int] = {}
    for idx, (ano, sem) in enumerate(semanas, start=1):
        id_semana[(ano, sem)] = idx
        valores_semana.append(f"    ({idx}, {ano}, {sem})")
    partes.append(
        "INSERT INTO semana_epidemiologica "
        "(id_semana_epidemiologica, ano_epidemiologico, numero_semana) VALUES\n"
        + ",\n".join(valores_semana)
        + ";"
    )

    # serie_temporal
    partes.append("\n-- Serie temporal semanal consolidada consumida pelo modelo.")
    valores_serie = []
    for idx, linha in enumerate(linhas, start=1):
        chave = (int(linha["ANO"]), int(linha["SEMANA_EPI"]))
        valores_serie.append(
            f"    ({idx}, {id_semana[chave]}, {ID_UNIDADE_SP}, "
            f"{int(linha['CASOS_PROXY'])}, "
            f"{_bool_sql(linha['RESERVADA_ATRASO_NOTIFICACAO'])}, "
            f"{_bool_sql(linha['USAR_NO_TREINO'])})"
        )
    partes.append(
        "INSERT INTO serie_temporal (id_serie_temporal, id_semana_epidemiologica, "
        "id_unidade_notificacao, casos_proxy, reservada_atraso_notificacao, "
        "usar_no_treino) VALUES\n" + ",\n".join(valores_serie) + ";"
    )

    partes.append("")  # newline final
    return "\n".join(partes)


def main() -> None:
    linhas = ler_serie()
    sql = gerar_sql(linhas)
    destino = caminho_seed()
    destino.write_text(sql, encoding="utf-8")
    LOGGER.info("seed.sql gerado em %s (%d bytes).", destino, len(sql))


if __name__ == "__main__":
    main()
