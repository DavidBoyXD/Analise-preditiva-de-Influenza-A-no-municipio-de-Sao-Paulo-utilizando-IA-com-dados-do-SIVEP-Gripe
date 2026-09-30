"""Definicao dos endpoints REST da API (RF001/RF002/RF003).

Todos os endpoints retornam o envelope JSON padronizado {sucesso, dados,
mensagem}. As mensagens e descricoes estao em Portugues-Brasil; os nomes de
rota seguem a convencao tecnica (ingles/kebab) do FastAPI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import obter_logger
from app.db import get_db
from app.schemas.common import RespostaPadrao, resposta_ok
from app.schemas.epidemiologia import (
    MetricaResposta,
    PontoSerie,
    PrevisaoResposta,
    StatusResposta,
    UnidadeNotificacaoResposta,
)
from app.services import (
    dados_service,
    metricas_service,
    previsao_service,
    unidades_service,
)
from app.services.erros import PrevisaoIndisponivel, RecursoNaoEncontrado

logger = obter_logger("api.rotas")

router = APIRouter(prefix="/api")


@router.get(
    "/status",
    response_model=RespostaPadrao[StatusResposta],
    summary="Healthcheck da API",
    tags=["Sistema"],
)
def status(db: Session = Depends(get_db)) -> dict:
    """Verifica a saude da API, a conexao com o banco e o modelo carregado."""
    settings = get_settings()
    banco_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # o status nunca deve levantar erro nao tratado
        banco_ok = False
        logger.warning("Healthcheck: banco indisponivel (%s).", exc)

    dados = {
        "status": "ok" if banco_ok else "degradado",
        "aplicacao": settings.app_nome,
        "versao": settings.app_versao,
        "banco_conectado": banco_ok,
        "modelo_carregado": previsao_service.modelo_esta_carregado(),
    }
    return resposta_ok(dados, "API operacional.")


@router.get(
    "/dados",
    response_model=RespostaPadrao[list[PontoSerie]],
    summary="Registros/serie filtrados por periodo (semana/ano inicio-fim)",
    tags=["Dados historicos"],
)
def dados(
    db: Session = Depends(get_db),
    ano_inicio: int | None = Query(default=None, description="Ano epidemiologico inicial."),
    semana_inicio: int | None = Query(
        default=None, ge=1, le=53, description="Semana epidemiologica inicial (1-53)."
    ),
    ano_fim: int | None = Query(default=None, description="Ano epidemiologico final."),
    semana_fim: int | None = Query(
        default=None, ge=1, le=53, description="Semana epidemiologica final (1-53)."
    ),
) -> dict:
    """Retorna os dados historicos semanais filtrados por periodo.

    O intervalo e validado no servico (inicio <= fim); parametros incoerentes
    retornam 400 com mensagem clara (tratado no handler global).
    """
    dados_serie = dados_service.obter_serie(
        db,
        ano_inicio=ano_inicio,
        semana_inicio=semana_inicio,
        ano_fim=ano_fim,
        semana_fim=semana_fim,
    )
    mensagem = (
        "Dados retornados com sucesso."
        if dados_serie
        else "Nenhum dado encontrado para o periodo informado."
    )
    return resposta_ok(dados_serie, mensagem)


@router.get(
    "/series-temporais",
    response_model=RespostaPadrao[list[PontoSerie]],
    summary="Serie temporal semanal do municipio de Sao Paulo",
    tags=["Dados historicos"],
)
def series_temporais(
    db: Session = Depends(get_db),
    apenas_treino: bool = Query(
        default=False,
        description="Se verdadeiro, exclui as semanas reservadas por atraso de notificacao.",
    ),
) -> dict:
    """Retorna a serie temporal semanal municipal completa (ou apenas treino)."""
    serie = dados_service.obter_serie(db, apenas_treino=apenas_treino)
    mensagem = (
        "Serie temporal retornada com sucesso."
        if serie
        else "Serie temporal vazia (nenhum ponto cadastrado)."
    )
    return resposta_ok(serie, mensagem)


@router.get(
    "/previsoes",
    response_model=RespostaPadrao[PrevisaoResposta],
    summary="Estimativas de 6 semanas do modelo (com fallback baseline)",
    tags=["Previsao"],
)
def previsoes(
    db: Session = Depends(get_db),
    horizonte: int = Query(
        default=6, ge=1, le=12, description="Quantidade de semanas a prever (1-12)."
    ),
) -> dict:
    """Retorna a previsao de casos-proxy para as proximas semanas.

    Usa o modelo treinado quando disponivel; caso contrario, o baseline. Se o
    modulo preditivo falhar, retorna erro tratado (503) sem afetar os demais
    endpoints (RF002 / tolerancia a falhas).
    """
    resultado = previsao_service.prever(db, horizonte=horizonte)
    origem = resultado["origem_modelo"]
    mensagem = (
        "Previsao gerada pelo modelo treinado."
        if origem == "modelo_treinado"
        else "Previsao gerada pelo baseline (modelo treinado indisponivel)."
    )
    return resposta_ok(resultado, mensagem)


@router.get(
    "/metricas",
    response_model=RespostaPadrao[MetricaResposta],
    summary="MAE/RMSE/MAPE/acerto direcional do modelo ativo",
    tags=["Previsao"],
)
def metricas(db: Session = Depends(get_db)) -> dict:
    """Retorna as metricas de avaliacao do modelo preditivo ativo."""
    dados_metrica = metricas_service.obter_metricas_modelo_ativo(db)
    return resposta_ok(dados_metrica, "Metricas do modelo ativo retornadas com sucesso.")


@router.get(
    "/unidades-notificacao",
    response_model=RespostaPadrao[list[UnidadeNotificacaoResposta]],
    summary="Lista de unidades de notificacao (a fonte pode nao popular NM_UN_INTE)",
    tags=["Dados historicos"],
)
def unidades_notificacao(db: Session = Depends(get_db)) -> dict:
    """Lista as unidades de notificacao cadastradas.

    A fonte consolidada atual NAO popula NM_UN_INTE; nesse caso o campo vem
    nulo e fonte_populada = falso (pendencia documentada).
    """
    unidades = unidades_service.listar_unidades(db)
    mensagem = (
        "Unidades de notificacao retornadas com sucesso."
        if unidades
        else "Nenhuma unidade de notificacao cadastrada."
    )
    return resposta_ok(unidades, mensagem)


# Reexporta as excecoes de dominio para o handler global (importadas no main).
__all__ = ["router", "PrevisaoIndisponivel", "RecursoNaoEncontrado"]
