"""Experimento ISOLADO de validacao da metodologia preditiva (serie de Dengue).

ATENCAO (enquadramento): este script NAO faz parte do objeto oficial do TCC
(que continua Influenza A / municipio de Sao Paulo). Ele e um EXPERIMENTO DE
VALIDACAO DA METODOLOGIA em uma SEGUNDA serie temporal (Dengue, municipio de
Sao Paulo, dados publicos do InfoDengue), ISOLADO e NAO-INTEGRADO ao repo. O
objetivo e verificar, com honestidade, se o mesmo pipeline vence o baseline com
significancia quando a serie e mais densa.

Ele ESPELHA EXATAMENTE a logica de ``_repo_ref/scripts/train_model.py`` nas
funcoes ``avaliar_modelos``, ``testar_significancia``, ``salvar_tabela_metricas``
e ``gerar_grafico``, usando os MESMOS parametros do experimento oficial e os
MESMOS modulos do pipeline (copiados em ``pipeline_ref/``, sem alterar a logica).

Diferencas deliberadas e justificadas em relacao ao train_model.py original:
    * le a serie de Dengue (``saida/serie_semanal_dengue.csv``, colunas
      ANO,SEMANA_EPI,CASOS_PROXY) em vez da serie oficial de Influenza;
    * grava os artefatos em ``saida/`` (NAO em ``docs/`` do repo de referencia);
    * NAO registra nada em banco e NAO mexe em ``database/seed.sql`` nem salva
      modelo final serializado: essas etapas do train_model.py sao parte da
      integracao do TCC e NAO se aplicam a este experimento isolado.

Uso (a partir de /projects/sandbox/_exploracao_validacao_dengue):
    .venv/bin/python scripts/02_executar_pipeline_dengue.py
"""

from __future__ import annotations

import csv
import logging
import os
import sys
from pathlib import Path

# matplotlib em ambiente sem display / sem /root/.config gravavel.
os.environ.setdefault("MPLCONFIGDIR", "/tmp")

RAIZ = Path(__file__).resolve().parent.parent
PIPELINE_REF = RAIZ / "pipeline_ref"
SAIDA = RAIZ / "saida"
SERIE = SAIDA / "serie_semanal_dengue.csv"

# Importa os modulos do pipeline copiado (sem alterar a logica).
sys.path.insert(0, str(PIPELINE_REF))

from features import CONFIG_ATRIBUTOS_PADRAO  # noqa: E402
from metricas import calcular_metricas  # noqa: E402
from significancia import diebold_mariano, wilcoxon_erros  # noqa: E402
from walk_forward import (  # noqa: E402
    avaliar_walk_forward,
    preditor_baseline_sazonal,
    preditor_prophet,
    preditor_random_forest,
    preditor_sarima,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("pipeline_dengue")

# Configuracao do experimento (IDENTICA ao experimento oficial de Influenza) ---
HORIZONTE_PREVISAO = 6
JANELA_MINIMA = 60  # semanas de historico antes da primeira origem walk-forward

PARAMS_RANDOM_FOREST = {
    "n_estimators": 300,
    "max_depth": None,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1,
}
ORDEM_SARIMA = (1, 0, 1)
ORDEM_SAZONAL_SARIMA = (1, 0, 0, 52)


def carregar_serie_dengue() -> tuple[list[float], list[int], list[int]]:
    """Le a serie semanal de Dengue e devolve (valores, semanas, anos).

    A serie ja esta tratada e ordenada cronologicamente (FEAT-001). Diferente da
    serie oficial de Influenza, aqui NAO ha coluna USAR_NO_TREINO: toda a serie e
    usada no experimento de validacao walk-forward.
    """
    if not SERIE.exists():
        raise FileNotFoundError(
            f"Serie de Dengue nao encontrada em {SERIE}. Rode scripts/01_download_dengue.py."
        )
    valores: list[float] = []
    semanas: list[int] = []
    anos: list[int] = []
    with SERIE.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            valores.append(float(linha["CASOS_PROXY"]))
            semanas.append(int(linha["SEMANA_EPI"]))
            anos.append(int(linha["ANO"]))
    LOGGER.info("Serie de Dengue carregada: %d semanas.", len(valores))
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

    Espelha avaliar_modelos de train_model.py: baseline, random_forest, sarima e
    prophet (quando instalado), com os MESMOS parametros.
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
    """Aplica Diebold-Mariano e Wilcoxon entre o RF e cada comparador.

    Espelha testar_significancia de train_model.py: RF = modelo 1; erros =
    real - previsto.
    """
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
    """Gera o grafico real x previsto (ultimo bloco de teste) em saida/.

    Espelha gerar_grafico de train_model.py, ajustando apenas titulos/textos para
    deixar claro que e Dengue / municipio de Sao Paulo / experimento de validacao,
    e o destino para saida/.
    """
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
        "Real x Previsto - casos-proxy de Dengue (municipio de Sao Paulo)\n"
        "EXPERIMENTO DE VALIDACAO DA METODOLOGIA (isolado, nao-integrado ao TCC)\n"
        "validacao cronologica walk-forward, horizonte de 6 semanas"
    )
    ax.set_xlabel("Semanas do periodo de teste (walk-forward concatenado)")
    ax.set_ylabel("Casos-proxy semanais")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    destino = SAIDA / "grafico_real_x_previsto_dengue.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=120)
    plt.close(fig)
    LOGGER.info("Grafico real x previsto salvo em %s.", destino)
    return destino


def salvar_tabela_metricas(
    avaliacoes: dict[str, dict], testes: dict[str, dict]
) -> tuple[Path, Path]:
    """Salva a tabela comparativa de metricas em CSV e Markdown em saida/.

    Espelha salvar_tabela_metricas de train_model.py: MESMAS colunas; destino em
    saida/ (metricas_dengue.csv e metricas_dengue.md).
    """
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho_csv = SAIDA / "metricas_dengue.csv"
    caminho_md = SAIDA / "metricas_dengue.md"

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
        "# Tabela comparativa de metricas dos modelos - EXPERIMENTO DE VALIDACAO (Dengue)\n\n"
        "**Enquadramento:** experimento ISOLADO e NAO-INTEGRADO ao TCC. A Dengue NAO faz "
        "parte do objeto oficial do projeto (que continua Influenza A / municipio de Sao "
        "Paulo). Reaplicacao da MESMA metodologia sobre uma segunda serie para validacao.\n\n"
        "Metricas obtidas sob validacao cronologica walk-forward (origem expansiva, "
        "horizonte de 6 semanas) sobre a serie semanal de Dengue do municipio de Sao Paulo "
        "(InfoDengue, 2010-2024).\n\n"
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


def main() -> None:
    """Executa o experimento de validacao da metodologia sobre a serie de Dengue."""
    valores, semanas, anos = carregar_serie_dengue()
    avaliacoes = avaliar_modelos(valores, semanas)
    testes = testar_significancia(avaliacoes)
    gerar_grafico(valores, semanas, anos, avaliacoes)
    salvar_tabela_metricas(avaliacoes, testes)

    # Resumo honesto no log (NAO forcar o RF a "vencer").
    mae_rf = avaliacoes["random_forest"]["metricas"]["mae"]
    mae_base = avaliacoes["baseline"]["metricas"]["mae"]
    dm_base = testes.get("baseline", {}).get("diebold_mariano")
    if mae_rf < mae_base:
        LOGGER.info(
            "RESUMO: Random Forest com MAE menor que o baseline (%.4f < %.4f).",
            mae_rf,
            mae_base,
        )
    else:
        LOGGER.warning(
            "RESUMO HONESTO: Random Forest NAO superou o baseline em MAE (%.4f >= %.4f).",
            mae_rf,
            mae_base,
        )
    if dm_base is not None:
        LOGGER.info(
            "DM RF vs baseline: estatistica=%.4f p=%.4f significativo=%s",
            dm_base.estatistica,
            dm_base.p_valor,
            "sim" if dm_base.significativo else "nao",
        )
    LOGGER.info("Experimento de validacao (Dengue) concluido.")


if __name__ == "__main__":
    main()
