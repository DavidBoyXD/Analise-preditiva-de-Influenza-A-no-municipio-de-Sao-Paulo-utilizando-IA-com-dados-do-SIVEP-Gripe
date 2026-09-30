"""Acesso a dados de unidades de notificacao."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UnidadeNotificacao


def listar_unidades(db: Session) -> list[UnidadeNotificacao]:
    """Lista as unidades de notificacao cadastradas.

    Args:
        db: Sessao SQLAlchemy.

    Returns:
        Lista de UnidadeNotificacao ordenada pelo identificador.
    """
    stmt = select(UnidadeNotificacao).order_by(UnidadeNotificacao.id_unidade_notificacao)
    return list(db.execute(stmt).scalars().all())
