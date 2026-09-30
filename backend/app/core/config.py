"""Configuracoes da aplicacao lidas de variaveis de ambiente.

Usa pydantic-settings para carregar as configuracoes a partir de variaveis de
ambiente (e, opcionalmente, de um arquivo .env na raiz do repositorio). Nenhuma
credencial fica embutida no codigo: a string de conexao vem sempre de
`DATABASE_URL`. Um valor padrao SQLite e usado apenas para desenvolvimento e
testes locais, nunca com segredos.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parametros de configuracao da API.

    Atributos:
        app_nome: Nome exibido na documentacao OpenAPI/Swagger.
        app_versao: Versao da API.
        database_url: String de conexao SQLAlchemy. Em producao aponta para o
            PostgreSQL (ex.: postgresql+psycopg2://usuario:senha@host:5432/db);
            nos testes e no desenvolvimento local pode apontar para um SQLite.
        horizonte_previsao_semanas: Horizonte padrao de previsao (6 semanas).
        caminho_modelos: Diretorio onde os arquivos .joblib do modelo sao
            procurados na inicializacao do servico de previsao.
        co_mun_res_padrao: Codigo IBGE do municipio de Sao Paulo (355030).
        cors_origens: Lista de origens permitidas para CORS.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_nome: str = "API de Analise Preditiva de Influenza A - Municipio de Sao Paulo"
    app_versao: str = "0.1.0"

    # Padrao SQLite local (sem credenciais). Em producao, defina DATABASE_URL
    # apontando para o PostgreSQL via variavel de ambiente.
    database_url: str = "sqlite:///./influenza_dev.db"

    horizonte_previsao_semanas: int = 6
    caminho_modelos: str = "../models"
    co_mun_res_padrao: str = "355030"

    cors_origens: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Retorna a instancia unica (cacheada) das configuracoes da aplicacao."""
    return Settings()
