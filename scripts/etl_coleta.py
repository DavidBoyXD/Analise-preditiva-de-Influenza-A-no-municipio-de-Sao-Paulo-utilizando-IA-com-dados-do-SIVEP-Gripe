"""Etapa de coleta do ETL (RF003) - leitura e inspecao da base bruta.

Le o CSV bruto do SIVEP-Gripe preservado em ``data/raw/`` (encoding utf-8-sig,
separador ';'), registra metadados de rastreabilidade (numero de linhas, colunas,
periodo coberto por DT_SIN_PRI) e emite logs. Esta etapa NAO altera o conteudo
bruto: apenas inspeciona e reporta.

Uso (a partir da raiz do repositorio):

    uv --directory backend run python ../scripts/etl_coleta.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl_utils import (  # noqa: E402
    COLUNAS_ESPERADAS,
    CSV_ENCODING,
    CSV_SEP,
    caminho_dados_brutos,
    configurar_log,
)

logger = configurar_log("etl_coleta")


def carregar_base_bruta() -> pd.DataFrame:
    """Le o CSV bruto preservado em ``data/raw/`` sem alterar o conteudo.

    Todas as colunas sao lidas como texto (``dtype=str``) para nao perder zeros
    a esquerda de codigos (por exemplo CO_MUN_RES) nem coagir campos vazios.
    """
    origem = caminho_dados_brutos()
    if not origem.exists():
        raise FileNotFoundError(
            f"CSV bruto nao encontrado em {origem}. "
            "Confirme que a base foi copiada para data/raw/ (ver dicionario_dados.md)."
        )

    logger.info("Lendo base bruta: %s", origem)
    df = pd.read_csv(
        origem,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
    )
    return df


def relatar_metadados(df: pd.DataFrame) -> dict:
    """Registra metadados de rastreabilidade da base bruta e os retorna."""
    n_linhas = len(df)
    colunas = list(df.columns)

    logger.info("Total de linhas (registros): %d", n_linhas)
    logger.info("Total de colunas: %d -> %s", len(colunas), colunas)

    if tuple(colunas) != COLUNAS_ESPERADAS:
        logger.warning(
            "Colunas divergem do esperado. Esperado=%s Obtido=%s",
            list(COLUNAS_ESPERADAS),
            colunas,
        )

    # Periodo coberto por DT_SIN_PRI (formato DD/MM/AAAA).
    datas = pd.to_datetime(df["DT_SIN_PRI"], format="%d/%m/%Y", errors="coerce")
    ano_min = int(datas.dt.year.min())
    ano_max = int(datas.dt.year.max())
    invalidas = int(datas.isna().sum())
    logger.info("Periodo de DT_SIN_PRI: %d a %d", ano_min, ano_max)
    if invalidas:
        logger.warning("Datas DT_SIN_PRI nao parseaveis: %d", invalidas)

    return {
        "n_linhas": n_linhas,
        "colunas": colunas,
        "ano_min": ano_min,
        "ano_max": ano_max,
        "datas_invalidas": invalidas,
    }


def main() -> None:
    """Executa a etapa de coleta: le a base bruta e reporta metadados."""
    df = carregar_base_bruta()
    metadados = relatar_metadados(df)
    logger.info("Coleta concluida. Metadados: %s", metadados)


if __name__ == "__main__":
    main()
