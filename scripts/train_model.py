"""Treino e avaliacao do modelo preditivo de Influenza A (RF004).

Este script executa, de ponta a ponta, o experimento de modelagem descrito no
TCC (Manual Interno, secao do modelo preditivo):

1. carrega a serie temporal semanal (``data/processed/serie_temporal_semanal.csv``)
   e usa SOMENTE as semanas de treino (USAR_NO_TREINO=True; as 8 semanas mais
   recentes ficam reservadas por atraso de notificacao);
2. gera atributos temporais (defasagens, medias moveis, sazonalidade) - o MESMO
   gerador usado pelo backend em producao;
3. avalia, sob validacao cronologica walk-forward (origem expansiva, horizonte de
   6 semanas), quatro estrategias: baseline ingenuo, Random Forest, SARIMA e
   Prophet (quando instalado);
4. calcula MAE, RMSE, MAPE (com ressalva para semanas de zero casos) e acerto
   direcional de cada modelo;
5. aplica o teste de significancia Diebold-Mariano (principal) e Wilcoxon
   (alternativo) entre os erros do Random Forest e de cada comparador;
6. gera o grafico real x previsto em ``docs/grafico_real_x_previsto.png`` e a
   tabela comparativa de metricas (``docs/metricas_modelos.csv`` e ``.md``);
7. treina o Random Forest final com TODO o historico de treino e o salva
   versionado em ``models/modelo_rf_v1.joblib``;
8. registra o modelo e suas metricas no banco (SQLite de desenvolvimento) e
   regenera os INSERTs correspondentes em ``database/seed.sql``, de modo que a
   API (FEAT-003) sirva as metricas reais.

IMPORTANTE (honestidade metodologica): as metricas reportadas sao as
efetivamente obtidas. A serie e curta e esparsa (proxy PCR_FLUASU, hiato
2020-2021); se o Random Forest NAO superar o baseline, isso e documentado tal
como observado - o modelo nao e forcado a "vencer".

Uso (a partir da raiz do repositorio):
    uv --directory backend run python ../scripts/train_model.py
"""

from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl_utils import (
    caminho_serie_semanal,
    configurar_log,
    raiz_repositorio,
)  # noqa: E402

# O pacote do modelo vive no backend (app.model); garante o import.
sys.path.insert(0, str(raiz_repositorio() / "backend"))

from app.model import (  # noqa: E402
    CONFIG_ATRIBUTOS_PADRAO,
    PreditorRandomForest,
    calcular_metricas,
    diebold_mariano,
    wilcoxon_erros,
)
from app.model.walk_forward import (  # noqa: E402
    avaliar_walk_forward,
    preditor_baseline_sazonal,
    preditor_prophet,
    preditor_random_forest,
    preditor_sarima,
)

LOGGER = configurar_log("train_model")

# Configuracao do experimento -------------------------------------------------
HORIZONTE_PREVISAO = 6
JANELA_MINIMA = 60  # semanas de historico antes da primeira origem walk-forward
NOME_MODELO = "random_forest"
VERSAO_MODELO = "1"
ARQUIVO_MODELO = "modelo_rf_v1.joblib"

PARAMS_RANDOM_FOREST = {
    "n_estimators": 300,
    "max_depth": None,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1,
}
ORDEM_SARIMA = (1, 0, 1)
ORDEM_SAZONAL_SARIMA = (1, 0, 0, 52)


def carregar_serie_treino() -> tuple[list[float], list[int], list[int]]:
    """Le a serie semanal e devolve (valores, semanas, anos) apenas do treino."""
    caminho = caminho_serie_semanal()
    if not caminho.exists():
        raise FileNotFoundError(
            f"Serie temporal nao encontrada em {caminho}. Rode o ETL antes (FEAT-001)."
        )
    valores: list[float] = []
    semanas: list[int] = []
    anos: list[int] = []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if str(linha["USAR_NO_TREINO"]).strip().lower() != "true":
                continue
            valores.append(float(linha["CASOS_PROXY"]))
            semanas.append(int(linha["SEMANA_EPI"]))
            anos.append(int(linha["ANO"]))
    LOGGER.info(
        "Serie de treino carregada: %d semanas (USAR_NO_TREINO=True).", len(valores)
    )
    return valores, semanas, anos


def _prophet_disponivel() -> bool:
    """Indica se o Prophet esta instalado no ambiente."""
    try:
        import prophet  # noqa: F401

        return True
    except Exception:
        return False


def avaliar_modelos(valores: list[float], semanas: list[int]) -> dict[str, dict]:
    """Avalia todos os modelos sob o mesmo protocolo walk-forward.

    Returns:
        Dicionario nome_modelo -> {resultado, metricas} com os pares reais e
        previstos e as metricas calculadas.
    """
    preditores: dict[str, object] = {
        "baseline": preditor_baseline_sazonal(),
        "random_forest": preditor_random_forest(
            PARAMS_RANDOM_FOREST, CONFIG_ATRIBUTOS_PADRAO
        ),
        "sarima": preditor_sarima(ORDEM_SARIMA, ORDEM_SAZONAL_SARIMA),
    }
    if _prophet_disponivel():
        preditores["prophet"] = preditor_prophet()
        LOGGER.info("Prophet disponivel: incluido como comparador.")
    else:
        LOGGER.warning(
            "Prophet indisponivel: mantendo baseline + SARIMA como comparadores."
        )

    avaliacoes: dict[str, dict] = {}
    for nome, preditor in preditores.items():
        LOGGER.info(
            "Avaliando '%s' sob walk-forward (horizonte=%d)...",
            nome,
            HORIZONTE_PREVISAO,
        )
        resultado = avaliar_walk_forward(
            valores, semanas, preditor, HORIZONTE_PREVISAO, JANELA_MINIMA
        )
        metricas = calcular_metricas(resultado.reais, resultado.previstos)
        avaliacoes[nome] = {"resultado": resultado, "metricas": metricas}
        LOGGER.info(
            "'%s': MAE=%.3f RMSE=%.3f sMAPE=%.2f%% acerto_dir=%.3f (%d blocos, %d pontos)",
            nome,
            metricas["mae"],
            metricas["rmse"],
            metricas["smape"],
            metricas["acerto_direcional"],
            resultado.n_blocos,
            len(resultado.reais),
        )
    return avaliacoes


def testar_significancia(avaliacoes: dict[str, dict]) -> dict[str, dict]:
    """Aplica Diebold-Mariano e Wilcoxon entre o RF e cada comparador."""
    rf = avaliacoes["random_forest"]["resultado"]
    erros_rf = [r - p for r, p in zip(rf.reais, rf.previstos)]

    testes: dict[str, dict] = {}
    for nome, dados in avaliacoes.items():
        if nome == "random_forest":
            continue
        comp = dados["resultado"]
        erros_comp = [r - p for r, p in zip(comp.reais, comp.previstos)]
        tamanho = min(len(erros_rf), len(erros_comp))
        dm = diebold_mariano(
            erros_rf[:tamanho], erros_comp[:tamanho], horizonte=HORIZONTE_PREVISAO
        )
        wx = wilcoxon_erros(erros_rf[:tamanho], erros_comp[:tamanho])
        testes[nome] = {"diebold_mariano": dm, "wilcoxon": wx}
        LOGGER.info("RF vs %s | %s | %s", nome, dm.detalhe, wx.detalhe)
    return testes


def gerar_grafico(
    valores: list[float],
    semanas: list[int],
    anos: list[int],
    avaliacoes: dict[str, dict],
) -> Path:
    """Gera o grafico real x previsto (ultimo bloco de teste) em docs/."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rf = avaliacoes["random_forest"]["resultado"]
    n_mostrar = min(len(rf.reais), 52)
    reais = rf.reais[-n_mostrar:]
    eixo = list(range(len(reais)))

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(eixo, reais, label="Real (casos-proxy)", color="#222222", linewidth=2)
    cores = {
        "random_forest": "#c0392b",
        "baseline": "#7f8c8d",
        "sarima": "#2980b9",
        "prophet": "#27ae60",
    }
    for nome, dados in avaliacoes.items():
        previstos = dados["resultado"].previstos[-n_mostrar:]
        ax.plot(
            eixo,
            previstos,
            label=f"Previsto - {nome}",
            color=cores.get(nome, None),
            linestyle="--",
            linewidth=1.3,
        )
    ax.set_title(
        "Real x Previsto - casos-proxy de Influenza A (Sao Paulo)\n"
        "validacao cronologica walk-forward, horizonte de 6 semanas"
    )
    ax.set_xlabel("Semanas do periodo de teste (walk-forward concatenado)")
    ax.set_ylabel("Casos-proxy semanais")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    destino = raiz_repositorio() / "docs" / "grafico_real_x_previsto.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=120)
    plt.close(fig)
    LOGGER.info("Grafico real x previsto salvo em %s.", destino)
    return destino


def salvar_tabela_metricas(
    avaliacoes: dict[str, dict], testes: dict[str, dict]
) -> tuple[Path, Path]:
    """Salva a tabela comparativa de metricas em CSV e Markdown em docs/."""
    docs = raiz_repositorio() / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    caminho_csv = docs / "metricas_modelos.csv"
    caminho_md = docs / "metricas_modelos.md"

    colunas = [
        "modelo",
        "mae",
        "rmse",
        "mape_semanas_positivas",
        "smape",
        "acerto_direcional",
        "semanas_ignoradas_mape",
        "dm_estatistica",
        "dm_p_valor",
        "dm_significativo",
        "wilcoxon_p_valor",
        "wilcoxon_significativo",
    ]

    def _linha(nome: str) -> dict[str, object]:
        m = avaliacoes[nome]["metricas"]
        linha: dict[str, object] = {
            "modelo": nome,
            "mae": round(m["mae"], 4),
            "rmse": round(m["rmse"], 4),
            "mape_semanas_positivas": (
                round(m["mape"], 4) if m["mape"] == m["mape"] else "indefinido"
            ),
            "smape": round(m["smape"], 4),
            "acerto_direcional": round(m["acerto_direcional"], 4),
            "semanas_ignoradas_mape": int(m["semanas_ignoradas_mape"]),
            "dm_estatistica": "",
            "dm_p_valor": "",
            "dm_significativo": "",
            "wilcoxon_p_valor": "",
            "wilcoxon_significativo": "",
        }
        if nome in testes:
            dm = testes[nome]["diebold_mariano"]
            wx = testes[nome]["wilcoxon"]
            linha["dm_estatistica"] = round(dm.estatistica, 4)
            linha["dm_p_valor"] = round(dm.p_valor, 4)
            linha["dm_significativo"] = "sim" if dm.significativo else "nao"
            linha["wilcoxon_p_valor"] = (
                round(wx.p_valor, 4) if wx.p_valor == wx.p_valor else "indisponivel"
            )
            linha["wilcoxon_significativo"] = "sim" if wx.significativo else "nao"
        elif nome == "random_forest":
            linha["dm_estatistica"] = "(referencia)"
        return linha

    linhas = [_linha(nome) for nome in avaliacoes]

    with caminho_csv.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)

    cabecalho = "| " + " | ".join(colunas) + " |"
    separador = "| " + " | ".join("---" for _ in colunas) + " |"
    corpo = [
        "| " + " | ".join(str(linha[c]) for c in colunas) + " |" for linha in linhas
    ]
    conteudo_md = (
        "# Tabela comparativa de metricas dos modelos (RF004)\n\n"
        "Metricas obtidas sob validacao cronologica walk-forward (origem expansiva, "
        "horizonte de 6 semanas) sobre a serie de treino do municipio de Sao Paulo.\n\n"
        "- **mae / rmse**: erro medio absoluto e raiz do erro quadratico medio.\n"
        "- **mape_semanas_positivas**: MAPE classico calculado apenas em semanas com "
        "real > 0 (evita divisao por zero); **semanas_ignoradas_mape** conta as semanas "
        "de zero casos descartadas.\n"
        "- **smape**: MAPE simetrico, finito mesmo com zeros.\n"
        "- **acerto_direcional**: proporcao de acerto na direcao (subida/descida).\n"
        "- **dm_**: teste de Diebold-Mariano do RF frente ao comparador (perda quadratica). "
        "DM < 0 favorece o Random Forest.\n"
        "- **wilcoxon_**: teste nao parametrico de Wilcoxon sobre os erros absolutos.\n\n"
        + cabecalho
        + "\n"
        + separador
        + "\n"
        + "\n".join(corpo)
        + "\n"
    )
    caminho_md.write_text(conteudo_md, encoding="utf-8")
    LOGGER.info("Tabela de metricas salva em %s e %s.", caminho_csv, caminho_md)
    return caminho_csv, caminho_md


def treinar_modelo_final(
    valores: list[float], semanas: list[int]
) -> PreditorRandomForest:
    """Treina o Random Forest final com todo o historico de treino."""
    from sklearn.ensemble import RandomForestRegressor

    from app.model.features import gerar_atributos_serie

    X, y, _ = gerar_atributos_serie(valores, semanas, CONFIG_ATRIBUTOS_PADRAO)
    modelo = RandomForestRegressor(**PARAMS_RANDOM_FOREST)
    modelo.fit(X, y)
    LOGGER.info(
        "Random Forest final treinado com %d observacoes supervisionadas.", len(X)
    )
    return PreditorRandomForest(
        modelo=modelo,
        config=CONFIG_ATRIBUTOS_PADRAO,
        nome=NOME_MODELO,
        versao=VERSAO_MODELO,
    )


def salvar_modelo(preditor: PreditorRandomForest) -> Path:
    """Salva o modelo versionado em models/*.joblib."""
    import joblib

    destino_dir = raiz_repositorio() / "models"
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / ARQUIVO_MODELO
    joblib.dump(preditor, destino)
    LOGGER.info("Modelo salvo em %s.", destino)
    return destino


def registrar_no_banco(
    avaliacoes: dict[str, dict],
    testes: dict[str, dict],
    caminho_modelo: Path,
    anos: list[int],
    semanas: list[int],
) -> None:
    """Registra o modelo ativo e suas metricas no banco (SQLite de desenvolvimento).

    Reutiliza os modelos ORM e a sessao do backend (FEAT-003). As metricas
    gravadas sao as do Random Forest; o teste de significancia registrado e o
    Diebold-Mariano frente ao baseline (comparador de referencia obrigatorio).
    """
    from app.db import Base, SessionLocal, engine
    from app.models import MetricaModelo, ModeloPreditivo

    Base.metadata.create_all(bind=engine)

    m = avaliacoes["random_forest"]["metricas"]
    dm_baseline = testes.get("baseline", {}).get("diebold_mariano")
    base_inicio = date(min(anos), 1, 1)
    base_fim = date(max(anos), 12, 28)

    caminho_relativo = str(caminho_modelo.relative_to(raiz_repositorio()))

    with SessionLocal() as sessao:
        # Desativa modelos anteriores e remove um registro homonimo desta versao.
        for existente in sessao.query(ModeloPreditivo).all():
            existente.ativo = False
        anterior = (
            sessao.query(ModeloPreditivo)
            .filter_by(nome_modelo=NOME_MODELO, versao=VERSAO_MODELO)
            .one_or_none()
        )
        if anterior is not None:
            sessao.query(MetricaModelo).filter_by(id_modelo=anterior.id_modelo).delete()
            sessao.delete(anterior)
            sessao.flush()

        modelo = ModeloPreditivo(
            nome_modelo=NOME_MODELO,
            algoritmo="RandomForestRegressor (scikit-learn) com atributos temporais",
            versao=VERSAO_MODELO,
            caminho_modelo_serializado=caminho_relativo,
            janela_historica_semanas=CONFIG_ATRIBUTOS_PADRAO.historico_minimo,
            horizonte_previsao_semanas=HORIZONTE_PREVISAO,
            data_treinamento=datetime.now(),
            status_modelo="ativo",
            ativo=True,
            observacao=(
                "Modelo principal do TCC (RF004). Metricas obtidas sob walk-forward "
                "(origem expansiva, horizonte de 6 semanas). Serie curta/esparsa - ver "
                "docs/documentacao_modelo.md e docs/relatorio_qualidade_dados.md."
            ),
        )
        sessao.add(modelo)
        sessao.flush()

        significativo = dm_baseline.significativo if dm_baseline else None
        estatistica = dm_baseline.estatistica if dm_baseline else None
        p_valor = dm_baseline.p_valor if dm_baseline else None

        sessao.add(
            MetricaModelo(
                id_modelo=modelo.id_modelo,
                mae=round(m["mae"], 4),
                rmse=round(m["rmse"], 4),
                mape=(round(m["mape"], 4) if m["mape"] == m["mape"] else None),
                acerto_direcional=round(m["acerto_direcional"], 4),
                teste_significancia="Diebold-Mariano (RF vs baseline)",
                estatistica_teste=(
                    round(estatistica, 6) if estatistica is not None else None
                ),
                p_valor=(round(p_valor, 6) if p_valor is not None else None),
                significativo=significativo,
                base_teste_inicio=base_inicio,
                base_teste_fim=base_fim,
                observacao=(
                    f"sMAPE={round(m['smape'], 2)}%; MAPE classico sobre semanas com real>0 "
                    f"({int(m['semanas_ignoradas_mape'])} semanas de zero casos ignoradas)."
                ),
            )
        )
        sessao.commit()
        LOGGER.info(
            "Modelo (id=%d) e metricas registrados no banco em %s.",
            modelo.id_modelo,
            engine.url,
        )


def _fmt(valor: float) -> str:
    """Formata um float para o SQL do seed (ou NULL)."""
    if valor is None or valor != valor:  # None ou NaN
        return "NULL"
    return f"{valor:.4f}"


def atualizar_seed_sql(
    avaliacoes: dict[str, dict],
    testes: dict[str, dict],
    caminho_modelo: Path,
    anos: list[int],
) -> None:
    """Acrescenta INSERTs de modelo_preditivo/metrica_modelo ao database/seed.sql.

    O bloco e delimitado por marcadores para poder ser regenerado sem duplicar.
    Assim, ao aplicar o schema + seed em um PostgreSQL limpo, a API tambem serve
    as metricas reais do modelo treinado.
    """
    m = avaliacoes["random_forest"]["metricas"]
    dm = testes.get("baseline", {}).get("diebold_mariano")
    caminho_relativo = str(caminho_modelo.relative_to(raiz_repositorio()))
    inicio = f"{min(anos)}-01-01"
    fim = f"{max(anos)}-12-28"

    marcador_ini = (
        "-- >>> INICIO BLOCO MODELO PREDITIVO (gerado por scripts/train_model.py)"
    )
    marcador_fim = "-- <<< FIM BLOCO MODELO PREDITIVO"

    significativo = "NULL"
    estatistica = "NULL"
    p_valor = "NULL"
    if dm is not None:
        significativo = "TRUE" if dm.significativo else "FALSE"
        estatistica = f"{dm.estatistica:.6f}"
        p_valor = f"{dm.p_valor:.6f}"

    mape_val = _fmt(m["mape"])
    bloco = (
        f"{marcador_ini}\n"
        "-- Modelo principal (RF004) e suas metricas reais obtidas sob walk-forward.\n"
        "-- Metricas honestas: ver docs/documentacao_modelo.md.\n"
        "INSERT INTO modelo_preditivo (id_modelo, nome_modelo, algoritmo, versao, "
        "caminho_modelo_serializado, janela_historica_semanas, horizonte_previsao_semanas, "
        "data_treinamento, status_modelo, ativo, observacao) VALUES\n"
        f"    (1, '{NOME_MODELO}', "
        "'RandomForestRegressor (scikit-learn) com atributos temporais', "
        f"'{VERSAO_MODELO}', '{caminho_relativo}', "
        f"{CONFIG_ATRIBUTOS_PADRAO.historico_minimo}, {HORIZONTE_PREVISAO}, "
        "CURRENT_TIMESTAMP, 'ativo', TRUE, "
        "'Modelo principal do TCC (RF004) - metricas reais sob walk-forward de 6 semanas.');\n"
        "INSERT INTO metrica_modelo (id_metrica, id_modelo, mae, rmse, mape, "
        "acerto_direcional, teste_significancia, estatistica_teste, p_valor, significativo, "
        "base_teste_inicio, base_teste_fim, observacao) VALUES\n"
        f"    (1, 1, {_fmt(m['mae'])}, {_fmt(m['rmse'])}, {mape_val}, "
        f"{_fmt(m['acerto_direcional'])}, 'Diebold-Mariano (RF vs baseline)', "
        f"{estatistica}, {p_valor}, {significativo}, "
        f"'{inicio}', '{fim}', "
        f"'sMAPE={m['smape']:.2f}%; MAPE apenas em semanas com real>0 "
        f"({int(m['semanas_ignoradas_mape'])} semanas de zero ignoradas).');\n"
        f"{marcador_fim}\n"
    )

    caminho_seed = raiz_repositorio() / "database" / "seed.sql"
    conteudo = caminho_seed.read_text(encoding="utf-8") if caminho_seed.exists() else ""
    if marcador_ini in conteudo and marcador_fim in conteudo:
        antes = conteudo.split(marcador_ini)[0].rstrip("\n")
        depois = conteudo.split(marcador_fim, 1)[1].lstrip("\n")
        conteudo = antes + "\n\n" + bloco + ("\n" + depois if depois else "")
    else:
        conteudo = conteudo.rstrip("\n") + "\n\n" + bloco
    caminho_seed.write_text(conteudo, encoding="utf-8")
    LOGGER.info("Bloco de modelo/metricas atualizado em %s.", caminho_seed)


def main() -> None:
    """Executa o experimento completo de modelagem (RF004)."""
    valores, semanas, anos = carregar_serie_treino()
    avaliacoes = avaliar_modelos(valores, semanas)
    testes = testar_significancia(avaliacoes)
    gerar_grafico(valores, semanas, anos, avaliacoes)
    salvar_tabela_metricas(avaliacoes, testes)
    preditor = treinar_modelo_final(valores, semanas)
    caminho_modelo = salvar_modelo(preditor)
    registrar_no_banco(avaliacoes, testes, caminho_modelo, anos, semanas)
    atualizar_seed_sql(avaliacoes, testes, caminho_modelo, anos)

    # Resumo honesto no log.
    mae_rf = avaliacoes["random_forest"]["metricas"]["mae"]
    mae_base = avaliacoes["baseline"]["metricas"]["mae"]
    if mae_rf < mae_base:
        LOGGER.info(
            "RESUMO: Random Forest com MAE menor que o baseline (%.3f < %.3f).",
            mae_rf,
            mae_base,
        )
    else:
        LOGGER.warning(
            "RESUMO HONESTO: Random Forest NAO superou o baseline em MAE (%.3f >= %.3f). "
            "Documentado em docs/documentacao_modelo.md.",
            mae_rf,
            mae_base,
        )
    LOGGER.info("Treino e avaliacao concluidos.")


if __name__ == "__main__":
    main()
