"""Servico de previsao de casos-proxy de Influenza A (RF001).

Este servico define a INTERFACE de previsao consumida pela API e implementa um
fallback baseline. O modelo real (Random Forest) e treinado e integrado em
FEAT-004; aqui o servico:

  1. tenta carregar um modelo serializado (.joblib) do diretorio de modelos na
     inicializacao (padrao descrito no TC2, secao 4.6.4 - modelo carregado em
     memoria uma unica vez);
  2. caso nao exista modelo, usa um baseline sazonal-ingenuo calculado a partir
     da propria serie historica do banco (NAO ha dado fixo mockado em producao);
  3. isola falhas: uma exceção no modulo preditivo vira PrevisaoIndisponivel e
     NAO derruba os endpoints de dados historicos (RF002 / tolerancia a falhas).

O baseline repete, para cada semana futura, a media historica de casos-proxy da
mesma semana epidemiologica (comportamento sazonal-ingenuo). Quando nao ha
historico da semana-alvo, usa a media geral da serie de treino.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import obter_logger
from app.repositories import modelo_repository, serie_temporal_repository
from app.services.erros import PrevisaoIndisponivel

logger = obter_logger("api.previsao")

# Estado do modelo carregado em memoria (padrao TC2 4.6.4). Enquanto FEAT-004
# nao entrega o .joblib, permanece None e o baseline e usado.
_modelo_em_memoria: object | None = None
_modelo_carregado_de: str | None = None


def carregar_modelo() -> None:
    """Tenta carregar um modelo .joblib do diretorio de modelos, se existir.

    Nao lanca excecao se nao houver modelo: apenas registra em log e mantem o
    baseline como estrategia de previsao. Chamada na inicializacao da API.
    """
    global _modelo_em_memoria, _modelo_carregado_de

    settings = get_settings()
    diretorio = Path(settings.caminho_modelos)
    if not diretorio.exists():
        logger.info("Diretorio de modelos '%s' inexistente; usando baseline.", diretorio)
        return

    arquivos = sorted(diretorio.glob("*.joblib"))
    if not arquivos:
        logger.info("Nenhum .joblib encontrado em '%s'; usando baseline.", diretorio)
        return

    caminho = arquivos[-1]
    try:
        import joblib

        _modelo_em_memoria = joblib.load(caminho)
        _modelo_carregado_de = str(caminho)
        logger.info("Modelo preditivo carregado em memoria de '%s'.", caminho)
    except Exception as exc:  # tolerancia a falhas: baseline assume o lugar
        _modelo_em_memoria = None
        _modelo_carregado_de = None
        logger.warning("Falha ao carregar modelo de '%s' (%s); usando baseline.", caminho, exc)


def modelo_esta_carregado() -> bool:
    """Indica se ha um modelo preditivo carregado em memoria."""
    return _modelo_em_memoria is not None


def _proximas_semanas(ano: int, semana: int, quantidade: int) -> list[tuple[int, int]]:
    """Gera os pares (ano, semana) das proximas `quantidade` semanas.

    Trata a virada de ano de forma simples usando 52 semanas por ano (a semana
    53 e rara; a modelagem definitiva fica a cargo de FEAT-004).
    """
    resultado: list[tuple[int, int]] = []
    ano_atual, semana_atual = ano, semana
    for _ in range(quantidade):
        semana_atual += 1
        if semana_atual > 52:
            semana_atual = 1
            ano_atual += 1
        resultado.append((ano_atual, semana_atual))
    return resultado


def _prever_baseline(historico: list[tuple[int, int, int]], horizonte: int) -> list[dict]:
    """Calcula a previsao baseline sazonal-ingenua a partir do historico.

    Args:
        historico: Lista de (ano, semana, casos_proxy) da serie de treino,
            ordenada por tempo.
        horizonte: Quantidade de semanas a prever.

    Returns:
        Lista de dicionarios prontos para o schema PrevisaoSemana.
    """
    if not historico:
        raise PrevisaoIndisponivel(
            "Nao ha serie historica suficiente para gerar a previsao baseline."
        )

    media_por_semana: dict[int, list[int]] = {}
    for _ano, semana, casos in historico:
        media_por_semana.setdefault(semana, []).append(casos)

    todos = [casos for _a, _s, casos in historico]
    media_geral = sum(todos) / len(todos)

    ultimo_ano, ultima_semana, _ = historico[-1]
    alvos = _proximas_semanas(ultimo_ano, ultima_semana, horizonte)

    previsoes: list[dict] = []
    for indice, (ano, semana) in enumerate(alvos, start=1):
        amostras = media_por_semana.get(semana)
        estimativa = (sum(amostras) / len(amostras)) if amostras else media_geral
        previsoes.append(
            {
                "horizonte": indice,
                "ano": ano,
                "semana": semana,
                "casos_previstos": round(max(estimativa, 0.0), 2),
            }
        )
    return previsoes


def prever(db: Session, horizonte: int | None = None) -> dict:
    """Gera a previsao de casos-proxy para as proximas semanas.

    Usa o modelo carregado em memoria quando disponivel; caso contrario, aplica
    o baseline sazonal-ingenuo sobre a serie de treino lida do banco. Qualquer
    falha e encapsulada em PrevisaoIndisponivel para preservar a tolerancia a
    falhas exigida pelo RF002.

    Args:
        db: Sessao SQLAlchemy.
        horizonte: Quantidade de semanas a prever (padrao: config, 6 semanas).

    Returns:
        Dicionario pronto para o schema PrevisaoResposta.

    Raises:
        PrevisaoIndisponivel: quando nao e possivel gerar a previsao.
    """
    settings = get_settings()
    horizonte = horizonte or settings.horizonte_previsao_semanas

    try:
        linhas = serie_temporal_repository.listar_serie(db, apenas_treino=True)
        historico = [
            (semana.ano_epidemiologico, semana.numero_semana, serie.casos_proxy)
            for serie, semana in linhas
        ]

        if _modelo_em_memoria is not None:
            # A integracao real (features/predict) e concluida em FEAT-004.
            # A interface abaixo delega ao modelo quando ele expuser prever_series.
            previsoes = _prever_com_modelo(historico, horizonte)
            origem = "modelo_treinado"
            modelo = modelo_repository.obter_modelo_ativo(db)
            nome_modelo = f"{modelo.nome_modelo} v{modelo.versao}" if modelo is not None else None
        else:
            previsoes = _prever_baseline(historico, horizonte)
            origem = "baseline"
            nome_modelo = None

        return {
            "origem_modelo": origem,
            "nome_modelo": nome_modelo,
            "horizonte_semanas": horizonte,
            "previsoes": previsoes,
        }
    except PrevisaoIndisponivel:
        raise
    except Exception as exc:  # isola qualquer falha do modulo preditivo
        logger.error("Falha ao gerar previsao: %s", exc)
        raise PrevisaoIndisponivel("O modulo preditivo esta temporariamente indisponivel.") from exc


def _prever_com_modelo(historico: list[tuple[int, int, int]], horizonte: int) -> list[dict]:
    """Delega a previsao ao modelo carregado (interface para FEAT-004).

    Enquanto FEAT-004 nao padroniza a API do modelo serializado, se o objeto
    carregado nao expuser um metodo `prever_series`, recorre-se ao baseline
    para nao quebrar o endpoint.
    """
    modelo = _modelo_em_memoria
    if hasattr(modelo, "prever_series"):
        pares = _proximas_semanas(historico[-1][0], historico[-1][1], horizonte)
        valores = modelo.prever_series(historico, horizonte)  # type: ignore[attr-defined]
        return [
            {
                "horizonte": i + 1,
                "ano": pares[i][0],
                "semana": pares[i][1],
                "casos_previstos": round(max(float(valores[i]), 0.0), 2),
            }
            for i in range(horizonte)
        ]
    # Modelo carregado mas sem interface conhecida: baseline garante resposta.
    return _prever_baseline(historico, horizonte)
