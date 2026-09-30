"""Engenharia de atributos temporais para a previsao de casos-proxy (RF004).

A serie temporal semanal municipal (casos-proxy de Influenza A em Sao Paulo) e
transformada em uma matriz supervisionada de atributos preditores (X) e alvo (y)
usando exclusivamente informacao PASSADA de cada semana, para respeitar a ordem
cronologica (nunca ha vazamento de informacao futura):

* defasagens (lags) de 1..k semanas;
* medias moveis de janelas configuraveis (ex.: 3 e 5 semanas), calculadas apenas
  sobre valores anteriores a semana-alvo;
* indicadores de sazonalidade derivados da semana epidemiologica: seno/cosseno
  do ciclo anual (52 semanas) e o mes aproximado da semana.

O MESMO gerador de atributos e usado no treino (``scripts/train_model.py``) e na
previsao em producao (``app.services.previsao_service``), de modo que o formato
das features seja identico nos dois momentos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConfigAtributos:
    """Configuracao da engenharia de atributos temporais.

    Atributos:
        lags: Defasagens (em semanas) usadas como preditores. Ex.: (1, 2, 3, 4).
        janelas_media_movel: Tamanhos de janela das medias moveis. Ex.: (3, 5).
        usar_sazonalidade: Se inclui os indicadores de sazonalidade (seno/cosseno
            do ciclo anual e o mes aproximado da semana).
        semanas_por_ano: Numero de semanas por ano usado no ciclo sazonal (52).
    """

    lags: tuple[int, ...] = (1, 2, 3, 4)
    janelas_media_movel: tuple[int, ...] = (3, 5)
    usar_sazonalidade: bool = True
    semanas_por_ano: int = 52

    @property
    def historico_minimo(self) -> int:
        """Quantidade minima de observacoes passadas para gerar uma linha valida.

        E o maior valor entre o maior lag e a maior janela de media movel: antes
        disso nao ha historico suficiente para todos os atributos.
        """
        candidatos = list(self.lags) + list(self.janelas_media_movel)
        return max(candidatos) if candidatos else 0

    def nomes_atributos(self) -> list[str]:
        """Lista, em ordem estavel, os nomes das colunas de atributos gerados."""
        nomes: list[str] = [f"lag_{k}" for k in self.lags]
        nomes += [f"media_movel_{j}" for j in self.janelas_media_movel]
        if self.usar_sazonalidade:
            nomes += ["sazonal_seno", "sazonal_cosseno", "mes"]
        return nomes


#: Configuracao padrao usada pelo treino e pela previsao em producao.
CONFIG_ATRIBUTOS_PADRAO = ConfigAtributos()


def _mes_aproximado(numero_semana: int) -> int:
    """Aproxima o mes (1-12) a partir do numero da semana epidemiologica (1-53)."""
    mes = math.ceil(numero_semana / 4.34524)
    return min(max(mes, 1), 12)


def _atributos_sazonais(numero_semana: int, semanas_por_ano: int) -> list[float]:
    """Calcula os indicadores de sazonalidade para uma semana epidemiologica."""
    angulo = 2.0 * math.pi * (numero_semana / semanas_por_ano)
    return [math.sin(angulo), math.cos(angulo), float(_mes_aproximado(numero_semana))]


def gerar_atributos_serie(
    valores: list[float],
    semanas: list[int],
    config: ConfigAtributos = CONFIG_ATRIBUTOS_PADRAO,
) -> tuple[list[list[float]], list[float], list[int]]:
    """Gera a matriz supervisionada (X, y) a partir da serie de valores.

    Para cada posicao ``t`` com historico suficiente, os atributos usam somente
    valores ate ``t-1`` (defasagens e medias moveis) e a sazonalidade da propria
    semana-alvo ``t`` (a semana epidemiologica de destino e conhecida de antemao).
    O alvo ``y[t]`` e o valor observado em ``t``.

    Args:
        valores: Serie de casos-proxy ordenada cronologicamente.
        semanas: Numero da semana epidemiologica correspondente a cada valor.
        config: Configuracao da engenharia de atributos.

    Returns:
        Tupla (X, y, indices) onde X e a lista de vetores de atributos, y o alvo
        e indices as posicoes originais da serie que geraram cada linha.

    Raises:
        ValueError: se ``valores`` e ``semanas`` tiverem tamanhos diferentes.
    """
    if len(valores) != len(semanas):
        raise ValueError("valores e semanas devem ter o mesmo tamanho.")

    inicio = config.historico_minimo
    X: list[list[float]] = []
    y: list[float] = []
    indices: list[int] = []

    for t in range(inicio, len(valores)):
        linha: list[float] = []
        for k in config.lags:
            linha.append(float(valores[t - k]))
        for janela in config.janelas_media_movel:
            trecho = valores[t - janela : t]
            linha.append(sum(trecho) / janela)
        if config.usar_sazonalidade:
            linha.extend(_atributos_sazonais(semanas[t], config.semanas_por_ano))

        X.append(linha)
        y.append(float(valores[t]))
        indices.append(t)

    return X, y, indices


def gerar_atributos_proxima_semana(
    historico_valores: list[float],
    semana_alvo: int,
    config: ConfigAtributos = CONFIG_ATRIBUTOS_PADRAO,
) -> list[float]:
    """Gera o vetor de atributos de UMA proxima semana a partir do historico.

    Usado na previsao recursiva de producao: dado o historico ate a semana
    anterior e a semana epidemiologica de destino, monta o vetor de atributos no
    mesmo formato de ``gerar_atributos_serie``.

    Args:
        historico_valores: Valores observados/previstos ate a semana anterior a
            semana-alvo (o ultimo elemento e o valor da semana imediatamente
            anterior).
        semana_alvo: Numero da semana epidemiologica que se deseja prever.
        config: Configuracao da engenharia de atributos.

    Returns:
        Vetor de atributos da proxima semana.

    Raises:
        ValueError: se nao houver historico suficiente para todos os atributos.
    """
    if len(historico_valores) < config.historico_minimo:
        raise ValueError(
            "Historico insuficiente para gerar atributos: "
            f"necessario {config.historico_minimo}, recebido {len(historico_valores)}."
        )

    linha: list[float] = []
    for k in config.lags:
        linha.append(float(historico_valores[-k]))
    for janela in config.janelas_media_movel:
        trecho = historico_valores[-janela:]
        linha.append(sum(trecho) / janela)
    if config.usar_sazonalidade:
        linha.extend(_atributos_sazonais(semana_alvo, config.semanas_por_ano))
    return linha


@dataclass
class MatrizTreino:
    """Resultado da construcao da matriz de treino supervisionada."""

    X: list[list[float]] = field(default_factory=list)
    y: list[float] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)
    nomes_atributos: list[str] = field(default_factory=list)


def construir_matriz_treino(
    valores: list[float],
    semanas: list[int],
    config: ConfigAtributos = CONFIG_ATRIBUTOS_PADRAO,
) -> MatrizTreino:
    """Constroi a matriz de treino supervisionada com os nomes dos atributos."""
    X, y, indices = gerar_atributos_serie(valores, semanas, config)
    return MatrizTreino(
        X=X, y=y, indices=indices, nomes_atributos=config.nomes_atributos()
    )
