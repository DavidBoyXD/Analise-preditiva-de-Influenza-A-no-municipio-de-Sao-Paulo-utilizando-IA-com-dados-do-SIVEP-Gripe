"""Etapa de tratamento do ETL (RF003) - base tratada e serie temporal semanal.

A partir da base bruta preservada em ``data/raw/``, este script:

(a) filtra o municipio de Sao Paulo capital (CO_MUN_RES == "355030");
(b) parseia DT_SIN_PRI (DD/MM/AAAA) e deriva o ano; usa SEM_PRI (semana
    epidemiologica oficial da fonte) como semana;
(c) aplica a REGRA DE PROXY de confirmacao de Influenza A: registros com
    PCR_FLUASU preenchido (nao vazio) sao contados como caso-proxy. Os campos
    de confirmacao laboratorial da Tabela 1 do TC2 (CLASSI_FIN, PCR_RESUL,
    POS_PCRFLU, TP_FLU_PCR, POS_AN_FLU, TP_FLU_AN) NAO existem no CSV;
(d) quantifica ausentes e duplicidades;
(e) trata inconsistencias sem excluir dados sem justificativa (tudo em log);
(f) salva data/processed/base_tratada.csv;
(g) agrega casos-proxy por (ano, semana epidemiologica), produz serie continua
    (semanas sem casos = 0) e marca as 8 semanas mais recentes como reservadas
    (nao usar no treino) por conta do atraso de notificacao.

Uso (a partir da raiz do repositorio):

    uv --directory backend run python ../scripts/etl_tratamento.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl_coleta import carregar_base_bruta  # noqa: E402
from etl_utils import (  # noqa: E402
    CODIGO_MUNICIPIO_SP,
    SEMANAS_RESERVADAS,
    caminho_base_tratada,
    caminho_serie_semanal,
    configurar_log,
)

logger = configurar_log("etl_tratamento")

#: Campos de confirmacao laboratorial esperados pelo TC2 (Tabela 1) e AUSENTES no CSV.
CAMPOS_CONFIRMACAO_AUSENTES: tuple[str, ...] = (
    "CLASSI_FIN",
    "PCR_RESUL",
    "POS_PCRFLU",
    "TP_FLU_PCR",
    "POS_AN_FLU",
    "TP_FLU_AN",
)


def filtrar_municipio_sp(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra os registros residentes do municipio de Sao Paulo capital."""
    sp = df[df["CO_MUN_RES"].str.strip() == CODIGO_MUNICIPIO_SP].copy()
    logger.info(
        "Filtro CO_MUN_RES == %s (Sao Paulo capital): %d registros",
        CODIGO_MUNICIPIO_SP,
        len(sp),
    )
    return sp


def derivar_tempo(sp: pd.DataFrame) -> pd.DataFrame:
    """Parseia DT_SIN_PRI (DD/MM/AAAA) e deriva ano e semana epidemiologica.

    A semana usa SEM_PRI (semana epidemiologica oficial informada pela fonte).
    O ano e derivado de DT_SIN_PRI. Registros com data ou semana invalidas sao
    apenas sinalizados em log; nao sao excluidos sem justificativa.
    """
    sp = sp.copy()
    sp["DT_SIN_PRI_PARSED"] = pd.to_datetime(
        sp["DT_SIN_PRI"], format="%d/%m/%Y", errors="coerce"
    )
    datas_invalidas = int(sp["DT_SIN_PRI_PARSED"].isna().sum())
    if datas_invalidas:
        logger.warning("Registros com DT_SIN_PRI invalida: %d", datas_invalidas)

    sp["ANO"] = sp["DT_SIN_PRI_PARSED"].dt.year.astype("Int64")
    sp["SEMANA_EPI"] = pd.to_numeric(sp["SEM_PRI"], errors="coerce").astype("Int64")

    semanas_invalidas = int(sp["SEMANA_EPI"].isna().sum())
    if semanas_invalidas:
        logger.warning("Registros com SEM_PRI invalida: %d", semanas_invalidas)

    fora_faixa = int(((sp["SEMANA_EPI"] < 1) | (sp["SEMANA_EPI"] > 53)).sum())
    if fora_faixa:
        logger.warning("Registros com SEM_PRI fora da faixa 1-53: %d", fora_faixa)

    return sp


def aplicar_proxy_influenza(sp: pd.DataFrame) -> pd.DataFrame:
    """Aplica a regra de proxy: PCR_FLUASU preenchido => caso-proxy de Influenza A.

    Documenta a distribuicao de categorias de PCR_FLUASU e alerta que os campos
    de confirmacao laboratorial da Tabela 1 do TC2 nao existem neste CSV.
    """
    sp = sp.copy()
    sp["PCR_FLUASU"] = sp["PCR_FLUASU"].fillna("").str.strip()
    sp["CASO_PROXY_INFLUENZA_A"] = (sp["PCR_FLUASU"] != "").astype(int)

    ausentes = [c for c in CAMPOS_CONFIRMACAO_AUSENTES if c not in sp.columns]
    if ausentes:
        logger.warning(
            "Campos de confirmacao laboratorial do TC2 AUSENTES no CSV: %s. "
            "Aplicando REGRA DE PROXY sobre PCR_FLUASU (ver relatorio_qualidade_dados.md).",
            ausentes,
        )

    distribuicao = sp["PCR_FLUASU"].replace("", "<vazio>").value_counts().to_dict()
    logger.info("Distribuicao PCR_FLUASU (SP capital): %s", distribuicao)
    logger.info(
        "Casos-proxy de Influenza A (PCR_FLUASU preenchido): %d de %d",
        int(sp["CASO_PROXY_INFLUENZA_A"].sum()),
        len(sp),
    )
    return sp


def quantificar_qualidade(sp: pd.DataFrame) -> None:
    """Quantifica valores ausentes por coluna e duplicidades (apenas log)."""
    ausentes = {
        col: int((sp[col].fillna("").astype(str).str.strip() == "").sum())
        for col in sp.columns
        if not col.endswith("_PARSED")
    }
    logger.info("Valores ausentes por coluna: %s", ausentes)

    colunas_originais = [
        c
        for c in sp.columns
        if c not in {"DT_SIN_PRI_PARSED", "ANO", "SEMANA_EPI", "CASO_PROXY_INFLUENZA_A"}
    ]
    duplicadas = int(sp.duplicated(subset=colunas_originais).sum())
    logger.info(
        "Linhas identicas (duplicidade exata considerando colunas originais): %d",
        duplicadas,
    )


def salvar_base_tratada(sp: pd.DataFrame) -> pd.DataFrame:
    """Ordena, seleciona colunas e salva a base tratada em data/processed/."""
    colunas_saida = [
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
        "ANO",
        "SEMANA_EPI",
        "CASO_PROXY_INFLUENZA_A",
    ]
    tratada = sp[colunas_saida].copy()
    destino = caminho_base_tratada()
    tratada.to_csv(destino, index=False, encoding="utf-8")
    logger.info("Base tratada salva em %s (%d linhas)", destino, len(tratada))
    return tratada


def gerar_serie_semanal(tratada: pd.DataFrame) -> pd.DataFrame:
    """Gera a serie temporal semanal continua de casos-proxy do municipio de SP.

    Agrega os casos-proxy por (ANO, SEMANA_EPI) e preenche com zero as semanas
    sem casos, produzindo uma serie continua. A continuidade e construida apenas
    sobre os anos efetivamente presentes na fonte (2009-2019 e 2022-2026); os
    anos 2020-2021 nao constam no CSV e NAO sao preenchidos com zeros artificiais
    (ver relatorio_qualidade_dados.md). As 8 semanas epidemiologicas mais recentes
    sao marcadas como reservadas (excluidas do treino) por atraso de notificacao.
    """
    validos = tratada.dropna(subset=["ANO", "SEMANA_EPI"]).copy()
    validos = validos[(validos["SEMANA_EPI"] >= 1) & (validos["SEMANA_EPI"] <= 53)]
    validos["ANO"] = validos["ANO"].astype(int)
    validos["SEMANA_EPI"] = validos["SEMANA_EPI"].astype(int)

    agregado = (
        validos.groupby(["ANO", "SEMANA_EPI"])["CASO_PROXY_INFLUENZA_A"]
        .sum()
        .rename("CASOS_PROXY")
        .reset_index()
    )

    # Grade continua de (ano, semana 1..52) apenas para os anos presentes na fonte.
    anos_presentes = sorted(validos["ANO"].unique())
    grade = pd.MultiIndex.from_product(
        [anos_presentes, range(1, 53)], names=["ANO", "SEMANA_EPI"]
    ).to_frame(index=False)

    serie = grade.merge(agregado, on=["ANO", "SEMANA_EPI"], how="left")
    serie["CASOS_PROXY"] = serie["CASOS_PROXY"].fillna(0).astype(int)
    serie = serie.sort_values(["ANO", "SEMANA_EPI"]).reset_index(drop=True)

    # Marca as SEMANAS_RESERVADAS mais recentes como reservadas (fora do treino).
    serie["RESERVADA_ATRASO_NOTIFICACAO"] = False
    idx_reservadas = serie.index[-SEMANAS_RESERVADAS:]
    serie.loc[idx_reservadas, "RESERVADA_ATRASO_NOTIFICACAO"] = True
    serie["USAR_NO_TREINO"] = ~serie["RESERVADA_ATRASO_NOTIFICACAO"]

    destino = caminho_serie_semanal()
    serie.to_csv(destino, index=False, encoding="utf-8")
    logger.info(
        "Serie semanal salva em %s (%d semanas; %d reservadas por atraso de notificacao)",
        destino,
        len(serie),
        int(serie["RESERVADA_ATRASO_NOTIFICACAO"].sum()),
    )
    return serie


def main() -> None:
    """Executa o tratamento completo e gera os artefatos processados."""
    df = carregar_base_bruta()
    sp = filtrar_municipio_sp(df)
    sp = derivar_tempo(sp)
    sp = aplicar_proxy_influenza(sp)
    quantificar_qualidade(sp)
    tratada = salvar_base_tratada(sp)
    gerar_serie_semanal(tratada)
    logger.info("Tratamento concluido com sucesso.")


if __name__ == "__main__":
    main()
