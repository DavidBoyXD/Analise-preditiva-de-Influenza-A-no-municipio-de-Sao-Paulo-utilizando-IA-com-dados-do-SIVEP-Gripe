"""Utilitarios compartilhados do pipeline de ETL do TCC de Influenza A (SIVEP-Gripe).

Concentra a resolucao de caminhos e a configuracao de log usadas pelos scripts
``etl_coleta.py`` e ``etl_tratamento.py``. Os caminhos sao sempre resolvidos a
partir da raiz do repositorio, de modo que os scripts funcionem independentemente
do diretorio de trabalho atual (por exemplo, ao rodar via
``uv --directory backend run python ../scripts/etl_tratamento.py``).
"""

from __future__ import annotations

import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes de dominio (fonte de verdade do dataset real do SIVEP-Gripe)
# ---------------------------------------------------------------------------

#: Codigo IBGE (CO_MUN_RES) do municipio de Sao Paulo capital.
CODIGO_MUNICIPIO_SP: str = "355030"

#: Separador de campos do CSV consolidado.
CSV_SEP: str = ";"

#: Encoding do CSV consolidado (contem BOM UTF-8).
CSV_ENCODING: str = "utf-8-sig"

#: Nome do arquivo bruto preservado em data/raw/.
ARQUIVO_BRUTO: str = "sivep_gripe_consolidado_2009_2026.csv"

#: Colunas esperadas no CSV bruto (ordem original).
COLUNAS_ESPERADAS: tuple[str, ...] = (
    "CS_SEXO",
    "CS_RACA",
    "NU_IDADE",
    "SEM_PRI",
    "DT_SIN_PRI",
    "SG_UF",
    "CO_MUN_RES",
    "ID_MN_RESI",
    "CS_ZONA",
    "PCR_FLUASU",
    "FLUASU_OUT",
)

#: Numero de semanas epidemiologicas mais recentes reservadas (nao usadas no treino)
#: por conta do atraso de notificacao (regra do Manual Interno).
SEMANAS_RESERVADAS: int = 8


def raiz_repositorio() -> Path:
    """Retorna o caminho absoluto da raiz do repositorio.

    ``scripts/`` fica diretamente sob a raiz do repositorio, logo a raiz e o
    diretorio pai deste arquivo.
    """
    return Path(__file__).resolve().parent.parent


def caminho_dados_brutos() -> Path:
    """Caminho do CSV bruto preservado em ``data/raw/``."""
    return raiz_repositorio() / "data" / "raw" / ARQUIVO_BRUTO


def dir_processado() -> Path:
    """Diretorio ``data/processed/`` (criado se necessario)."""
    destino = raiz_repositorio() / "data" / "processed"
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def caminho_base_tratada() -> Path:
    """Caminho de saida da base tratada."""
    return dir_processado() / "base_tratada.csv"


def caminho_serie_semanal() -> Path:
    """Caminho de saida da serie temporal semanal."""
    return dir_processado() / "serie_temporal_semanal.csv"


def configurar_log(nome: str) -> logging.Logger:
    """Configura e retorna um logger padronizado para os scripts de ETL."""
    logger = logging.getLogger(nome)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formato)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
