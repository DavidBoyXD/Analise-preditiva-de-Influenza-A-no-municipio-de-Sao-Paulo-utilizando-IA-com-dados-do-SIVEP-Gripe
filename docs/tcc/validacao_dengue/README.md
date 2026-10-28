# Validacao da metodologia na serie de Dengue: artefatos-fonte (experimento isolado)

Esta pasta reune os artefatos que embasam o **experimento de validacao da
metodologia** preditiva do projeto, reaplicada a uma segunda serie temporal
(Dengue do municipio de Sao Paulo). O material da rastreabilidade a um
experimento conduzido fora do repositorio oficial e serve para que ele
sobreviva entre sessoes de trabalho.

> **Natureza do material.** Este e um **EXPERIMENTO DE VALIDACAO DA
> METODOLOGIA**, conduzido de forma **isolada e nao-integrada** ao fluxo
> principal do projeto. A **Dengue esta FORA do escopo oficial do TCC**, que
> permanece **Influenza A no municipio de Sao Paulo**. O experimento apenas
> reaplica a MESMA metodologia preditiva sobre uma segunda serie, para checar se
> o metodo supera o baseline quando ha mais dados. Nenhum modelo, banco de dados
> ou API oficiais do projeto foram reaproveitados: a serie de Dengue vem de
> **fonte publica independente** e o pipeline rodou em area separada. O
> experimento ja foi executado e aprovado; os arquivos aqui sao copias fieis dos
> resultados, sem reexecucao.

## Fonte dos dados

- **Projeto:** InfoDengue (FGV / Fundacao Oswaldo Cruz, Fiocruz).
- **API publica (endpoint alertcity):**
  [info.dengue.mat.br/api/alertcity](https://info.dengue.mat.br/api/alertcity?geocode=3550308&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2010&ey_end=2024)
- **Recorte geografico:** municipio de Sao Paulo (codigo IBGE 3550308).
- **Granularidade:** semana epidemiologica (campo `SE`, formato AAAASS).
- **Periodo:** 2010 a 2024.
- **Data da extracao (UTC):** 2026-10-28 (detalhes em
  [`FICHA_RASTREABILIDADE.md`](FICHA_RASTREABILIDADE.md)).

A serie padronizada tem **782 semanas**, **0 semanas com zero casos**, com
minimo de **38**, maximo de **85389** e media de **2188,86** casos por semana
(valores conforme a ficha de rastreabilidade). O alvo `CASOS_PROXY` espelha o
papel da contagem semanal usada na serie oficial de Influenza.

## Conteudo

| Arquivo | Descricao |
| ------- | --------- |
| [`RELATORIO_VALIDACAO_DENGUE.md`](RELATORIO_VALIDACAO_DENGUE.md) | Relatorio completo do experimento: objetivo, metodo, resultados, testes de significancia e conclusao de validacao. |
| [`metricas_dengue.csv`](metricas_dengue.csv) | Tabela de metricas por modelo (MAE, RMSE, MAPE, sMAPE, acerto direcional, Diebold-Mariano e Wilcoxon) em formato CSV. |
| [`metricas_dengue.md`](metricas_dengue.md) | A mesma tabela de metricas em Markdown, com enquadramento e glossario das colunas. |
| [`serie_semanal_dengue.csv`](serie_semanal_dengue.csv) | Serie semanal padronizada (ANO, SEMANA_EPI, CASOS_PROXY) usada no experimento. |
| [`grafico_real_x_previsto_dengue.png`](grafico_real_x_previsto_dengue.png) | Grafico comparando valores reais e previstos ao longo do horizonte avaliado. |
| [`FICHA_RASTREABILIDADE.md`](FICHA_RASTREABILIDADE.md) | Procedencia auditavel da fonte: URL da API, parametros, data/hora de extracao, recorte, alvo e densidade da serie. |
| [`dengue_sp_infodengue_2010_2024.csv`](dengue_sp_infodengue_2010_2024.csv) | CSV bruto da resposta da API InfoDengue, preservado para reprodutibilidade. |
| [`scripts/01_download_dengue.py`](scripts/01_download_dengue.py) | Script de download da serie de Dengue a partir da API publica do InfoDengue. |
| [`scripts/02_executar_pipeline_dengue.py`](scripts/02_executar_pipeline_dengue.py) | Script que reaplica a metodologia preditiva sobre a serie de Dengue e gera as metricas e o grafico. |

## Como reproduzir

A validacao cronologica foi feita com walk-forward (origem expansiva, horizonte
de 6 semanas) sobre a serie semanal de Dengue. Os scripts em `scripts/`
reaplicam a **mesma metodologia** da serie oficial, reutilizando os modulos de
`backend/app/model/` do proprio repositorio:

- `features.py`: construcao das variaveis preditoras.
- `metricas.py`: calculo das metricas de erro e acerto direcional.
- `preditor.py`: treino e previsao dos modelos.
- `significancia.py`: testes de Diebold-Mariano e Wilcoxon.
- `walk_forward.py`: orquestracao da validacao cronologica.

O fluxo original foi: `01_download_dengue.py` baixa a serie da API publica para
`dengue_sp_infodengue_2010_2024.csv` e gera a `FICHA_RASTREABILIDADE.md`; em
seguida `02_executar_pipeline_dengue.py` padroniza a serie, roda os modelos e
produz as metricas e o grafico. A execucao original ocorreu em uma area isolada,
fora deste repositorio, sem tocar no modelo, no banco nem na API oficiais do
projeto. Esta pasta preserva somente os resultados, para rastreabilidade
documental; nao e necessario reexecutar nada para consultar o experimento.
