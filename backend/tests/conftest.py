"""Fixtures de teste da API: banco SQLite em memoria + TestClient do FastAPI.

O banco de teste e um SQLite em memoria (rapido e sem dependencia de servidor
Postgres). O schema e criado via metadados do SQLAlchemy (DDL do dialeto ativo),
e os dados sao populados por uma fixture com uma amostra representativa da serie
temporal, um modelo ativo com metricas e uma unidade de notificacao.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def engine_teste():
    """Cria um engine SQLite em memoria compartilhado entre conexoes."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    return engine


@pytest.fixture
def app_e_dados(engine_teste):
    """Configura a app com o banco de teste populado e devolve (client, dados).

    Sobrescreve a dependencia get_db para usar a sessao de teste e injeta o
    engine de teste no servico de previsao (via app.db.engine nao e necessario
    porque os repositories recebem a sessao por dependencia).
    """
    from app.db import Base, get_db
    from app.main import app
    from app.models import (
        ArquivoDados,
        FonteDados,
        MetricaModelo,
        ModeloPreditivo,
        SemanaEpidemiologica,
        SerieTemporal,
        UnidadeNotificacao,
    )

    Base.metadata.create_all(bind=engine_teste)
    SessionTeste = sessionmaker(bind=engine_teste, autoflush=False, autocommit=False, future=True)

    dados_ref = {"total_pontos": 0, "reservadas": 3}

    with SessionTeste() as sessao:
        fonte = FonteDados(
            id_fonte_dados=1,
            nome_fonte="SIVEP-Gripe / SINAN - DATASUS",
            descricao="Dados publicos de SRAG.",
            url_fonte="https://opendatasus.saude.gov.br/",
        )
        arquivo = ArquivoDados(
            id_arquivo_dados=1,
            id_fonte_dados=1,
            nome_arquivo="base_tratada.csv",
            formato_arquivo="CSV",
            tipo_arquivo="tratado",
            ano_referencia_inicio=2009,
            ano_referencia_fim=2024,
            quantidade_registros=13139,
            status_arquivo="processado",
        )
        unidade = UnidadeNotificacao(
            id_unidade_notificacao=1,
            nm_un_inte=None,
            co_mun_res="355030",
            nome_municipio="Sao Paulo",
            sg_uf="SP",
            fonte_populada=False,
        )
        sessao.add_all([fonte, arquivo, unidade])

        # Serie: 10 semanas de 2024, as 3 ultimas reservadas por atraso.
        casos = [12, 20, 35, 50, 42, 30, 18, 10, 6, 4]
        for i, valor in enumerate(casos, start=1):
            reservada = i > 7
            sessao.add(
                SemanaEpidemiologica(
                    id_semana_epidemiologica=i,
                    ano_epidemiologico=2024,
                    numero_semana=i,
                )
            )
            sessao.add(
                SerieTemporal(
                    id_serie_temporal=i,
                    id_semana_epidemiologica=i,
                    id_unidade_notificacao=1,
                    casos_proxy=valor,
                    reservada_atraso_notificacao=reservada,
                    usar_no_treino=not reservada,
                )
            )
        dados_ref["total_pontos"] = len(casos)

        modelo = ModeloPreditivo(
            id_modelo=1,
            nome_modelo="random_forest",
            algoritmo="RandomForestRegressor",
            versao="1",
            caminho_modelo_serializado="models/random_forest_v1.joblib",
            janela_historica_semanas=8,
            horizonte_previsao_semanas=6,
            data_treinamento=datetime(2024, 3, 1, 12, 0, 0),
            status_modelo="ativo",
            ativo=True,
            observacao="Modelo de teste.",
        )
        sessao.add(modelo)
        sessao.add(
            MetricaModelo(
                id_metrica=1,
                id_modelo=1,
                mae=5.1234,
                rmse=7.8901,
                mape=12.34,
                acerto_direcional=0.75,
                teste_significancia="Diebold-Mariano",
                estatistica_teste=2.1,
                p_valor=0.032,
                significativo=True,
            )
        )
        sessao.commit()

    def _get_db_teste():
        db = SessionTeste()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_teste
    client = TestClient(app)
    yield client, dados_ref
    app.dependency_overrides.clear()


@pytest.fixture
def app_vazia(engine_teste):
    """App com schema criado mas SEM dados (para testar recurso vazio/404)."""
    from app.db import Base, get_db
    from app.main import app

    Base.metadata.create_all(bind=engine_teste)
    SessionTeste = sessionmaker(bind=engine_teste, autoflush=False, autocommit=False, future=True)

    def _get_db_teste():
        db = SessionTeste()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_teste
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
