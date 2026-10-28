# Ficha de rastreabilidade - serie de validacao (Dengue / Sao Paulo)

> **ENQUADRAMENTO.** Este e um **EXPERIMENTO DE VALIDACAO DA METODOLOGIA**
> preditiva do TCC aplicado a uma **segunda serie temporal (Dengue)**, de forma
> **ISOLADA e NAO-INTEGRADA** ao repositorio oficial. O objeto oficial do TCC
> permanece **Influenza A / municipio de Sao Paulo**. A Dengue entra apenas como
> serie de teste para checar se o metodo supera o baseline quando ha mais dados.

## Fonte dos dados

- **Projeto:** InfoDengue (FGV / Fundacao Oswaldo Cruz - Fiocruz).
- **API publica (endpoint alertcity):**
  `https://info.dengue.mat.br/api/alertcity?geocode=3550308&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2010&ey_end=2024`
- **Parametros da consulta:**
  - `geocode = 3550308` (codigo IBGE do municipio de Sao Paulo)
  - `disease = dengue`
  - `format = csv`
  - `ew_start = 1`, `ew_end = 52` (semanas epidemiologicas)
  - `ey_start = 2010`, `ey_end = 2024` (anos)
- **Data/hora da extracao (UTC):** 2026-10-28T00:56:47+00:00

## Recorte e granularidade

- **Doenca:** Dengue.
- **Recorte geografico:** municipio de Sao Paulo (IBGE 3550308).
- **Granularidade:** semana epidemiologica (campo `SE`, formato AAAASS).
- **Periodo:** 2010 a 2024 (observado: 2010 a 2024).

## Alvo (CASOS_PROXY)

- Coluna da API usada como alvo: **`casos`** = numero de casos
  notificados/confirmados de dengue na semana. Escolhida por ser a contagem
  semanal direta de casos, espelhando o papel de `CASOS_PROXY` na serie oficial
  de Influenza. `ANO` e derivado dos 4 primeiros digitos de `SE`; `SEMANA_EPI`
  dos 2 ultimos.

## Arquivos gerados

- **CSV bruto (resposta da API):** `dados_brutos/dengue_sp_infodengue_2010_2024.csv`
- **Serie padronizada (ANO,SEMANA_EPI,CASOS_PROXY):** `saida/serie_semanal_dengue.csv`

## Volume e densidade (serie padronizada)

- **Semanas totais:** 782
- **Semanas com zero casos:** 0
- **Minimo de CASOS_PROXY:** 38
- **Maximo de CASOS_PROXY:** 85389
- **Media de CASOS_PROXY:** 2188.86

Gerado automaticamente por `scripts/01_download_dengue.py` em 2026-10-28.
