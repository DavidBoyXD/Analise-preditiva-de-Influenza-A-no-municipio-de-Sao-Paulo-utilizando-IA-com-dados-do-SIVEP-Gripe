# Dicionario de Dados e Ficha de Rastreabilidade

Documento referente ao modulo de ETL (RF003) do TCC "Analise preditiva de
Influenza A no municipio de Sao Paulo utilizando IA com dados do SIVEP-Gripe".
Protótipo academico - nao constitui ferramenta oficial de vigilancia.

## 1. Ficha de rastreabilidade da base

| Item | Valor |
|------|-------|
| Fonte | SIVEP-Gripe / SINAN (DATASUS) - dados publicos de SRAG |
| Recorte geografico | Municipio de Sao Paulo capital (CO_MUN_RES = 355030) |
| Periodo coberto | 2009 a 2019 e 2022 a 2026 (anos 2020-2021 ausentes na fonte consolidada) |
| Arquivo original (fonte) | `Documentos_Para_Desenv_TCC/Dados consolidados e padronizados 2009 a 2019 e 2022 a 2026.csv` |
| Arquivo bruto preservado | `data/raw/sivep_gripe_consolidado_2009_2026.csv` (copia fiel, nao alterada) |
| Encoding | UTF-8 com BOM (`utf-8-sig`) |
| Separador | `;` (ponto e virgula) |
| Total de registros na fonte | 48.775 linhas de dados (+ 1 cabecalho) |
| Registros do municipio de SP | 13.139 |
| Arquivo tratado | `data/processed/base_tratada.csv` |
| Serie temporal semanal | `data/processed/serie_temporal_semanal.csv` |
| Data de extracao/copia | Copia realizada durante a implementacao do modulo de ETL (FEAT-001) |

> A base bruta em `data/raw/` e preservada e nunca sobrescrita (regra do Manual
> Interno). Os artefatos tratados sao sempre regeraveis a partir dela.

## 2. Comandos de regeneracao

Os scripts ficam em `/scripts` (raiz do repositorio) e o ambiente Python em
`/backend`. Rodar a partir da raiz do repositorio:

```bash
uv --directory backend run python ../scripts/etl_coleta.py
uv --directory backend run python ../scripts/etl_tratamento.py
```

Os scripts resolvem os caminhos de forma robusta a partir da raiz do repositorio
(ver `scripts/etl_utils.py`), independentemente do diretorio de trabalho.

## 3. Dicionario das colunas da base bruta (fonte)

| Coluna | Descricao | Observacao |
|--------|-----------|------------|
| CS_SEXO | Sexo do paciente (M/F/I) | - |
| CS_RACA | Raca/cor (codigo) | 261 ausentes em SP |
| NU_IDADE | Idade | - |
| SEM_PRI | Semana epidemiologica dos primeiros sintomas (1-52/53) | Semana oficial da fonte |
| DT_SIN_PRI | Data dos primeiros sintomas | Formato DD/MM/AAAA |
| SG_UF | Unidade da Federacao de residencia | SP no recorte |
| CO_MUN_RES | Codigo IBGE do municipio de residencia | 355030 = Sao Paulo capital |
| ID_MN_RESI | Nome do municipio de residencia | - |
| CS_ZONA | Zona de residencia (urbana/rural/periurbana) | 7.319 ausentes em SP |
| PCR_FLUASU | Subtipo de Influenza A por PCR (6 categorias antigas) | Base da regra de proxy |
| FLUASU_OUT | Subtipo em texto livre | 13.006 ausentes em SP |

## 4. Colunas derivadas na base tratada

| Coluna | Descricao |
|--------|-----------|
| ANO | Ano derivado de DT_SIN_PRI (DD/MM/AAAA) |
| SEMANA_EPI | Semana epidemiologica (a partir de SEM_PRI) |
| CASO_PROXY_INFLUENZA_A | 1 se PCR_FLUASU preenchido (caso-proxy), 0 caso contrario |

## 5. Colunas da serie temporal semanal

| Coluna | Descricao |
|--------|-----------|
| ANO | Ano epidemiologico |
| SEMANA_EPI | Semana epidemiologica (1-52) |
| CASOS_PROXY | Contagem de casos-proxy de Influenza A na semana (0 quando sem casos) |
| RESERVADA_ATRASO_NOTIFICACAO | `True` para as 8 semanas mais recentes (reservadas) |
| USAR_NO_TREINO | `False` para as semanas reservadas; `True` caso contrario |

## 6. Limitacoes de dados

As limitacoes (campos de confirmacao laboratorial ausentes, regra de proxy sobre
PCR_FLUASU, ausencia de NM_UN_INTE, atraso de notificacao, subnotificacao,
sazonalidade e o hiato 2020-2021) estao detalhadas e amarradas a ISO/IEC 25012 em
[`relatorio_qualidade_dados.md`](relatorio_qualidade_dados.md).
