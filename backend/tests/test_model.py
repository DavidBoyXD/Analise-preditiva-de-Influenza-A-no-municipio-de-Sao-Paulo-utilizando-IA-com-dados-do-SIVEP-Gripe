"""Testes do modelo preditivo (RF004).

Cobrem os pontos exigidos pela FEAT-004:

* geracao de atributos temporais (defasagens e medias moveis corretos);
* formato da saida de previsao de 6 semanas;
* calculo das metricas (MAE, RMSE, MAPE com tratamento de zeros, acerto
  direcional) e do teste de significancia.

Os testes sao independentes de banco e de arquivos gerados: constroem series
sinteticas controladas, o que permite conferir os valores esperados de forma
deterministica.
"""

from __future__ import annotations

import math

import pytest

from app.model import (
    calcular_metricas,
    diebold_mariano,
    mae,
    mape,
    rmse,
    wilcoxon_erros,
)
from app.model.features import (
    ConfigAtributos,
    gerar_atributos_proxima_semana,
    gerar_atributos_serie,
)
from app.model.metricas import acerto_direcional, smape

# ---------------------------------------------------------------------------
# Engenharia de atributos temporais
# ---------------------------------------------------------------------------


def test_atributos_lags_e_media_movel_corretos():
    """Confere que lags e medias moveis usam apenas o passado e batem na conta."""
    valores = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    semanas = [1, 2, 3, 4, 5, 6]
    config = ConfigAtributos(
        lags=(1, 2),
        janelas_media_movel=(3,),
        usar_sazonalidade=False,
    )
    X, y, indices = gerar_atributos_serie(valores, semanas, config)

    # historico_minimo = max(lags, janelas) = 3; primeira linha refere-se a t=3.
    assert indices[0] == 3
    assert y[0] == 4.0  # valor em t=3

    # lag_1 = valores[2]=3, lag_2 = valores[1]=2, media_movel_3 = (1+2+3)/3 = 2.
    assert X[0] == [3.0, 2.0, 2.0]

    # Segunda linha (t=4): lag_1=4, lag_2=3, media_movel_3=(2+3+4)/3=3.
    assert X[1] == [4.0, 3.0, 3.0]
    assert y[1] == 5.0


def test_atributos_incluem_sazonalidade_e_nomes():
    """Com sazonalidade, o vetor ganha seno/cosseno e mes; nomes ficam estaveis."""
    config = ConfigAtributos(
        lags=(1,), janelas_media_movel=(2,), usar_sazonalidade=True
    )
    nomes = config.nomes_atributos()
    assert nomes == ["lag_1", "media_movel_2", "sazonal_seno", "sazonal_cosseno", "mes"]

    valores = [10.0, 20.0, 30.0, 40.0]
    semanas = [50, 51, 52, 1]
    X, _y, _idx = gerar_atributos_serie(valores, semanas, config)
    # Cada linha tem exatamente 5 atributos (1 lag + 1 media + 3 sazonais).
    assert all(len(linha) == 5 for linha in X)
    # sen^2 + cos^2 = 1 para os atributos sazonais.
    seno, cosseno = X[0][2], X[0][3]
    assert math.isclose(seno**2 + cosseno**2, 1.0, rel_tol=1e-9)


def test_proxima_semana_reaproveita_formato():
    """gerar_atributos_proxima_semana produz o mesmo formato da matriz de treino."""
    config = ConfigAtributos(
        lags=(1, 2), janelas_media_movel=(3,), usar_sazonalidade=False
    )
    historico = [1.0, 2.0, 3.0]
    vetor = gerar_atributos_proxima_semana(historico, semana_alvo=4, config=config)
    # lag_1=3, lag_2=2, media_movel_3=(1+2+3)/3=2.
    assert vetor == [3.0, 2.0, 2.0]


def test_atributos_historico_insuficiente_levanta_erro():
    """Historico menor que o minimo necessario deve levantar ValueError."""
    config = ConfigAtributos(
        lags=(1, 2, 3), janelas_media_movel=(5,), usar_sazonalidade=False
    )
    with pytest.raises(ValueError):
        gerar_atributos_proxima_semana([1.0, 2.0], semana_alvo=3, config=config)


# ---------------------------------------------------------------------------
# Formato da saida de 6 semanas (previsao recursiva)
# ---------------------------------------------------------------------------


def test_previsao_seis_semanas_formato(preditor_treinado):
    """A previsao de 6 semanas retorna 6 valores nao negativos, na ordem."""
    historico = [(2024, ((i - 1) % 52) + 1, float(10 + (i % 5))) for i in range(1, 81)]
    previsoes = preditor_treinado.prever_series(historico, horizonte=6)
    assert len(previsoes) == 6
    assert all(isinstance(v, float) for v in previsoes)
    assert all(v >= 0.0 for v in previsoes)


def test_previsao_horizonte_arbitrario(preditor_treinado):
    """O horizonte controla a quantidade de semanas previstas."""
    historico = [(2024, ((i - 1) % 52) + 1, float(5 + i % 3)) for i in range(1, 81)]
    assert len(preditor_treinado.prever_series(historico, horizonte=3)) == 3
    assert len(preditor_treinado.prever_series(historico, horizonte=10)) == 10


# ---------------------------------------------------------------------------
# Metricas
# ---------------------------------------------------------------------------


def test_mae_e_rmse_valores_conhecidos():
    """MAE e RMSE batem com o calculo manual."""
    real = [10.0, 20.0, 30.0]
    previsto = [12.0, 18.0, 33.0]
    # erros abs: 2, 2, 3 -> MAE = 7/3.
    assert math.isclose(mae(real, previsto), 7.0 / 3.0, rel_tol=1e-9)
    # erros^2: 4, 4, 9 -> RMSE = sqrt(17/3).
    assert math.isclose(rmse(real, previsto), math.sqrt(17.0 / 3.0), rel_tol=1e-9)


def test_mape_ignora_semanas_de_zero():
    """MAPE classico descarta semanas com real == 0 (evita divisao por zero)."""
    real = [0.0, 10.0, 0.0, 50.0]
    previsto = [5.0, 11.0, 3.0, 45.0]
    # Apenas t=1 (|1/10|=0.1) e t=3 (|5/50|=0.1) entram -> MAPE = 10%.
    assert math.isclose(mape(real, previsto), 10.0, rel_tol=1e-9)


def test_mape_todos_zeros_e_nan():
    """Quando todos os reais sao zero, o MAPE classico e indefinido (NaN)."""
    resultado = mape([0.0, 0.0], [1.0, 2.0])
    assert math.isnan(resultado)


def test_smape_finito_com_zeros():
    """O sMAPE permanece finito mesmo com semanas de zero casos."""
    valor = smape([0.0, 10.0], [0.0, 10.0])
    assert valor == 0.0  # previsao perfeita, inclusive o zero


def test_acerto_direcional():
    """Acerto direcional compara o sinal das variacoes consecutivas."""
    real = [1.0, 2.0, 1.0, 3.0]  # direcoes: +, -, +
    previsto = [5.0, 6.0, 4.0, 2.0]  # direcoes: +, -, -
    # Acertos em t=1 (+/+) e t=2 (-/-); erro em t=3 (+/-). 2/3.
    assert math.isclose(acerto_direcional(real, previsto), 2.0 / 3.0, rel_tol=1e-9)


def test_calcular_metricas_estrutura():
    """calcular_metricas devolve todas as chaves esperadas e conta zeros."""
    real = [0.0, 10.0, 20.0, 0.0]
    previsto = [1.0, 9.0, 22.0, 2.0]
    m = calcular_metricas(real, previsto)
    for chave in (
        "mae",
        "rmse",
        "mape",
        "smape",
        "acerto_direcional",
        "semanas_ignoradas_mape",
    ):
        assert chave in m
    assert m["semanas_ignoradas_mape"] == 2.0


# ---------------------------------------------------------------------------
# Testes de significancia
# ---------------------------------------------------------------------------


def test_diebold_mariano_detecta_modelo_melhor():
    """DM aponta o Random Forest quando ele erra sistematicamente menos."""
    # erros do modelo pequenos; erros do comparador grandes.
    erros_rf = [0.5, -0.4, 0.6, -0.5, 0.3, -0.2, 0.4, -0.3, 0.5, -0.4] * 3
    erros_comp = [5.0, -4.5, 6.0, -5.5, 4.0, -3.5, 5.0, -4.0, 6.0, -5.0] * 3
    resultado = diebold_mariano(erros_rf, erros_comp, horizonte=1)
    assert resultado.nome == "Diebold-Mariano"
    assert resultado.estatistica < 0  # RF mais acurado
    assert 0.0 <= resultado.p_valor <= 1.0
    assert resultado.significativo is True


def test_diebold_mariano_p_valor_no_intervalo():
    """O p-valor do DM fica sempre no intervalo [0, 1]."""
    erros_rf = [1.0, -1.0, 2.0, -2.0, 1.5, -1.5]
    erros_comp = [1.1, -0.9, 2.1, -1.8, 1.4, -1.6]
    resultado = diebold_mariano(erros_rf, erros_comp, horizonte=6)
    assert 0.0 <= resultado.p_valor <= 1.0


def test_wilcoxon_erros_retorna_resultado():
    """O teste de Wilcoxon retorna estatistica e p-valor validos."""
    erros_rf = [0.5, -0.4, 0.6, -0.5, 0.3, -0.2, 0.4, -0.3]
    erros_comp = [5.0, -4.5, 6.0, -5.5, 4.0, -3.5, 5.0, -4.0]
    resultado = wilcoxon_erros(erros_rf, erros_comp)
    assert resultado.nome == "Wilcoxon"
    if not math.isnan(resultado.p_valor):
        assert 0.0 <= resultado.p_valor <= 1.0
