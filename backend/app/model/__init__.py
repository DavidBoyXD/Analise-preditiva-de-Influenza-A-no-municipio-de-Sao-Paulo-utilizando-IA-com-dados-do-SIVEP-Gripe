"""Pacote do modelo preditivo (RF004).

Reune a engenharia de atributos temporais, o calculo de metricas, os testes de
significancia estatistica e o objeto serializavel do modelo (Random Forest) que
e salvo em ``models/*.joblib`` e consumido pelo servico de previsao do backend
(FEAT-003).

Este codigo e importavel tanto pelo backend (``from app.model import ...``)
quanto pelo script de treino (``scripts/train_model.py``), garantindo uma unica
fonte de verdade para a geracao de atributos: o formato de features usado no
treino e exatamente o mesmo usado na previsao em producao.
"""

from __future__ import annotations

from app.model.features import (
    CONFIG_ATRIBUTOS_PADRAO,
    ConfigAtributos,
    construir_matriz_treino,
    gerar_atributos_serie,
)
from app.model.metricas import (
    acerto_direcional,
    calcular_metricas,
    mae,
    mape,
    rmse,
)
from app.model.preditor import PreditorRandomForest
from app.model.significancia import diebold_mariano, wilcoxon_erros

__all__ = [
    "ConfigAtributos",
    "CONFIG_ATRIBUTOS_PADRAO",
    "gerar_atributos_serie",
    "construir_matriz_treino",
    "mae",
    "rmse",
    "mape",
    "acerto_direcional",
    "calcular_metricas",
    "diebold_mariano",
    "wilcoxon_erros",
    "PreditorRandomForest",
]
