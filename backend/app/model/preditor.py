"""Objeto serializavel do modelo preditivo (RF004).

``PreditorRandomForest`` encapsula o RandomForestRegressor do scikit-learn junto
com a configuracao de atributos temporais usada no treino. Ele e salvo em
``models/*.joblib`` e carregado em memoria pelo servico de previsao do backend
(FEAT-003), que chama ``prever_series`` - a interface ja prevista em
``app.services.previsao_service._prever_com_modelo``.

A previsao multi-passo (horizonte de 6 semanas) e RECURSIVA: a previsao de uma
semana e reinserida no historico para gerar os atributos da semana seguinte,
mantendo o mesmo formato de features do treino.
"""

from __future__ import annotations

from app.model.features import (
    CONFIG_ATRIBUTOS_PADRAO,
    ConfigAtributos,
    gerar_atributos_proxima_semana,
)


class PreditorRandomForest:
    """Modelo Random Forest com engenharia de atributos temporais embutida.

    Atributos:
        modelo: Estimador scikit-learn ja treinado (RandomForestRegressor).
        config: Configuracao de atributos usada no treino (lags, medias moveis,
            sazonalidade) - reaplicada identicamente na previsao.
        nome: Nome do modelo (ex.: 'random_forest').
        versao: Versao do modelo (ex.: '1').
        semanas_por_ano: Numero de semanas por ano para a virada de ano.
    """

    def __init__(
        self,
        modelo: object,
        config: ConfigAtributos = CONFIG_ATRIBUTOS_PADRAO,
        nome: str = "random_forest",
        versao: str = "1",
        semanas_por_ano: int = 52,
    ) -> None:
        self.modelo = modelo
        self.config = config
        self.nome = nome
        self.versao = versao
        self.semanas_por_ano = semanas_por_ano

    def _proxima_semana(self, semana_atual: int) -> int:
        """Retorna o numero da proxima semana epidemiologica (com virada de ano)."""
        proxima = semana_atual + 1
        if proxima > self.semanas_por_ano:
            return 1
        return proxima

    def prever_series(
        self, historico: list[tuple[int, int, int]], horizonte: int
    ) -> list[float]:
        """Preve os proximos ``horizonte`` valores da serie de forma recursiva.

        Args:
            historico: Lista de (ano, semana, casos_proxy) ordenada por tempo,
                exatamente no formato fornecido pelo servico de previsao.
            horizonte: Quantidade de semanas a prever.

        Returns:
            Lista com ``horizonte`` valores previstos (>= 0), na ordem temporal.

        Raises:
            ValueError: se o historico for insuficiente para gerar atributos.
        """
        valores = [float(casos) for _ano, _semana, casos in historico]
        if len(valores) < self.config.historico_minimo:
            raise ValueError(
                "Historico insuficiente para previsao: "
                f"necessario {self.config.historico_minimo}, recebido {len(valores)}."
            )

        semana_corrente = historico[-1][1]
        previsoes: list[float] = []
        for _ in range(horizonte):
            semana_alvo = self._proxima_semana(semana_corrente)
            atributos = gerar_atributos_proxima_semana(
                valores, semana_alvo, self.config
            )
            estimativa = float(self.modelo.predict([atributos])[0])
            estimativa = max(estimativa, 0.0)
            previsoes.append(estimativa)
            valores.append(estimativa)
            semana_corrente = semana_alvo
        return previsoes
