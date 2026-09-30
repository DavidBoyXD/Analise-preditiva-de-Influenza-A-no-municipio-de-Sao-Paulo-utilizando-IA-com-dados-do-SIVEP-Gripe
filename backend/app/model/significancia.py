"""Testes de significancia estatistica entre erros de previsao (RF004).

Objetivo: verificar se a diferenca de acuracia entre o Random Forest e um modelo
comparador (baseline, SARIMA ou Prophet) e estatisticamente significativa, e nao
fruto do acaso. Isso e exigido pelo Manual Interno: o modelo NAO pode ser
apresentado como comprovadamente superior sem um teste formal.

Teste principal - Diebold-Mariano (DM):
    Referencia: Diebold, F. X.; Mariano, R. S. (1995). "Comparing Predictive
    Accuracy". Journal of Business & Economic Statistics, 13(3), 253-263.
    Correcao de amostra pequena: Harvey, D.; Leybourne, S.; Newbold, P. (1997).
    "Testing the equality of prediction mean squared errors". International
    Journal of Forecasting, 13(2), 281-291.

    Definicao. Sejam e1_t e e2_t os erros de previsao dos modelos 1 e 2 no
    instante t. Com uma funcao de perda g (aqui o erro quadratico, g(e)=e^2), o
    diferencial de perda e d_t = g(e1_t) - g(e2_t). Sob a hipotese nula de igual
    acuracia, E[d_t] = 0. A estatistica DM e:

        DM = d_barra / sqrt( var_lp(d_barra) )

    onde d_barra e a media de d_t e var_lp e a variancia de longo prazo da media
    (soma das autocovariancias ate a defasagem h-1, para horizonte h). Aplicamos
    a correcao de Harvey-Leybourne-Newbold (HLN) para amostras pequenas e
    comparamos DM* a uma distribuicao t de Student com (n-1) graus de liberdade.

    Interpretacao do sinal (com perda = erro^2, modelo 1 = Random Forest):
        DM < 0  => erro^2 do RF menor => RF mais acurado que o comparador;
        DM > 0  => comparador mais acurado.

Teste alternativo (nao parametrico) - Wilcoxon dos postos com sinais aplicado
aos erros absolutos pareados. Nao assume normalidade; util quando a serie e
curta/esparsa.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ResultadoTeste:
    """Resultado de um teste de significancia entre dois conjuntos de erros."""

    nome: str
    estatistica: float
    p_valor: float
    significativo: bool
    detalhe: str


def _perda_quadratica(e: float) -> float:
    """Funcao de perda: erro quadratico."""
    return e * e


def diebold_mariano(
    erros_modelo: list[float],
    erros_comparador: list[float],
    horizonte: int = 1,
    alpha: float = 0.05,
) -> ResultadoTeste:
    """Aplica o teste de Diebold-Mariano com correcao HLN de amostra pequena.

    Args:
        erros_modelo: Erros de previsao do modelo principal (Random Forest),
            na forma (real - previsto).
        erros_comparador: Erros de previsao do modelo comparador, pareados no
            tempo com ``erros_modelo``.
        horizonte: Horizonte de previsao h (numero de defasagens de
            autocovariancia consideradas: h-1).
        alpha: Nivel de significancia (padrao 0,05).

    Returns:
        ResultadoTeste com a estatistica DM* (corrigida), o p-valor bicaudal
        aproximado pela t de Student e a decisao de significancia.

    Raises:
        ValueError: se as series tiverem tamanhos diferentes ou forem curtas.
    """
    if len(erros_modelo) != len(erros_comparador):
        raise ValueError("As series de erro devem ter o mesmo tamanho.")
    n = len(erros_modelo)
    if n < 2:
        raise ValueError("Diebold-Mariano requer ao menos 2 observacoes.")

    d = [
        _perda_quadratica(a) - _perda_quadratica(b)
        for a, b in zip(erros_modelo, erros_comparador)
    ]
    d_barra = sum(d) / n

    # Autocovariancias gamma_0..gamma_{h-1} do diferencial de perda.
    def gamma(k: int) -> float:
        return sum((d[t] - d_barra) * (d[t - k] - d_barra) for t in range(k, n)) / n

    variancia_lp = gamma(0) + 2.0 * sum(gamma(k) for k in range(1, horizonte))
    if variancia_lp <= 0:
        # Sem variabilidade discernivel: nao ha evidencia de diferenca.
        return ResultadoTeste(
            nome="Diebold-Mariano",
            estatistica=0.0,
            p_valor=1.0,
            significativo=False,
            detalhe="Variancia de longo prazo nao positiva; diferenca nao detectavel.",
        )

    dm = d_barra / math.sqrt(variancia_lp / n)

    # Correcao de Harvey, Leybourne e Newbold (1997) para amostras pequenas.
    fator = (n + 1 - 2 * horizonte + horizonte * (horizonte - 1) / n) / n
    dm_corrigido = dm * math.sqrt(max(fator, 0.0)) if fator > 0 else dm

    graus_liberdade = n - 1
    p_valor = _p_valor_bicaudal_t(dm_corrigido, graus_liberdade)
    significativo = p_valor < alpha
    sentido = (
        "Random Forest mais acurado" if dm_corrigido < 0 else "comparador mais acurado"
    )
    detalhe = (
        f"DM*={dm_corrigido:.4f}, gl={graus_liberdade}, h={horizonte}; "
        f"{'diferenca significativa' if significativo else 'sem diferenca significativa'} "
        f"({sentido})."
    )
    return ResultadoTeste(
        nome="Diebold-Mariano",
        estatistica=dm_corrigido,
        p_valor=p_valor,
        significativo=significativo,
        detalhe=detalhe,
    )


def wilcoxon_erros(
    erros_modelo: list[float],
    erros_comparador: list[float],
    alpha: float = 0.05,
) -> ResultadoTeste:
    """Teste de Wilcoxon dos postos com sinais sobre os erros absolutos pareados.

    Compara |erro_modelo| e |erro_comparador| par a par (nao parametrico, nao
    assume normalidade). Delega o calculo ao scipy quando disponivel; caso
    contrario retorna um resultado sinalizando indisponibilidade.

    Returns:
        ResultadoTeste com a estatistica W e o p-valor do teste bicaudal.
    """
    if len(erros_modelo) != len(erros_comparador):
        raise ValueError("As series de erro devem ter o mesmo tamanho.")

    abs_modelo = [abs(e) for e in erros_modelo]
    abs_comparador = [abs(e) for e in erros_comparador]

    try:
        from scipy.stats import wilcoxon

        diffs = [a - b for a, b in zip(abs_modelo, abs_comparador)]
        if all(abs(x) < 1e-12 for x in diffs):
            return ResultadoTeste(
                nome="Wilcoxon",
                estatistica=0.0,
                p_valor=1.0,
                significativo=False,
                detalhe="Erros absolutos identicos; sem diferenca a testar.",
            )
        estatistica, p_valor = wilcoxon(
            abs_modelo, abs_comparador, zero_method="wilcox"
        )
        significativo = bool(p_valor < alpha)
        mediana_modelo = _mediana(abs_modelo)
        mediana_comp = _mediana(abs_comparador)
        sentido = (
            "Random Forest com menor erro mediano"
            if mediana_modelo < mediana_comp
            else "comparador com menor erro mediano"
        )
        detalhe = (
            f"W={float(estatistica):.4f}; "
            f"{'diferenca significativa' if significativo else 'sem diferenca significativa'} "
            f"({sentido})."
        )
        return ResultadoTeste(
            nome="Wilcoxon",
            estatistica=float(estatistica),
            p_valor=float(p_valor),
            significativo=significativo,
            detalhe=detalhe,
        )
    except ImportError:
        return ResultadoTeste(
            nome="Wilcoxon",
            estatistica=float("nan"),
            p_valor=float("nan"),
            significativo=False,
            detalhe="scipy indisponivel; teste de Wilcoxon nao executado.",
        )


def _mediana(valores: list[float]) -> float:
    """Mediana simples de uma lista de valores."""
    ordenados = sorted(valores)
    n = len(ordenados)
    meio = n // 2
    if n % 2 == 1:
        return ordenados[meio]
    return (ordenados[meio - 1] + ordenados[meio]) / 2.0


def _p_valor_bicaudal_t(estatistica: float, graus_liberdade: int) -> float:
    """p-valor bicaudal de uma estatistica t.

    Usa scipy quando disponivel; caso contrario, aproxima pela funcao beta
    incompleta via math (formula da cauda da distribuicao t de Student).
    """
    try:
        from scipy.stats import t as t_dist

        return float(2.0 * t_dist.sf(abs(estatistica), graus_liberdade))
    except ImportError:
        x = graus_liberdade / (graus_liberdade + estatistica * estatistica)
        # Cauda da t via funcao beta incompleta regularizada I_x(a, b).
        cauda = 0.5 * _beta_incompleta_regularizada(graus_liberdade / 2.0, 0.5, x)
        return float(min(max(2.0 * cauda, 0.0), 1.0))


def _beta_incompleta_regularizada(a: float, b: float, x: float) -> float:
    """Funcao beta incompleta regularizada I_x(a, b) por fracao continua (Lentz)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    ln_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    frente = math.exp(a * math.log(x) + b * math.log(1.0 - x) - ln_beta)

    if x < (a + 1.0) / (a + b + 2.0):
        return frente * _fracao_continua_beta(a, b, x) / a
    return 1.0 - frente * _fracao_continua_beta(b, a, 1.0 - x) / b


def _fracao_continua_beta(a: float, b: float, x: float) -> float:
    """Fracao continua da funcao beta incompleta (metodo de Lentz)."""
    minimo = 1e-30
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    if abs(d) < minimo:
        d = minimo
    d = 1.0 / d
    resultado = d
    for m in range(1, 200):
        m2 = 2 * m
        aa = m * (b - m) * x / ((a + m2 - 1.0) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < minimo:
            d = minimo
        c = 1.0 + aa / c
        if abs(c) < minimo:
            c = minimo
        d = 1.0 / d
        resultado *= d * c
        aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1.0))
        d = 1.0 + aa * d
        if abs(d) < minimo:
            d = minimo
        c = 1.0 + aa / c
        if abs(c) < minimo:
            c = minimo
        d = 1.0 / d
        delta = d * c
        resultado *= delta
        if abs(delta - 1.0) < 1e-10:
            break
    return resultado
