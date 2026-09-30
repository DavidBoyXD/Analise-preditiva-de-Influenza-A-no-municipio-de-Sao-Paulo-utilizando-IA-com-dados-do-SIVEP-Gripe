"""Testes da API REST (FastAPI) usando SQLite de teste e TestClient.

Cobre: /api/status, /api/dados (periodo valido e invalido), /api/series-temporais,
/api/metricas, /api/previsoes (baseline), formato do envelope JSON e recurso vazio.
"""

from __future__ import annotations


def _validar_envelope(corpo: dict) -> None:
    """Confere que o corpo segue o envelope padronizado {sucesso, dados, mensagem}."""
    assert set(corpo.keys()) == {"sucesso", "dados", "mensagem"}
    assert isinstance(corpo["sucesso"], bool)
    assert isinstance(corpo["mensagem"], str)


def test_status(app_e_dados):
    """/api/status retorna JSON de saude com banco conectado."""
    client, _ = app_e_dados
    resposta = client.get("/api/status")
    assert resposta.status_code == 200
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["sucesso"] is True
    assert corpo["dados"]["status"] == "ok"
    assert corpo["dados"]["banco_conectado"] is True


def test_dados_sem_filtro(app_e_dados):
    """/api/dados sem filtro retorna toda a serie no envelope padrao."""
    client, dados_ref = app_e_dados
    resposta = client.get("/api/dados")
    assert resposta.status_code == 200
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["sucesso"] is True
    assert len(corpo["dados"]) == dados_ref["total_pontos"]
    primeiro = corpo["dados"][0]
    assert set(primeiro.keys()) == {
        "ano",
        "semana",
        "casos_proxy",
        "reservada_atraso_notificacao",
        "usar_no_treino",
    }


def test_dados_periodo_valido(app_e_dados):
    """/api/dados com periodo valido filtra corretamente o intervalo."""
    client, _ = app_e_dados
    resposta = client.get(
        "/api/dados",
        params={"ano_inicio": 2024, "semana_inicio": 2, "ano_fim": 2024, "semana_fim": 5},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["sucesso"] is True
    semanas = [ponto["semana"] for ponto in corpo["dados"]]
    assert semanas == [2, 3, 4, 5]


def test_dados_periodo_invertido(app_e_dados):
    """/api/dados com inicio posterior ao fim retorna 400 tratado, sem stack trace."""
    client, _ = app_e_dados
    resposta = client.get(
        "/api/dados",
        params={"ano_inicio": 2024, "semana_inicio": 8, "ano_fim": 2024, "semana_fim": 2},
    )
    assert resposta.status_code == 400
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["sucesso"] is False
    assert "posterior" in corpo["mensagem"].lower()
    assert "traceback" not in corpo["mensagem"].lower()


def test_dados_semana_fora_do_intervalo(app_e_dados):
    """/api/dados com semana invalida (>53) retorna 422 tratado."""
    client, _ = app_e_dados
    resposta = client.get("/api/dados", params={"ano_inicio": 2024, "semana_inicio": 99})
    assert resposta.status_code == 422
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["sucesso"] is False


def test_series_temporais(app_e_dados):
    """/api/series-temporais retorna a serie completa e apenas-treino menor."""
    client, dados_ref = app_e_dados
    completa = client.get("/api/series-temporais").json()
    assert completa["sucesso"] is True
    assert len(completa["dados"]) == dados_ref["total_pontos"]

    treino = client.get("/api/series-temporais", params={"apenas_treino": True}).json()
    assert len(treino["dados"]) == dados_ref["total_pontos"] - dados_ref["reservadas"]
    assert all(ponto["usar_no_treino"] for ponto in treino["dados"])


def test_metricas(app_e_dados):
    """/api/metricas retorna as metricas do modelo ativo lidas do banco."""
    client, _ = app_e_dados
    resposta = client.get("/api/metricas")
    assert resposta.status_code == 200
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["dados"]["nome_modelo"] == "random_forest"
    assert corpo["dados"]["mae"] == 5.1234
    assert corpo["dados"]["significativo"] is True


def test_previsoes_baseline(app_e_dados):
    """/api/previsoes usa baseline (sem .joblib) e retorna 6 semanas por padrao."""
    client, _ = app_e_dados
    resposta = client.get("/api/previsoes")
    assert resposta.status_code == 200
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["dados"]["origem_modelo"] == "baseline"
    assert corpo["dados"]["horizonte_semanas"] == 6
    assert len(corpo["dados"]["previsoes"]) == 6
    for previsao in corpo["dados"]["previsoes"]:
        assert previsao["casos_previstos"] >= 0


def test_unidades_notificacao(app_e_dados):
    """/api/unidades-notificacao documenta a pendencia de NM_UN_INTE."""
    client, _ = app_e_dados
    resposta = client.get("/api/unidades-notificacao")
    assert resposta.status_code == 200
    corpo = resposta.json()
    _validar_envelope(corpo)
    unidade = corpo["dados"][0]
    assert unidade["nm_un_inte"] is None
    assert unidade["fonte_populada"] is False


def test_dados_vazio(app_vazia):
    """/api/dados em banco vazio retorna lista vazia com mensagem clara (nao erro)."""
    resposta = app_vazia.get("/api/dados")
    assert resposta.status_code == 200
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["dados"] == []
    assert "nenhum" in corpo["mensagem"].lower()


def test_metricas_sem_modelo(app_vazia):
    """/api/metricas sem modelo ativo retorna 404 tratado no envelope padrao."""
    resposta = app_vazia.get("/api/metricas")
    assert resposta.status_code == 404
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["sucesso"] is False


def test_previsoes_sem_historico(app_vazia):
    """/api/previsoes sem historico retorna 503 tratado (previsao indisponivel)."""
    resposta = app_vazia.get("/api/previsoes")
    assert resposta.status_code == 503
    corpo = resposta.json()
    _validar_envelope(corpo)
    assert corpo["sucesso"] is False
