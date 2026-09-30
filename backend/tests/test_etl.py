"""Testes do modulo de ETL (FEAT-001).

Validam, sobre o CSV real do SIVEP-Gripe:
- contagem de 13.139 registros do municipio de Sao Paulo capital;
- que o ETL nao introduz duplicidades (base tratada preserva o total do filtro);
- geracao da serie temporal semanal continua (semanas sem casos = 0);
- a flag de exclusao das 8 semanas epidemiologicas mais recentes.

Os testes garantem que os scripts de ETL rodem e regeneram os artefatos, e depois
inspecionam os artefatos gerados. Rodar com:

    cd backend && uv run pytest tests/test_etl.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Torna os scripts de ETL (raiz do repositorio / scripts) importaveis.
RAIZ_REPO = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = RAIZ_REPO / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import etl_tratamento  # noqa: E402
from etl_utils import (  # noqa: E402
    CODIGO_MUNICIPIO_SP,
    SEMANAS_RESERVADAS,
    caminho_base_tratada,
    caminho_dados_brutos,
    caminho_serie_semanal,
)

N_ESPERADO_SP = 13_139


@pytest.fixture(scope="module", autouse=True)
def executar_etl() -> None:
    """Roda o ETL de tratamento uma vez, regenerando os artefatos processados."""
    assert (
        caminho_dados_brutos().exists()
    ), "CSV bruto ausente em data/raw/. Copie a base antes de rodar os testes."
    etl_tratamento.main()


@pytest.fixture(scope="module")
def base_tratada() -> pd.DataFrame:
    return pd.read_csv(caminho_base_tratada(), dtype=str, keep_default_na=False)


@pytest.fixture(scope="module")
def serie_semanal() -> pd.DataFrame:
    return pd.read_csv(caminho_serie_semanal())


def test_contagem_municipio_sp(base_tratada: pd.DataFrame) -> None:
    """A base tratada contem exatamente os 13.139 registros de SP capital."""
    assert len(base_tratada) == N_ESPERADO_SP
    assert (base_tratada["CO_MUN_RES"] == CODIGO_MUNICIPIO_SP).all()


def test_etl_nao_introduz_duplicidades(base_tratada: pd.DataFrame) -> None:
    """O ETL preserva o total do filtro, sem inflar por duplicacao propria.

    Recontamos o filtro diretamente do bruto e comparamos com a base tratada:
    o processamento nao deve criar linhas alem das filtradas.
    """
    bruto = pd.read_csv(
        caminho_dados_brutos(),
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )
    n_filtro = int((bruto["CO_MUN_RES"].str.strip() == CODIGO_MUNICIPIO_SP).sum())
    assert n_filtro == N_ESPERADO_SP
    assert len(base_tratada) == n_filtro


def test_caso_proxy_derivado_de_pcr_fluasu(base_tratada: pd.DataFrame) -> None:
    """CASO_PROXY_INFLUENZA_A e 1 sse e somente se PCR_FLUASU esta preenchido."""
    pcr_preenchido = base_tratada["PCR_FLUASU"].str.strip() != ""
    proxy = base_tratada["CASO_PROXY_INFLUENZA_A"] == "1"
    assert (pcr_preenchido == proxy).all()
    # 7.407 casos-proxy no municipio de Sao Paulo (13.139 - 5.732 vazios).
    assert int(proxy.sum()) == 7_407


def test_serie_semanal_continua(serie_semanal: pd.DataFrame) -> None:
    """A serie e continua: cada ano presente tem as semanas 1..52 sem lacunas."""
    assert (serie_semanal["CASOS_PROXY"] >= 0).all()
    assert not serie_semanal["CASOS_PROXY"].isna().any()

    for ano, grupo in serie_semanal.groupby("ANO"):
        semanas = sorted(grupo["SEMANA_EPI"].tolist())
        assert semanas == list(range(1, 53)), f"Ano {ano} com semanas descontinuas"


def test_flag_reserva_oito_semanas_recentes(serie_semanal: pd.DataFrame) -> None:
    """As 8 semanas mais recentes estao marcadas como reservadas (fora do treino)."""
    reservadas = serie_semanal["RESERVADA_ATRASO_NOTIFICACAO"].sum()
    assert int(reservadas) == SEMANAS_RESERVADAS

    ordenada = serie_semanal.sort_values(["ANO", "SEMANA_EPI"]).reset_index(drop=True)
    ultimas = ordenada.tail(SEMANAS_RESERVADAS)
    assert bool(ultimas["RESERVADA_ATRASO_NOTIFICACAO"].all())
    assert not bool(ultimas["USAR_NO_TREINO"].any())

    # As demais semanas nao sao reservadas.
    restantes = ordenada.head(len(ordenada) - SEMANAS_RESERVADAS)
    assert not bool(restantes["RESERVADA_ATRASO_NOTIFICACAO"].any())
    assert bool(restantes["USAR_NO_TREINO"].all())
