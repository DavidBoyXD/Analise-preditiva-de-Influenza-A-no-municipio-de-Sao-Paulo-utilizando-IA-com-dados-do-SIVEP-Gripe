"""Schemas de dados epidemiologicos, series, previsoes, metricas e unidades."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PontoSerie(BaseModel):
    """Ponto semanal da serie temporal municipal de casos-proxy de Influenza A."""

    ano: int = Field(description="Ano epidemiologico (ex.: 2024).")
    semana: int = Field(description="Numero da semana epidemiologica (1 a 53).")
    casos_proxy: int = Field(description="Casos-proxy de Influenza A na semana (>= 0).")
    reservada_atraso_notificacao: bool = Field(
        description="TRUE para as 8 semanas mais recentes reservadas por atraso de notificacao."
    )
    usar_no_treino: bool = Field(description="FALSE para semanas reservadas; TRUE caso contrario.")


class StatusResposta(BaseModel):
    """Payload do healthcheck da API."""

    status: str = Field(description="Situacao geral da API (ex.: 'ok').")
    aplicacao: str = Field(description="Nome da aplicacao.")
    versao: str = Field(description="Versao da API.")
    banco_conectado: bool = Field(description="Indica se o banco respondeu a um SELECT 1.")
    modelo_carregado: bool = Field(
        description="Indica se ha um modelo preditivo carregado em memoria."
    )


class PrevisaoSemana(BaseModel):
    """Estimativa de casos-proxy para uma semana futura."""

    horizonte: int = Field(description="Posicao no horizonte de previsao (1 a N).")
    ano: int = Field(description="Ano epidemiologico estimado.")
    semana: int = Field(description="Semana epidemiologica estimada.")
    casos_previstos: float = Field(description="Estimativa de casos-proxy (>= 0).")


class PrevisaoResposta(BaseModel):
    """Conjunto de previsoes e a origem do modelo utilizado."""

    origem_modelo: str = Field(description="Origem da previsao: 'modelo_treinado' ou 'baseline'.")
    nome_modelo: str | None = Field(
        default=None, description="Nome/versao do modelo ativo, quando disponivel."
    )
    horizonte_semanas: int = Field(description="Quantidade de semanas previstas.")
    previsoes: list[PrevisaoSemana] = Field(description="Lista de previsoes semanais.")


class MetricaResposta(BaseModel):
    """Metricas de avaliacao do modelo ativo lidas do banco."""

    nome_modelo: str = Field(description="Nome do modelo avaliado.")
    versao: str = Field(description="Versao do modelo avaliado.")
    algoritmo: str = Field(description="Algoritmo/tecnica do modelo.")
    mae: float | None = Field(default=None, description="Erro Medio Absoluto.")
    rmse: float | None = Field(default=None, description="Raiz do Erro Quadratico Medio.")
    mape: float | None = Field(default=None, description="Erro Percentual Absoluto Medio (%).")
    acerto_direcional: float | None = Field(
        default=None, description="Proporcao de acerto direcional (0 a 1)."
    )
    teste_significancia: str | None = Field(
        default=None, description="Teste de significancia aplicado (ex.: Diebold-Mariano)."
    )
    p_valor: float | None = Field(default=None, description="p-valor do teste (0 a 1).")
    significativo: bool | None = Field(
        default=None, description="Se a diferenca frente ao comparador foi significativa."
    )


class UnidadeNotificacaoResposta(BaseModel):
    """Unidade de notificacao. A fonte atual pode nao popular NM_UN_INTE."""

    id_unidade_notificacao: int = Field(description="Identificador da unidade.")
    nm_un_inte: str | None = Field(
        default=None,
        description="Nome da unidade (NM_UN_INTE). NULO quando a fonte nao popula o campo.",
    )
    co_mun_res: str = Field(description="Codigo IBGE do municipio (ex.: 355030).")
    nome_municipio: str = Field(description="Nome do municipio.")
    sg_uf: str = Field(description="Sigla da UF.")
    fonte_populada: bool = Field(
        description="Indica se NM_UN_INTE foi efetivamente populado pela fonte."
    )
