"""Modelos ORM SQLAlchemy que espelham as tabelas definidas em database/schema.sql.

Os nomes de tabelas e colunas seguem exatamente o schema relacional entregue em
FEAT-002 (padrao do Manual de Documentacao de Bancos de Dados: PK id_<entidade>,
FK id_<entidade_referenciada>). Os tipos usados sao ANSI e portaveis, garantindo
compatibilidade tanto com PostgreSQL (producao) quanto com SQLite (testes).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class FonteDados(Base):
    """Origem publica dos dados epidemiologicos (SIVEP-Gripe / SINAN - DATASUS)."""

    __tablename__ = "fonte_dados"

    id_fonte_dados: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_fonte: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    url_fonte: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_inclusao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    arquivos: Mapped[list["ArquivoDados"]] = relationship(back_populates="fonte")


class ArquivoDados(Base):
    """Arquivos coletados/tratados/backup - rastreabilidade da origem dos dados."""

    __tablename__ = "arquivo_dados"

    id_arquivo_dados: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_fonte_dados: Mapped[int] = mapped_column(
        Integer, ForeignKey("fonte_dados.id_fonte_dados"), nullable=False
    )
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    formato_arquivo: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_arquivo: Mapped[str] = mapped_column(String(30), nullable=False)
    ano_referencia_inicio: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ano_referencia_fim: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    caminho_origem: Mapped[str | None] = mapped_column(Text, nullable=True)
    caminho_armazenamento: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantidade_registros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_importacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    status_arquivo: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="importado"
    )

    fonte: Mapped["FonteDados"] = relationship(back_populates="arquivos")


class UnidadeNotificacao(Base):
    """Unidade/local de notificacao (NM_UN_INTE). A fonte atual NAO popula esse campo."""

    __tablename__ = "unidade_notificacao"

    id_unidade_notificacao: Mapped[int] = mapped_column(Integer, primary_key=True)
    nm_un_inte: Mapped[str | None] = mapped_column(String(150), nullable=True)
    co_mun_res: Mapped[str] = mapped_column(String(7), nullable=False)
    nome_municipio: Mapped[str] = mapped_column(String(120), nullable=False)
    sg_uf: Mapped[str] = mapped_column(String(2), nullable=False)
    fonte_populada: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")


class SemanaEpidemiologica(Base):
    """Dimensao temporal: ano + numero da semana epidemiologica (datas DATE)."""

    __tablename__ = "semana_epidemiologica"

    id_semana_epidemiologica: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_epidemiologico: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    numero_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    data_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)


class RegistroEpidemiologico(Base):
    """Fato agregado por semana: casos-proxy de Influenza A no municipio de SP."""

    __tablename__ = "registro_epidemiologico"

    id_registro: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_arquivo_dados: Mapped[int] = mapped_column(
        Integer, ForeignKey("arquivo_dados.id_arquivo_dados"), nullable=False
    )
    id_semana_epidemiologica: Mapped[int] = mapped_column(
        Integer, ForeignKey("semana_epidemiologica.id_semana_epidemiologica"), nullable=False
    )
    id_unidade_notificacao: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("unidade_notificacao.id_unidade_notificacao"), nullable=True
    )
    quantidade_casos_proxy: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    quantidade_registros: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    data_referencia: Mapped[date | None] = mapped_column(Date, nullable=True)


class SerieTemporal(Base):
    """Serie semanal consolidada consumida pelo modelo preditivo."""

    __tablename__ = "serie_temporal"

    id_serie_temporal: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_semana_epidemiologica: Mapped[int] = mapped_column(
        Integer, ForeignKey("semana_epidemiologica.id_semana_epidemiologica"), nullable=False
    )
    id_unidade_notificacao: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("unidade_notificacao.id_unidade_notificacao"), nullable=True
    )
    casos_proxy: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    reservada_atraso_notificacao: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="0"
    )
    usar_no_treino: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    semana: Mapped["SemanaEpidemiologica"] = relationship()


class ModeloPreditivo(Base):
    """Metadados do modelo de IA (nome, versao, algoritmo, .joblib, versao ativa)."""

    __tablename__ = "modelo_preditivo"

    id_modelo: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    algoritmo: Mapped[str] = mapped_column(String(150), nullable=False)
    versao: Mapped[str] = mapped_column(String(30), nullable=False)
    caminho_modelo_serializado: Mapped[str | None] = mapped_column(Text, nullable=True)
    janela_historica_semanas: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    horizonte_previsao_semanas: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    data_treinamento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status_modelo: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="treinado"
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    metricas: Mapped[list["MetricaModelo"]] = relationship(back_populates="modelo")


class MetricaModelo(Base):
    """Metricas de avaliacao (MAE, RMSE, MAPE, acerto direcional) e significancia."""

    __tablename__ = "metrica_modelo"

    id_metrica: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_modelo: Mapped[int] = mapped_column(
        Integer, ForeignKey("modelo_preditivo.id_modelo"), nullable=False
    )
    mae: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    rmse: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    mape: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    acerto_direcional: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    teste_significancia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estatistica_teste: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    p_valor: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    significativo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    data_avaliacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    base_teste_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    base_teste_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    modelo: Mapped["ModeloPreditivo"] = relationship(back_populates="metricas")


class LogProcessamento(Base):
    """Eventos/alertas/erros de coleta, tratamento, treinamento ou execucao."""

    __tablename__ = "log_processamento"

    id_log: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_arquivo_dados: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("arquivo_dados.id_arquivo_dados"), nullable=True
    )
    id_modelo: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("modelo_preditivo.id_modelo"), nullable=True
    )
    data_hora: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    tipo_evento: Mapped[str] = mapped_column(String(20), nullable=False)
    origem: Mapped[str] = mapped_column(String(100), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pendente")
