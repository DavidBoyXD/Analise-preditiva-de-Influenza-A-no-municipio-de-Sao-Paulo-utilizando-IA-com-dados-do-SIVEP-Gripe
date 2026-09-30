"""Regras de negocio para leitura das metricas do modelo ativo."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import modelo_repository
from app.services.erros import RecursoNaoEncontrado


def _para_float(valor: object) -> float | None:
    """Converte um valor numerico do banco (incl. Decimal) em float, ou None."""
    if valor is None:
        return None
    return float(valor)


def obter_metricas_modelo_ativo(db: Session) -> dict:
    """Retorna as metricas mais recentes do modelo ativo.

    Args:
        db: Sessao SQLAlchemy.

    Returns:
        Dicionario pronto para o schema MetricaResposta.

    Raises:
        RecursoNaoEncontrado: quando nao ha modelo ativo ou metricas registradas.
    """
    modelo = modelo_repository.obter_modelo_ativo(db)
    if modelo is None:
        raise RecursoNaoEncontrado(
            "Nenhum modelo preditivo ativo foi encontrado no banco de dados."
        )

    metrica = modelo_repository.obter_metrica_mais_recente(db, modelo.id_modelo)
    if metrica is None:
        raise RecursoNaoEncontrado(
            "O modelo ativo ainda nao possui metricas de avaliacao registradas."
        )

    return {
        "nome_modelo": modelo.nome_modelo,
        "versao": modelo.versao,
        "algoritmo": modelo.algoritmo,
        "mae": _para_float(metrica.mae),
        "rmse": _para_float(metrica.rmse),
        "mape": _para_float(metrica.mape),
        "acerto_direcional": _para_float(metrica.acerto_direcional),
        "teste_significancia": metrica.teste_significancia,
        "p_valor": _para_float(metrica.p_valor),
        "significativo": metrica.significativo,
    }
