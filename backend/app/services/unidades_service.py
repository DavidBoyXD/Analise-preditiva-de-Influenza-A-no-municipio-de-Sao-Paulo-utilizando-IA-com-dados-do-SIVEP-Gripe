"""Regras de negocio para unidades de notificacao."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import unidade_repository


def listar_unidades(db: Session) -> list[dict]:
    """Lista as unidades de notificacao cadastradas.

    A fonte consolidada atual NAO popula NM_UN_INTE; nesse caso nm_un_inte vem
    NULO e fonte_populada = FALSE (pendencia documentada em FEAT-002).

    Args:
        db: Sessao SQLAlchemy.

    Returns:
        Lista de dicionarios prontos para o schema UnidadeNotificacaoResposta.
    """
    unidades = unidade_repository.listar_unidades(db)
    return [
        {
            "id_unidade_notificacao": u.id_unidade_notificacao,
            "nm_un_inte": u.nm_un_inte,
            "co_mun_res": u.co_mun_res,
            "nome_municipio": u.nome_municipio,
            "sg_uf": u.sg_uf,
            "fonte_populada": bool(u.fonte_populada),
        }
        for u in unidades
    ]
