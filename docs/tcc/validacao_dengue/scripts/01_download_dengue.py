"""Download e padronizacao da serie semanal de Dengue - municipio de Sao Paulo.

EXPERIMENTO DE VALIDACAO DA METODOLOGIA (ISOLADO, NAO-INTEGRADO AO TCC).
O objeto oficial do TCC continua sendo Influenza A / municipio de Sao Paulo.
Este script obtem uma SEGUNDA serie temporal (Dengue, mesmo municipio) apenas
para reaplicar o MESMO pipeline preditivo e verificar, com honestidade, se o
metodo vence o baseline quando a serie e mais densa.

Fonte: InfoDengue (projeto FGV/Fiocruz) - API publica alertcity.
Endpoint (geocode 3550308 = municipio de Sao Paulo, IBGE):
    https://info.dengue.mat.br/api/alertcity?geocode=3550308&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2010&ey_end=2024

O script e IDEMPOTENTE: recria dados_brutos/dengue_sp_infodengue_2010_2024.csv
(baixa da API; se o download falhar e o CSV bruto ja existir, reaproveita o
arquivo local) e deriva a serie padronizada saida/serie_semanal_dengue.csv com
as colunas ANO,SEMANA_EPI,CASOS_PROXY, espelhando o formato de
data/processed/serie_temporal_semanal.csv do repo de referencia.

Uso (a partir de _exploracao_validacao_dengue/):
    .venv/bin/python scripts/01_download_dengue.py
"""

from __future__ import annotations

import csv
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Parametros da extracao (fonte, recorte e granularidade)
# ---------------------------------------------------------------------------
GEOCODE_SAO_PAULO = "3550308"  # codigo IBGE do municipio de Sao Paulo
DOENCA = "dengue"
ANO_INICIO = 2010
ANO_FIM = 2024
SEMANA_INICIO = 1
SEMANA_FIM = 52

URL_API = (
    "https://info.dengue.mat.br/api/alertcity"
    f"?geocode={GEOCODE_SAO_PAULO}"
    f"&disease={DOENCA}"
    f"&format=csv"
    f"&ew_start={SEMANA_INICIO}"
    f"&ew_end={SEMANA_FIM}"
    f"&ey_start={ANO_INICIO}"
    f"&ey_end={ANO_FIM}"
)

# Coluna da API usada como alvo (CASOS_PROXY). Documentacao da escolha:
# a API InfoDengue entrega 'casos' = numero de casos notificados/confirmados de
# dengue na semana epidemiologica (SE). Usamos 'casos' como proxy de incidencia
# semanal, espelhando o papel de CASOS_PROXY na serie oficial de Influenza.
COLUNA_ALVO = "casos"
# Coluna com a semana epidemiologica no formato AAAASS (ex.: 201552).
COLUNA_SE = "SE"

RAIZ = Path(__file__).resolve().parent.parent
CSV_BRUTO = RAIZ / "dados_brutos" / "dengue_sp_infodengue_2010_2024.csv"
CSV_SERIE = RAIZ / "saida" / "serie_semanal_dengue.csv"
FICHA = RAIZ / "dados_brutos" / "FICHA_RASTREABILIDADE.md"


def baixar_csv_bruto() -> str:
    """Baixa o CSV bruto da API do InfoDengue (idempotente).

    Retorna a data/hora da extracao (UTC, ISO-8601). Se o download falhar mas o
    CSV bruto local ja existir, reaproveita o arquivo e sinaliza no retorno.
    """
    CSV_BRUTO.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"[01] Baixando da API InfoDengue:\n     {URL_API}")
        requisicao = urllib.request.Request(
            URL_API, headers={"User-Agent": "validacao-metodologia-tcc/1.0"}
        )
        with urllib.request.urlopen(requisicao, timeout=120) as resposta:
            conteudo = resposta.read().decode("utf-8")
        if "SE" not in conteudo.splitlines()[0]:
            raise ValueError("Resposta da API sem cabecalho esperado (coluna SE).")
        CSV_BRUTO.write_text(conteudo, encoding="utf-8")
        extracao = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(f"[01] CSV bruto salvo em {CSV_BRUTO} ({extracao}).")
        return extracao
    except Exception as erro:  # noqa: BLE001 - rede pode falhar; nao queremos travar
        if CSV_BRUTO.exists():
            print(
                f"[01] AVISO: download falhou ({erro}); "
                f"reaproveitando CSV bruto local existente {CSV_BRUTO}."
            )
            carimbo = datetime.fromtimestamp(
                CSV_BRUTO.stat().st_mtime, tz=timezone.utc
            ).isoformat(timespec="seconds")
            return carimbo + " (CSV local reaproveitado; download indisponivel)"
        raise


def ler_registros() -> list[dict[str, str]]:
    """Le o CSV bruto e devolve as linhas como dicionarios."""
    with CSV_BRUTO.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def padronizar_serie(registros: list[dict[str, str]]) -> list[dict[str, int]]:
    """Converte os registros brutos na serie ANO,SEMANA_EPI,CASOS_PROXY.

    Deriva ANO dos 4 primeiros digitos de SE (AAAASS) e SEMANA_EPI dos 2 ultimos;
    CASOS_PROXY a partir da coluna 'casos'. Ordena cronologicamente (ano, semana).
    """
    serie: list[dict[str, int]] = []
    for linha in registros:
        se_bruto = str(linha[COLUNA_SE]).strip()
        if not se_bruto or len(se_bruto) < 6:
            continue
        ano = int(se_bruto[:4])
        semana = int(se_bruto[4:])
        casos_bruto = str(linha.get(COLUNA_ALVO, "")).strip()
        if casos_bruto == "":
            continue
        # 'casos' chega como inteiro; convertemos via float para tolerar "1850.0".
        casos = int(round(float(casos_bruto)))
        serie.append({"ANO": ano, "SEMANA_EPI": semana, "CASOS_PROXY": casos})

    serie.sort(key=lambda r: (r["ANO"], r["SEMANA_EPI"]))
    return serie


def salvar_serie(serie: list[dict[str, int]]) -> None:
    """Escreve a serie padronizada em saida/serie_semanal_dengue.csv."""
    CSV_SERIE.parent.mkdir(parents=True, exist_ok=True)
    with CSV_SERIE.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo, fieldnames=["ANO", "SEMANA_EPI", "CASOS_PROXY"]
        )
        escritor.writeheader()
        escritor.writerows(serie)
    print(f"[01] Serie padronizada salva em {CSV_SERIE} ({len(serie)} semanas).")


def resumir(serie: list[dict[str, int]]) -> dict[str, float]:
    """Calcula o resumo de volume/densidade da serie."""
    casos = [r["CASOS_PROXY"] for r in serie]
    zeros = sum(1 for c in casos if c == 0)
    return {
        "n_semanas": len(serie),
        "semanas_zero": zeros,
        "min": min(casos) if casos else 0,
        "max": max(casos) if casos else 0,
        "media": (sum(casos) / len(casos)) if casos else 0.0,
        "ano_min": serie[0]["ANO"] if serie else 0,
        "ano_max": serie[-1]["ANO"] if serie else 0,
    }


def escrever_ficha(extracao: str, resumo: dict[str, float]) -> None:
    """Gera a ficha de rastreabilidade da fonte (espirito do Manual Interno)."""
    conteudo = f"""# Ficha de rastreabilidade - serie de validacao (Dengue / Sao Paulo)

> **ENQUADRAMENTO.** Este e um **EXPERIMENTO DE VALIDACAO DA METODOLOGIA**
> preditiva do TCC aplicado a uma **segunda serie temporal (Dengue)**, de forma
> **ISOLADA e NAO-INTEGRADA** ao repositorio oficial. O objeto oficial do TCC
> permanece **Influenza A / municipio de Sao Paulo**. A Dengue entra apenas como
> serie de teste para checar se o metodo supera o baseline quando ha mais dados.

## Fonte dos dados

- **Projeto:** InfoDengue (FGV / Fundacao Oswaldo Cruz - Fiocruz).
- **API publica (endpoint alertcity):**
  `{URL_API}`
- **Parametros da consulta:**
  - `geocode = {GEOCODE_SAO_PAULO}` (codigo IBGE do municipio de Sao Paulo)
  - `disease = {DOENCA}`
  - `format = csv`
  - `ew_start = {SEMANA_INICIO}`, `ew_end = {SEMANA_FIM}` (semanas epidemiologicas)
  - `ey_start = {ANO_INICIO}`, `ey_end = {ANO_FIM}` (anos)
- **Data/hora da extracao (UTC):** {extracao}

## Recorte e granularidade

- **Doenca:** Dengue.
- **Recorte geografico:** municipio de Sao Paulo (IBGE {GEOCODE_SAO_PAULO}).
- **Granularidade:** semana epidemiologica (campo `SE`, formato AAAASS).
- **Periodo:** {ANO_INICIO} a {ANO_FIM} (observado: {int(resumo['ano_min'])} a {int(resumo['ano_max'])}).

## Alvo (CASOS_PROXY)

- Coluna da API usada como alvo: **`{COLUNA_ALVO}`** = numero de casos
  notificados/confirmados de dengue na semana. Escolhida por ser a contagem
  semanal direta de casos, espelhando o papel de `CASOS_PROXY` na serie oficial
  de Influenza. `ANO` e derivado dos 4 primeiros digitos de `SE`; `SEMANA_EPI`
  dos 2 ultimos.

## Arquivos gerados

- **CSV bruto (resposta da API):** `dados_brutos/dengue_sp_infodengue_2010_2024.csv`
- **Serie padronizada (ANO,SEMANA_EPI,CASOS_PROXY):** `saida/serie_semanal_dengue.csv`

## Volume e densidade (serie padronizada)

- **Semanas totais:** {int(resumo['n_semanas'])}
- **Semanas com zero casos:** {int(resumo['semanas_zero'])}
- **Minimo de CASOS_PROXY:** {int(resumo['min'])}
- **Maximo de CASOS_PROXY:** {int(resumo['max'])}
- **Media de CASOS_PROXY:** {resumo['media']:.2f}

Gerado automaticamente por `scripts/01_download_dengue.py` em {date.today().isoformat()}.
"""
    FICHA.write_text(conteudo, encoding="utf-8")
    print(f"[01] Ficha de rastreabilidade salva em {FICHA}.")


def main() -> None:
    """Executa download + padronizacao + ficha + resumo de densidade."""
    extracao = baixar_csv_bruto()
    registros = ler_registros()
    serie = padronizar_serie(registros)
    if not serie:
        print("[01] ERRO: serie vazia apos padronizacao.", file=sys.stderr)
        raise SystemExit(1)
    salvar_serie(serie)
    resumo = resumir(serie)
    escrever_ficha(extracao, resumo)

    print("\n[01] Resumo de volume/densidade (para comparar com a Influenza):")
    print(f"     semanas totais .......: {int(resumo['n_semanas'])}")
    print(f"     semanas com zero casos: {int(resumo['semanas_zero'])}")
    print(f"     CASOS_PROXY min/max ..: {int(resumo['min'])} / {int(resumo['max'])}")
    print(f"     CASOS_PROXY media ....: {resumo['media']:.2f}")
    print(f"     periodo ..............: {int(resumo['ano_min'])}-{int(resumo['ano_max'])}")


if __name__ == "__main__":
    main()
