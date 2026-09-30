# Documentacao do Modelo Preditivo (RF004)

> Modulo **modelo** do nucleo pratico do TCC "Analise preditiva de Influenza A no
> municipio de Sao Paulo utilizando IA com dados do SIVEP-Gripe". Sustenta o
> requisito **RF004** (modelo preditivo). Prototipo academico - **nao** e
> ferramenta oficial de vigilancia epidemiologica.

## 1. Visao geral

O modelo preve a contagem semanal de **casos-proxy de Influenza A** no municipio
de Sao Paulo, com **horizonte de 6 semanas**. O modelo principal e um **Random
Forest** (scikit-learn) com **engenharia de atributos temporais**, comparado a um
**baseline ingenuo**, ao **SARIMA** (statsmodels) e ao **Prophet**, todos sob o
mesmo protocolo de **validacao cronologica walk-forward**. As diferencas de
acuracia sao submetidas a **teste de significancia** (Diebold-Mariano, com
Wilcoxon como alternativa nao parametrica).

Artefatos produzidos por `scripts/train_model.py`:

| Artefato | Caminho | Conteudo |
| -------- | ------- | -------- |
| Modelo serializado | `models/modelo_rf_v1.joblib` | `PreditorRandomForest` (RF + config de atributos). |
| Grafico real x previsto | `docs/grafico_real_x_previsto.png` | Real vs previsto de todos os modelos (walk-forward). |
| Tabela de metricas (CSV) | `docs/metricas_modelos.csv` | Metricas + testes de significancia por modelo. |
| Tabela de metricas (MD) | `docs/metricas_modelos.md` | Mesma tabela em Markdown, com legenda. |
| Registro no banco | `modelo_preditivo` + `metrica_modelo` | Modelo ativo e metricas reais, servidos por `/api/metricas`. |
| Bloco de seed | `database/seed.sql` (bloco delimitado) | INSERTs do modelo/metricas para PostgreSQL. |

## 2. Organizacao do codigo

O codigo do modelo vive em `backend/app/model/`, de modo que **o mesmo gerador de
atributos** seja usado no treino (`scripts/train_model.py`) e na previsao em
producao (`app.services.previsao_service`). Isso elimina divergencia de formato
de features entre treino e inferencia.

| Arquivo | Responsabilidade |
| ------- | ---------------- |
| `app/model/features.py` | Engenharia de atributos temporais (lags, medias moveis, sazonalidade). |
| `app/model/metricas.py` | MAE, RMSE, MAPE (com tratamento de zeros), sMAPE e acerto direcional. |
| `app/model/significancia.py` | Diebold-Mariano (com correcao HLN) e Wilcoxon. |
| `app/model/preditor.py` | `PreditorRandomForest` serializavel, com `prever_series` (previsao recursiva). |
| `app/model/walk_forward.py` | Validacao walk-forward e preditores de bloco (baseline/RF/SARIMA/Prophet). |
| `scripts/train_model.py` | Orquestra o experimento e gera todos os artefatos. |

## 3. Variavel-alvo e base

- **Alvo:** casos-proxy semanais de Influenza A no municipio de Sao Paulo
  (agregacao por semana epidemiologica). O proxy segue a regra do ETL (FEAT-001):
  registros com `PCR_FLUASU` preenchido contam como caso.
- **Base de treino:** semanas com `USAR_NO_TREINO = True`. As **8 semanas
  epidemiologicas mais recentes** ficam **reservadas** (atraso de notificacao) e
  nao entram no treino nem na avaliacao.
- **Granularidade:** sempre **municipal** (a fonte consolidada nao tem
  granularidade por unidade/bairro).

## 4. Engenharia de atributos temporais

Para cada semana `t`, os atributos usam **exclusivamente informacao anterior a
`t`** (sem vazamento de futuro):

- **defasagens (lags):** 1, 2, 3 e 4 semanas;
- **medias moveis:** janelas de 3 e 5 semanas (calculadas sobre valores
  anteriores a `t`);
- **sazonalidade:** seno e cosseno do ciclo anual (52 semanas) e o mes aproximado
  da semana epidemiologica.

A previsao multi-passo do horizonte de 6 semanas e **recursiva**: cada previsao e
reinserida no historico para gerar os atributos da semana seguinte.

## 5. Protocolo de validacao (walk-forward)

A avaliacao **nunca** usa embaralhamento aleatorio. Adotamos *walk-forward* com
**origem expansiva** (`expanding window`): a cada passo o modelo treina com todo o
historico disponivel ate a origem e preve o proximo bloco de **6 semanas**; a
origem avanca 6 semanas e o processo se repete ate esgotar a serie de treino. Os
pares (real, previsto) de todos os blocos sao concatenados para o calculo das
metricas e dos testes de significancia. A primeira origem exige um historico
minimo de 60 semanas.

## 6. Metricas

| Metrica | Definicao | Observacao |
| ------- | --------- | ---------- |
| **MAE** | Erro medio absoluto | Robusta a escala. |
| **RMSE** | Raiz do erro quadratico medio | Penaliza erros grandes (picos). |
| **MAPE** | Erro percentual absoluto medio | Calculado **apenas nas semanas com real > 0** para evitar divisao por zero; o numero de semanas de zero descartadas e reportado. |
| **sMAPE** | MAPE simetrico | Finito mesmo com zeros; metrica percentual principal reportada. |
| **acerto direcional** | Proporcao de acerto na direcao (subida/descida) | Compara o sinal das variacoes consecutivas. |

**Tratamento de semanas de zero casos.** A serie e esparsa: ha muitas semanas com
zero casos-proxy. O MAPE classico e indefinido nesses pontos (divisao por zero),
por isso ele e restrito as semanas com real positivo e complementado pelo sMAPE,
que permanece finito. Essa ressalva esta amarrada a caracteristica de
**Exatidao/Completude** do Anexo de Qualidade (ISO/IEC 25012).

## 7. Teste de significancia estatistica

- **Diebold-Mariano (principal).** Compara a acuracia de dois modelos pela media
  do diferencial de perda (perda quadratica, `g(e) = e^2`). Sob a hipotese nula
  de igual acuracia, o diferencial medio e zero. Aplicamos a **correcao de amostra
  pequena de Harvey-Leybourne-Newbold (1997)** e comparamos a estatistica a uma
  distribuicao t de Student com `n-1` graus de liberdade. Com o Random Forest como
  modelo 1, `DM < 0` favorece o Random Forest. A formula e as fontes estao
  documentadas no cabecalho de `app/model/significancia.py`.
- **Wilcoxon (alternativa).** Teste nao parametrico dos postos com sinais aplicado
  aos erros absolutos pareados; nao assume normalidade e e util em series curtas.

## 8. Resultados observados (honestidade metodologica)

Os valores abaixo sao os **efetivamente obtidos** na execucao do
`scripts/train_model.py` sobre a serie de treino (walk-forward, horizonte de 6
semanas). A tabela completa (com p-valores) esta em `docs/metricas_modelos.md`.

| modelo | MAE | RMSE | sMAPE (%) | acerto direcional |
| ------ | --- | ---- | --------- | ----------------- |
| baseline (sazonal-ingenuo) | 8,28 | 22,86 | 47,33 | 0,512 |
| **random_forest** | 8,56 | 25,48 | 37,51 | 0,531 |
| sarima | 7,51 | 23,34 | 44,53 | 0,482 |
| prophet | 10,38 | 23,07 | 46,96 | 0,532 |

Testes de significancia (Random Forest frente a cada comparador):

| comparador | Diebold-Mariano (p-valor) | significativo? | Wilcoxon (p-valor) | significativo? |
| ---------- | ------------------------- | -------------- | ------------------ | -------------- |
| baseline | 0,512 | nao | 0,0006 | sim |
| sarima | 0,336 | nao | 0,482 | nao |
| prophet | 0,542 | nao | 0,000 | sim |

**Leitura honesta dos resultados.** Nesta serie curta e esparsa, o Random Forest
**nao superou** o baseline sazonal-ingenuo em MAE/RMSE, e o teste de
**Diebold-Mariano nao indicou diferenca estatisticamente significativa** entre o
Random Forest e nenhum dos comparadores (todos os p-valores > 0,05). O **SARIMA**
obteve o menor MAE, tambem sem diferenca significativa frente ao Random Forest. O
Wilcoxon acusou diferenca no erro *mediano* frente a baseline e Prophet, mas o
Diebold-Mariano (baseado na perda media) nao confirmou vantagem media
significativa. Conforme o Manual Interno, **o modelo nao pode ser apresentado como
comprovadamente superior**: o artefato e entregue e integrado por completude do
requisito RF004, com desempenho reportado com transparencia. O sMAPE menor do
Random Forest sugere melhor desempenho relativo em semanas de valores moderados,
mas isso nao se traduz em vantagem estatisticamente significativa.

## 9. Integracao com o backend (RF001)

- O `PreditorRandomForest` salvo em `models/modelo_rf_v1.joblib` expoe
  `prever_series(historico, horizonte)` - exatamente a interface ja prevista em
  `app.services.previsao_service._prever_com_modelo` (FEAT-003).
- Na inicializacao, o servico carrega o `.joblib` em memoria (padrao do TC2,
  secao 4.6.4). Quando o modelo existe, `/api/previsoes` responde com
  `origem_modelo = "modelo_treinado"`; caso contrario, usa o baseline sazonal.
- As metricas reais sao gravadas em `modelo_preditivo`/`metrica_modelo` e servidas
  por `/api/metricas` (o `train_model.py` grava no banco de desenvolvimento e
  regenera o bloco correspondente em `database/seed.sql`).

## 10. Limitacoes do modelo

- **Subnotificacao e atraso de notificacao:** dados recentes sao incompletos; por
  isso as 8 semanas mais recentes sao reservadas do treino.
- **Serie curta e esparsa:** muitas semanas de zero casos e **hiato de 2020-2021**
  (ausente na fonte, nao preenchido com zeros artificiais) reduzem a capacidade de
  aprendizado de padroes estaveis.
- **Alvo baseado em proxy:** o alvo usa `PCR_FLUASU` preenchido como proxy de
  confirmacao, pois os campos de confirmacao laboratorial do TC2
  (`CLASSI_FIN`, `PCR_RESUL`, `POS_PCRFLU`, `TP_FLU_PCR`, `POS_AN_FLU`,
  `TP_FLU_AN`) **nao existem** na fonte consolidada (ver
  `docs/relatorio_qualidade_dados.md`).
- **Sazonalidade e regime variavel:** a intensidade das temporadas varia bastante
  entre anos, dificultando a generalizacao.
- **Previsao recursiva:** o erro se acumula ao longo do horizonte de 6 semanas.
- **Nao e vigilancia oficial:** as previsoes tem carater academico e exploratorio.

## 11. Reproducao

```bash
# a partir da raiz do repositorio
uv --directory backend run python ../scripts/train_model.py   # treina e gera artefatos
cd backend && uv run pytest tests/test_model.py -q            # testes do modelo
```

## 12. Rastreabilidade de referencias

Cada decisao do modulo esta amarrada a sua fonte, conforme solicitado (documentos
internos do TCC e referencias tecnicas/publicas).

| # | Decisao / conteudo aplicado | Fonte / referencia | Onde no projeto |
| - | --------------------------- | ------------------ | --------------- |
| 1 | Requisito RF004 (modelo preditivo) e comparacao obrigatoria com baseline/SARIMA/Prophet + teste de significancia | Manual Interno de Desenvolvimento do TCC (`Documentos_Para_Desenv_TCC/Manual_Interno_Desenvolvimento_TCC_Influenza_v2.docx`); `TCC - C D H M (TC2).docx` (RF001-RF004) | `scripts/train_model.py`, `app/model/walk_forward.py` |
| 2 | Exclusao das 8 semanas mais recentes do treino (atraso de notificacao) | Manual Interno; `docs/relatorio_qualidade_dados.md` | `carregar_serie_treino` em `scripts/train_model.py` |
| 3 | Regra de proxy `PCR_FLUASU` e ausencia dos campos de confirmacao do TC2 | `TCC - C D H M (TC2).docx` (Tabela 1); `docs/relatorio_qualidade_dados.md`; `docs/dicionario_dados.md` | Secao 3 e 10 deste documento |
| 4 | Horizonte de 6 semanas e carga do modelo em memoria na inicializacao | `TCC_DefinicaoConceitual_v12 (1).docx`; TC2 secao 4.6.4 (modelo em memoria) | `app/services/previsao_service.py`, `app/core/config.py` |
| 5 | Validacao cronologica walk-forward (nunca aleatoria) | Boa pratica de avaliacao de series temporais: Hyndman, R. J.; Athanasopoulos, G. *Forecasting: Principles and Practice*, 3a ed., cap. 5.10 ([otexts.com/fpp3](https://otexts.com/fpp3/tscv.html)) | `app/model/walk_forward.py` |
| 6 | MAPE indefinido com zeros; uso do sMAPE | Hyndman & Koehler (2006), "Another look at measures of forecast accuracy", *International Journal of Forecasting* 22(4); ISO/IEC 25012 (Exatidao/Completude, Anexo de Qualidade `TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx`) | `app/model/metricas.py` |
| 7 | Teste de Diebold-Mariano | Diebold, F. X.; Mariano, R. S. (1995), "Comparing Predictive Accuracy", *Journal of Business & Economic Statistics* 13(3), 253-263 | `app/model/significancia.py` |
| 8 | Correcao de amostra pequena do DM | Harvey, D.; Leybourne, S.; Newbold, P. (1997), "Testing the equality of prediction mean squared errors", *International Journal of Forecasting* 13(2), 281-291 | `app/model/significancia.py` |
| 9 | Teste de Wilcoxon (alternativa nao parametrica) | Wilcoxon, F. (1945), "Individual Comparisons by Ranking Methods", *Biometrics Bulletin* 1(6); implementacao `scipy.stats.wilcoxon` ([docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html)) | `app/model/significancia.py` |
| 10 | Random Forest para regressao | Breiman, L. (2001), "Random Forests", *Machine Learning* 45(1); `sklearn.ensemble.RandomForestRegressor` ([docs](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)) | `app/model/preditor.py`, `app/model/walk_forward.py` |
| 11 | SARIMA | `statsmodels.tsa.statespace.sarimax.SARIMAX` ([docs](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html)) | `preditor_sarima` em `app/model/walk_forward.py` |
| 12 | Prophet | Taylor, S. J.; Letham, B. (2018), "Forecasting at scale", *The American Statistician* 72(1); biblioteca Prophet ([facebook.github.io/prophet](https://facebook.github.io/prophet/)) | `preditor_prophet` em `app/model/walk_forward.py` |
| 13 | Registro de metricas no banco (rastreabilidade) e uso dos modelos ORM | `Manual_Padrao_Documentacao_Bancos_de_Dados.docx`; `docs/dicionario_banco.md`; schema de FEAT-002 | `registrar_no_banco` em `scripts/train_model.py`, `app/models/orm.py` |
| 14 | Honestidade na apresentacao de resultados (proibicao de superioridade nao comprovada) | Manual Interno; `Normas CNPQ Uso de IA.pdf` | Secao 8 deste documento e do notebook |
| 15 | Serializacao do modelo com joblib | `joblib` ([docs](https://joblib.readthedocs.io/)) | `salvar_modelo` em `scripts/train_model.py` |

> As referencias a documentos internos (`Documentos_Para_Desenv_TCC/*.docx/*.pdf`)
> apontam para os arquivos versionados no repositorio. As referencias externas
> apontam para a documentacao publica das bibliotecas e para a literatura tecnica
> das tecnicas empregadas.
