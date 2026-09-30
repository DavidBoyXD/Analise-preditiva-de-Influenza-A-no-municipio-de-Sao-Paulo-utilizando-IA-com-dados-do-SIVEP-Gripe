"""Validacao cronologica walk-forward e modelos comparadores (RF004).

A avaliacao NUNCA usa embaralhamento aleatorio: o conjunto de teste e sempre
POSTERIOR ao conjunto de treino. Adotamos o esquema de origem expansiva
(expanding window): a cada passo, o modelo e treinado com todo o historico
disponivel ate a origem e preve o proximo bloco de ``horizonte`` semanas; a
origem entao avanca ``horizonte`` semanas e o processo se repete ate esgotar a
serie de treino. Os pares (real, previsto) de todos os blocos sao concatenados
para o calculo das metricas e dos testes de significancia.

Modelos avaliados sob o MESMO protocolo:
    * baseline ingenuo (media sazonal por semana epidemiologica; fallback: ultimo
      valor observado);
    * Random Forest (scikit-learn) - modelo principal;
    * SARIMA (statsmodels);
    * Prophet (quando instalado).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.model.features import (
    CONFIG_ATRIBUTOS_PADRAO,
    ConfigAtributos,
    gerar_atributos_serie,
)
from app.model.preditor import PreditorRandomForest


@dataclass
class ResultadoWalkForward:
    """Pares reais e previstos acumulados na validacao walk-forward."""

    reais: list[float] = field(default_factory=list)
    previstos: list[float] = field(default_factory=list)
    n_blocos: int = 0


# Assinatura de um preditor de bloco: recebe o historico (valores, semanas) de
# treino e a lista de semanas-alvo do bloco; devolve as previsoes do bloco.
PreditorBloco = Callable[[list[float], list[int], list[int]], list[float]]


def _proximas_semanas(
    semana_inicial: int, quantidade: int, semanas_por_ano: int = 52
) -> list[int]:
    """Gera os numeros das proximas ``quantidade`` semanas epidemiologicas."""
    resultado: list[int] = []
    corrente = semana_inicial
    for _ in range(quantidade):
        corrente = corrente + 1 if corrente < semanas_por_ano else 1
        resultado.append(corrente)
    return resultado


def avaliar_walk_forward(
    valores: list[float],
    semanas: list[int],
    preditor_bloco: PreditorBloco,
    horizonte: int,
    janela_minima: int,
) -> ResultadoWalkForward:
    """Executa a validacao walk-forward com origem expansiva.

    Args:
        valores: Serie de casos-proxy (ordenada cronologicamente).
        semanas: Numero da semana epidemiologica de cada valor.
        preditor_bloco: Funcao que treina/preve um bloco a partir do historico.
        horizonte: Tamanho de cada bloco de previsao (ex.: 6 semanas).
        janela_minima: Tamanho minimo do historico antes da primeira origem.

    Returns:
        ResultadoWalkForward com reais e previstos concatenados.
    """
    resultado = ResultadoWalkForward()
    origem = janela_minima
    n = len(valores)
    while origem < n:
        fim_bloco = min(origem + horizonte, n)
        hist_valores = valores[:origem]
        hist_semanas = semanas[:origem]
        semanas_alvo = semanas[origem:fim_bloco]
        try:
            previsoes = preditor_bloco(hist_valores, hist_semanas, semanas_alvo)
        except Exception:
            previsoes = [hist_valores[-1]] * len(semanas_alvo)
        reais_bloco = valores[origem:fim_bloco]
        tamanho = min(len(previsoes), len(reais_bloco))
        resultado.reais.extend(reais_bloco[:tamanho])
        resultado.previstos.extend(previsoes[:tamanho])
        resultado.n_blocos += 1
        origem = fim_bloco
    return resultado


# ---------------------------------------------------------------------------
# Preditores de bloco por modelo
# ---------------------------------------------------------------------------


def preditor_baseline_sazonal(semanas_por_ano: int = 52) -> PreditorBloco:
    """Baseline ingenuo: media historica dos casos por semana epidemiologica.

    Quando a semana-alvo nunca ocorreu no historico, usa o ultimo valor
    observado (repeticao do ultimo valor - naive persistente).
    """

    def _preditor(
        hist_valores: list[float], hist_semanas: list[int], semanas_alvo: list[int]
    ) -> list[float]:
        media_por_semana: dict[int, list[float]] = {}
        for v, s in zip(hist_valores, hist_semanas):
            media_por_semana.setdefault(s, []).append(v)
        ultimo = hist_valores[-1] if hist_valores else 0.0
        previsoes: list[float] = []
        for s in semanas_alvo:
            amostras = media_por_semana.get(s)
            previsoes.append(sum(amostras) / len(amostras) if amostras else ultimo)
        return previsoes

    return _preditor


def preditor_random_forest(
    parametros: dict, config: ConfigAtributos = CONFIG_ATRIBUTOS_PADRAO
) -> PreditorBloco:
    """Preditor de bloco do Random Forest treinado no historico do passo.

    Reaproveita o objeto ``PreditorRandomForest`` para prever recursivamente o
    bloco, garantindo o MESMO formato de atributos usado em producao.
    """
    from sklearn.ensemble import RandomForestRegressor

    def _preditor(
        hist_valores: list[float], hist_semanas: list[int], semanas_alvo: list[int]
    ) -> list[float]:
        X, y, _ = gerar_atributos_serie(hist_valores, hist_semanas, config)
        if len(X) < 5:
            return [hist_valores[-1]] * len(semanas_alvo)
        modelo = RandomForestRegressor(**parametros)
        modelo.fit(X, y)
        preditor = PreditorRandomForest(modelo=modelo, config=config)
        historico = [(0, s, v) for s, v in zip(hist_semanas, hist_valores)]
        return preditor.prever_series(historico, len(semanas_alvo))

    return _preditor


def preditor_sarima(ordem: tuple, ordem_sazonal: tuple) -> PreditorBloco:
    """Preditor de bloco do SARIMA (statsmodels) treinado no historico do passo."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    def _preditor(
        hist_valores: list[float], hist_semanas: list[int], semanas_alvo: list[int]
    ) -> list[float]:
        modelo = SARIMAX(
            hist_valores,
            order=ordem,
            seasonal_order=ordem_sazonal,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        ajuste = modelo.fit(disp=False)
        previsao = ajuste.forecast(steps=len(semanas_alvo))
        return [max(float(v), 0.0) for v in previsao]

    return _preditor


def preditor_prophet(semanas_por_ano: int = 52) -> PreditorBloco:
    """Preditor de bloco do Prophet treinado no historico do passo.

    O Prophet exige uma coluna de datas; construimos datas semanais sinteticas
    (frequencia de 7 dias) a partir de uma origem fixa, o que preserva a ordem e
    a sazonalidade anual sem depender do calendario epidemiologico exato.
    """
    import pandas as pd
    from prophet import Prophet

    def _preditor(
        hist_valores: list[float], hist_semanas: list[int], semanas_alvo: list[int]
    ) -> list[float]:
        datas = pd.date_range("2009-01-04", periods=len(hist_valores), freq="7D")
        treino = pd.DataFrame({"ds": datas, "y": hist_valores})
        modelo = Prophet(
            weekly_seasonality=False,
            daily_seasonality=False,
            yearly_seasonality=True,
        )
        modelo.fit(treino)
        futuro = modelo.make_future_dataframe(periods=len(semanas_alvo), freq="7D")
        previsao = modelo.predict(futuro)
        valores = previsao["yhat"].tail(len(semanas_alvo)).tolist()
        return [max(float(v), 0.0) for v in valores]

    return _preditor
