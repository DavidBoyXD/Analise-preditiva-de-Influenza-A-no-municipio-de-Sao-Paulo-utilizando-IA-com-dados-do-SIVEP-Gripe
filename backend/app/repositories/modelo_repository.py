"""Acesso a dados de modelos preditivos e suas metricas."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MetricaModelo, ModeloPreditivo


def obter_modelo_ativo(db: Session) -> ModeloPreditivo | None:
    """Retorna o modelo preditivo marcado como ativo, ou None se nao houver.

    Args:
        db: Sessao SQLAlchemy.

    Returns:
        Instancia de ModeloPreditivo ativa ou None.
    """
    stmt = (
        select(ModeloPreditivo)
        .where(ModeloPreditivo.ativo.is_(True))
        .order_by(ModeloPreditivo.data_treinamento.desc())
    )
    return db.execute(stmt).scalars().first()


def obter_metrica_mais_recente(db: Session, id_modelo: int) -> MetricaModelo | None:
    """Retorna a metrica mais recente de um modelo.

    Args:
        db: Sessao SQLAlchemy.
        id_modelo: Identificador do modelo.

    Returns:
        Instancia de MetricaModelo mais recente ou None.
    """
    stmt = (
        select(MetricaModelo)
        .where(MetricaModelo.id_modelo == id_modelo)
        .order_by(MetricaModelo.data_avaliacao.desc())
    )
    return db.execute(stmt).scalars().first()
