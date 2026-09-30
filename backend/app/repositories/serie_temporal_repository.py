"""Acesso a dados da serie temporal semanal (compativel com Postgres e SQLite)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SemanaEpidemiologica, SerieTemporal


def listar_serie(
    db: Session,
    ano_inicio: int | None = None,
    semana_inicio: int | None = None,
    ano_fim: int | None = None,
    semana_fim: int | None = None,
    apenas_treino: bool = False,
) -> list[tuple[SerieTemporal, SemanaEpidemiologica]]:
    """Lista pontos da serie temporal, opcionalmente filtrados por periodo.

    O filtro por periodo usa a chave composta (ano, semana) traduzida para um
    valor ordenavel (ano * 100 + semana), o que e portavel entre PostgreSQL e
    SQLite (evita SQL cru dependente de dialeto).

    Args:
        db: Sessao SQLAlchemy.
        ano_inicio: Ano epidemiologico inicial (inclusive), quando informado.
        semana_inicio: Semana inicial (inclusive), quando informado.
        ano_fim: Ano epidemiologico final (inclusive), quando informado.
        semana_fim: Semana final (inclusive), quando informado.
        apenas_treino: Se TRUE, retorna apenas semanas com usar_no_treino = TRUE.

    Returns:
        Lista de tuplas (SerieTemporal, SemanaEpidemiologica) ordenadas por
        ano e semana crescentes.
    """
    stmt = (
        select(SerieTemporal, SemanaEpidemiologica)
        .join(
            SemanaEpidemiologica,
            SerieTemporal.id_semana_epidemiologica == SemanaEpidemiologica.id_semana_epidemiologica,
        )
        .order_by(
            SemanaEpidemiologica.ano_epidemiologico,
            SemanaEpidemiologica.numero_semana,
        )
    )

    ordenavel = SemanaEpidemiologica.ano_epidemiologico * 100 + SemanaEpidemiologica.numero_semana
    if ano_inicio is not None and semana_inicio is not None:
        stmt = stmt.where(ordenavel >= ano_inicio * 100 + semana_inicio)
    if ano_fim is not None and semana_fim is not None:
        stmt = stmt.where(ordenavel <= ano_fim * 100 + semana_fim)
    if apenas_treino:
        stmt = stmt.where(SerieTemporal.usar_no_treino.is_(True))

    return list(db.execute(stmt).all())
