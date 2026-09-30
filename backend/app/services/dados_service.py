"""Regras de negocio para dados historicos e series temporais.

Monta a serie historica filtrada por periodo e valida o intervalo informado. A
validacao de intervalo (inicio <= fim) e feita aqui para gerar mensagens claras
em Portugues-Brasil, independentemente do endpoint.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import serie_temporal_repository
from app.services.erros import ErroValidacao


def _validar_periodo(
    ano_inicio: int | None,
    semana_inicio: int | None,
    ano_fim: int | None,
    semana_fim: int | None,
) -> None:
    """Valida a coerencia do periodo informado.

    Regras:
        - inicio e fim devem ser informados em par (ano + semana);
        - o inicio nao pode ser posterior ao fim.

    Raises:
        ErroValidacao: quando os parametros sao incoerentes.
    """
    if (ano_inicio is None) != (semana_inicio is None):
        raise ErroValidacao("Para filtrar pelo inicio, informe ano_inicio e semana_inicio juntos.")
    if (ano_fim is None) != (semana_fim is None):
        raise ErroValidacao("Para filtrar pelo fim, informe ano_fim e semana_fim juntos.")

    if semana_inicio is not None and not 1 <= semana_inicio <= 53:
        raise ErroValidacao("semana_inicio deve estar entre 1 e 53.")
    if semana_fim is not None and not 1 <= semana_fim <= 53:
        raise ErroValidacao("semana_fim deve estar entre 1 e 53.")

    if (
        ano_inicio is not None
        and ano_fim is not None
        and semana_inicio is not None
        and semana_fim is not None
    ):
        inicio = ano_inicio * 100 + semana_inicio
        fim = ano_fim * 100 + semana_fim
        if inicio > fim:
            raise ErroValidacao(
                "O periodo inicial (ano_inicio/semana_inicio) nao pode ser "
                "posterior ao periodo final (ano_fim/semana_fim)."
            )


def obter_serie(
    db: Session,
    ano_inicio: int | None = None,
    semana_inicio: int | None = None,
    ano_fim: int | None = None,
    semana_fim: int | None = None,
    apenas_treino: bool = False,
) -> list[dict]:
    """Retorna a serie temporal semanal filtrada por periodo.

    Args:
        db: Sessao SQLAlchemy.
        ano_inicio: Ano inicial do filtro (opcional, em par com semana_inicio).
        semana_inicio: Semana inicial do filtro (opcional).
        ano_fim: Ano final do filtro (opcional, em par com semana_fim).
        semana_fim: Semana final do filtro (opcional).
        apenas_treino: Se TRUE, exclui as semanas reservadas por atraso.

    Returns:
        Lista de dicionarios prontos para o schema PontoSerie.

    Raises:
        ErroValidacao: quando o periodo informado e incoerente.
    """
    _validar_periodo(ano_inicio, semana_inicio, ano_fim, semana_fim)

    linhas = serie_temporal_repository.listar_serie(
        db,
        ano_inicio=ano_inicio,
        semana_inicio=semana_inicio,
        ano_fim=ano_fim,
        semana_fim=semana_fim,
        apenas_treino=apenas_treino,
    )

    return [
        {
            "ano": semana.ano_epidemiologico,
            "semana": semana.numero_semana,
            "casos_proxy": serie.casos_proxy,
            "reservada_atraso_notificacao": bool(serie.reservada_atraso_notificacao),
            "usar_no_treino": bool(serie.usar_no_treino),
        }
        for serie, semana in linhas
    ]
