"""Metricas de avaliacao de previsao (RF004).

Implementa MAE, RMSE, MAPE e acerto direcional. Todas as funcoes operam sobre
listas de floats (real x previsto) e sao independentes de framework, para poder
ser testadas isoladamente e reutilizadas no script de treino.

Tratamento de MAPE em semanas de zero casos: o MAPE classico divide pelo valor
real e, portanto, e indefinido quando o real e zero (divisao por zero) - situacao
frequente nesta serie, que e esparsa. Adotamos o sMAPE (MAPE simetrico) como
metrica reportada de erro percentual, pois ele e finito mesmo com zeros, e
tambem calculamos um MAPE classico restrito as semanas com real > 0, sinalizando
quantas semanas foram ignoradas. Essa ressalva esta documentada no relatorio de
qualidade e nas limitacoes do modelo.
"""

from __future__ import annotations

import math


def _validar(real: list[float], previsto: list[float]) -> None:
    """Valida que as series tem o mesmo tamanho e nao estao vazias."""
    if len(real) != len(previsto):
        raise ValueError("real e previsto devem ter o mesmo tamanho.")
    if not real:
        raise ValueError("as series de erro nao podem ser vazias.")


def erros_absolutos(real: list[float], previsto: list[float]) -> list[float]:
    """Retorna a lista de erros absolutos |real - previsto| por ponto."""
    _validar(real, previsto)
    return [abs(r - p) for r, p in zip(real, previsto)]


def mae(real: list[float], previsto: list[float]) -> float:
    """Erro Medio Absoluto (Mean Absolute Error)."""
    abs_ = erros_absolutos(real, previsto)
    return sum(abs_) / len(abs_)


def rmse(real: list[float], previsto: list[float]) -> float:
    """Raiz do Erro Quadratico Medio (Root Mean Squared Error)."""
    _validar(real, previsto)
    quadrados = [(r - p) ** 2 for r, p in zip(real, previsto)]
    return math.sqrt(sum(quadrados) / len(quadrados))


def mape(real: list[float], previsto: list[float]) -> float:
    """MAPE classico restrito as semanas com real > 0 (evita divisao por zero).

    Retorna o erro percentual absoluto medio (em %) considerando apenas os pontos
    com valor real diferente de zero. Se todos os reais forem zero, retorna NaN
    (indefinido), sinalizando que a metrica nao se aplica ao trecho.
    """
    _validar(real, previsto)
    percentuais = [abs((r - p) / r) for r, p in zip(real, previsto) if r != 0]
    if not percentuais:
        return float("nan")
    return 100.0 * sum(percentuais) / len(percentuais)


def smape(real: list[float], previsto: list[float]) -> float:
    """MAPE simetrico (sMAPE), finito mesmo com zeros (em %).

    Divide pela soma dos modulos de real e previsto; quando ambos sao zero o
    ponto contribui com erro zero (previsao perfeita de ausencia de casos).
    """
    _validar(real, previsto)
    total = 0.0
    for r, p in zip(real, previsto):
        denominador = abs(r) + abs(p)
        if denominador == 0:
            total += 0.0
        else:
            total += abs(r - p) / denominador
    return 100.0 * total / len(real)


def acerto_direcional(real: list[float], previsto: list[float]) -> float:
    """Proporcao de acerto na direcao (subida/descida) entre semanas consecutivas.

    Compara o sinal da variacao real (real[t] - real[t-1]) com o sinal da
    variacao prevista. Retorna a fracao de acertos (0 a 1). Requer ao menos duas
    observacoes; com menos de duas, retorna NaN.
    """
    _validar(real, previsto)
    if len(real) < 2:
        return float("nan")
    acertos = 0
    total = 0
    for t in range(1, len(real)):
        dir_real = _sinal(real[t] - real[t - 1])
        dir_prev = _sinal(previsto[t] - previsto[t - 1])
        total += 1
        if dir_real == dir_prev:
            acertos += 1
    return acertos / total if total else float("nan")


def _sinal(valor: float) -> int:
    """Retorna -1, 0 ou 1 conforme o sinal do valor."""
    if valor > 0:
        return 1
    if valor < 0:
        return -1
    return 0


def calcular_metricas(real: list[float], previsto: list[float]) -> dict[str, float]:
    """Calcula o conjunto de metricas de avaliacao de uma serie real x prevista.

    Returns:
        Dicionario com as chaves ``mae``, ``rmse``, ``mape`` (classico, semanas
        com real > 0), ``smape``, ``acerto_direcional`` e
        ``semanas_ignoradas_mape`` (quantidade de semanas com real == 0
        descartadas do MAPE classico).
    """
    _validar(real, previsto)
    semanas_zero = sum(1 for r in real if r == 0)
    return {
        "mae": mae(real, previsto),
        "rmse": rmse(real, previsto),
        "mape": mape(real, previsto),
        "smape": smape(real, previsto),
        "acerto_direcional": acerto_direcional(real, previsto),
        "semanas_ignoradas_mape": float(semanas_zero),
    }
