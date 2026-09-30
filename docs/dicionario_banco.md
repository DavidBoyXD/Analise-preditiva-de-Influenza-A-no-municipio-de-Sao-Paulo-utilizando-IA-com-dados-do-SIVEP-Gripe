# Dicionario de Dados do Banco Relacional (RF003)

| Item | Valor |
|------|-------|
| Sistema | Analise preditiva de Influenza A no municipio de Sao Paulo utilizando IA com dados do SIVEP-Gripe |
| Documento | Dicionario e documentacao do banco de dados relacional |
| Versao | 1.0 |
| Status | Aprovado (entrega do modulo de banco - FEAT-002) |
| Classificacao | Uso interno academico (dados publicos; nao ha dados pessoais identificaveis armazenados) |
| Responsavel | Equipe do TCC (C D H M) |
| SGBD | PostgreSQL 16 (producao); SQLite (banco de testes do backend) |
| Artefatos | `database/schema.sql`, `database/indexes.sql`, `database/seed.sql`, `docs/der_banco.mmd`, `docs/der_banco.png` |

> Este documento segue o **Manual Padrao de Documentacao Tecnica de Bancos de
> Dados** (secoes 3 a 4): visao geral, contexto e responsaveis; modelo logico e
> fisico; dicionario de dados; convencoes de nomenclatura; regras de modelagem;
> justificativa de normalizacao. Protótipo academico - **nao** e ferramenta
> oficial de vigilancia epidemiologica.

---

## 1. Visao geral

O banco relacional armazena, de forma rastreavel e normalizada, os dados
epidemiologicos de SRAG/Influenza A do municipio de Sao Paulo capital
(CO_MUN_RES = 355030) provenientes do **SIVEP-Gripe / SINAN (DATASUS)**, a serie
temporal semanal consumida pelo modelo preditivo e os metadados/metricas dos
modelos de IA. Ele sustenta o requisito **RF003** (persistencia e rastreabilidade
dos dados) e alimenta o backend (FastAPI) e o modulo de modelagem.

**Granularidade principal:** uma linha por semana epidemiologica (nivel
**municipal**) em `serie_temporal` e em `registro_epidemiologico`. A variavel-alvo
e a contagem semanal de casos-proxy de Influenza A (ver secao 6).

## 2. Contexto e responsaveis (papeis do Manual, secao 2.1)

| Papel | Responsabilidade |
|-------|------------------|
| Data Owner | Equipe do TCC - define finalidade academica e escopo |
| Data Steward | Equipe do TCC - mantem o dicionario e as regras de qualidade |
| Arquiteto de Dados | Equipe do TCC - define o modelo relacional e os padroes |
| Consumidores | Backend FastAPI (RF001/RF002/RF004) e modulo de modelagem |

Fonte publica dos dados: SIVEP-Gripe / SINAN (DATASUS), dados abertos de SRAG.

## 3. Modelo logico

O modelo tem **nove entidades**. Diagrama Entidade-Relacionamento:

- Fonte editavel: [`der_banco.mmd`](der_banco.mmd) (Mermaid).
- Imagem: [`der_banco.png`](der_banco.png).
- Regeneracao: `mmdc -i docs/der_banco.mmd -o docs/der_banco.png`
  (`npm i -g @mermaid-js/mermaid-cli`) ou colar a fonte em <https://mermaid.live>.

Entidades e papel:

1. **fonte_dados** - origem publica dos dados (SIVEP-Gripe/DATASUS).
2. **arquivo_dados** - arquivos brutos/tratados/backup (rastreabilidade).
3. **unidade_notificacao** - recorte de unidade/municipio (campo NM_UN_INTE).
4. **semana_epidemiologica** - dimensao temporal (ano + numero da semana).
5. **registro_epidemiologico** - fato agregado por semana (casos-proxy).
6. **serie_temporal** - serie semanal consolidada usada pelo modelo.
7. **modelo_preditivo** - metadados dos modelos de IA (.joblib, versao ativa).
8. **metrica_modelo** - metricas de avaliacao e teste de significancia.
9. **log_processamento** - eventos/erros de coleta, tratamento e execucao.

## 4. Convencoes de nomenclatura (Manual, secao 4.2)

| Objeto | Padrao | Exemplo neste banco |
|--------|--------|---------------------|
| Tabela | singular snake_case | `arquivo_dados` |
| Chave primaria | `id_<entidade>` | `id_arquivo_dados` |
| Chave estrangeira | `id_<entidade_referenciada>` | `id_fonte_dados` |
| Indice | `ix_<tabela>_<colunas>` | `ix_semana_epidemiologica_ano_semana` |
| Unico | `uq_<tabela>_<colunas>` | `uq_fonte_dados_nome_fonte` |
| Check | `ck_<tabela>_<regra>` | `ck_arquivo_dados_status` |
| PK/FK constraint | `pk_<tabela>` / `fk_<tabela>_<ref>` | `fk_arquivo_dados_fonte_dados` |

Datas usam **tipo temporal** (`DATE`/`TIMESTAMP`), nunca texto (Manual, secao 4.3
- "Proibido: datas armazenadas como texto"). Toda tabela e coluna possui
`COMMENT ON` (Manual - "Proibido: tabelas ou colunas sem descricao"). Todo indice
possui justificativa (Manual - "Proibido: indice sem motivacao").

## 5. Dicionario de dados

Legenda de Chave: PK = primaria; FK = estrangeira; UK = unica. "Nulo" indica se
a coluna aceita `NULL`.

### 5.1. fonte_dados
Origem publica dos dados epidemiologicos. Relacao 1:N com `arquivo_dados`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_fonte_dados | INTEGER | Nao | PK | Identificador tecnico imutavel da fonte. |
| nome_fonte | VARCHAR(100) | Nao | UK | Nome da fonte (ex.: "SIVEP-Gripe / SINAN - DATASUS"). |
| descricao | TEXT | Nao | - | Descricao da fonte e uso permitido. |
| url_fonte | VARCHAR(500) | Sim | - | URL publica de referencia. |
| data_inclusao | TIMESTAMP | Nao | - | Data/hora de registro da fonte. Default CURRENT_TIMESTAMP. |

### 5.2. arquivo_dados
Arquivos coletados/tratados/backup. N:1 com `fonte_dados`; 1:N com
`registro_epidemiologico` e `log_processamento`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_arquivo_dados | INTEGER | Nao | PK | Identificador do arquivo. |
| id_fonte_dados | INTEGER | Nao | FK | Fonte a que o arquivo pertence. |
| nome_arquivo | VARCHAR(255) | Nao | - | Nome do arquivo. |
| formato_arquivo | VARCHAR(20) | Nao | - | Formato (ex.: CSV, PARQUET). |
| tipo_arquivo | VARCHAR(30) | Nao | - | Dominio: `bruto` \| `tratado` \| `backup`. |
| ano_referencia_inicio | SMALLINT | Sim | - | Primeiro ano epidemiologico coberto. |
| ano_referencia_fim | SMALLINT | Sim | - | Ultimo ano epidemiologico coberto (>= inicio). |
| caminho_origem | TEXT | Sim | - | Endereco do arquivo original. |
| caminho_armazenamento | TEXT | Sim | - | Endereco de armazenamento no projeto. |
| quantidade_registros | INTEGER | Sim | - | Numero de linhas de dados (>= 0). |
| data_importacao | TIMESTAMP | Nao | - | Data/hora da importacao. Default CURRENT_TIMESTAMP. |
| status_arquivo | VARCHAR(30) | Nao | - | Dominio: `importado` \| `processado` \| `erro`. |

### 5.3. unidade_notificacao
Recorte de unidade de notificacao (NM_UN_INTE). **Substitui** bairro/regiao do
TC2. 1:N com `registro_epidemiologico` e `serie_temporal`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_unidade_notificacao | INTEGER | Nao | PK | Identificador da unidade. |
| nm_un_inte | VARCHAR(150) | Sim | UK* | Nome da unidade (NM_UN_INTE). NULO na fonte atual (ver secao 8). |
| co_mun_res | VARCHAR(7) | Nao | UK* | Codigo IBGE do municipio (ex.: 355030). |
| nome_municipio | VARCHAR(120) | Nao | - | Nome do municipio (ex.: Sao Paulo). |
| sg_uf | VARCHAR(2) | Nao | - | Sigla da UF (ex.: SP). |
| fonte_populada | BOOLEAN | Nao | - | TRUE se NM_UN_INTE foi populado; FALSE registra a pendencia. |

\* `uq_unidade_notificacao_mun_unidade` = UNIQUE (co_mun_res, nm_un_inte).

### 5.4. semana_epidemiologica
Dimensao temporal. 1:N com `registro_epidemiologico` e `serie_temporal`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_semana_epidemiologica | INTEGER | Nao | PK | Identificador da semana. |
| ano_epidemiologico | SMALLINT | Nao | UK* | Ano (2000 a 2100). |
| numero_semana | SMALLINT | Nao | UK* | Numero da semana (1 a 53). |
| data_inicio | DATE | Sim | - | Data de inicio da semana. |
| data_fim | DATE | Sim | - | Data de fim da semana (>= inicio). |

\* `uq_semana_epidemiologica_ano_semana` = UNIQUE (ano_epidemiologico, numero_semana).

### 5.5. registro_epidemiologico
Fato agregado por semana (casos-proxy). Tabela central. N:1 com `arquivo_dados`,
`semana_epidemiologica` e `unidade_notificacao`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_registro | INTEGER | Nao | PK | Identificador do agregado. |
| id_arquivo_dados | INTEGER | Nao | FK | Arquivo tratado de origem. |
| id_semana_epidemiologica | INTEGER | Nao | FK | Semana do agregado. |
| id_unidade_notificacao | INTEGER | Sim | FK | Unidade/municipio (NULO enquanto NM_UN_INTE nao e populado). |
| quantidade_casos_proxy | INTEGER | Nao | - | Casos-proxy de Influenza A na semana (>= 0). |
| quantidade_registros | INTEGER | Nao | - | Total de registros de SRAG na semana (>= casos_proxy). |
| data_referencia | DATE | Sim | - | Data de referencia do agregado. |

UNIQUE `uq_registro_epidemiologico_arquivo_semana_unidade` (id_arquivo_dados,
id_semana_epidemiologica, id_unidade_notificacao) evita duplicidade do agregado.

### 5.6. serie_temporal
Serie semanal consolidada consumida pelo modelo. N:1 com `semana_epidemiologica`
e `unidade_notificacao`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_serie_temporal | INTEGER | Nao | PK | Identificador do ponto da serie. |
| id_semana_epidemiologica | INTEGER | Nao | FK | Semana do ponto. |
| id_unidade_notificacao | INTEGER | Sim | FK | Recorte (municipal). |
| casos_proxy | INTEGER | Nao | - | Casos-proxy na semana (0 quando sem casos; >= 0). |
| reservada_atraso_notificacao | BOOLEAN | Nao | - | TRUE para as 8 semanas mais recentes (reservadas). |
| usar_no_treino | BOOLEAN | Nao | - | FALSE para reservadas; TRUE caso contrario. |

CHECK `ck_serie_temporal_flag_treino` garante a coerencia:
`reservada_atraso_notificacao = TRUE` **se e somente se** `usar_no_treino = FALSE`.
UNIQUE `uq_serie_temporal_semana_unidade` garante um ponto por semana/unidade.

### 5.7. modelo_preditivo
Metadados dos modelos de IA. 1:N com `metrica_modelo` e `log_processamento`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_modelo | INTEGER | Nao | PK | Identificador do modelo. |
| nome_modelo | VARCHAR(100) | Nao | UK* | Nome (ex.: random_forest, sarima, baseline_sazonal). |
| algoritmo | VARCHAR(150) | Nao | - | Tecnica/algoritmo utilizado. |
| versao | VARCHAR(30) | Nao | UK* | Versao do modelo. |
| caminho_modelo_serializado | TEXT | Sim | - | Caminho do `.joblib`. |
| janela_historica_semanas | SMALLINT | Sim | - | Semanas historicas de entrada (> 0). |
| horizonte_previsao_semanas | SMALLINT | Sim | - | Semanas previstas a frente (> 0). |
| data_treinamento | TIMESTAMP | Sim | - | Data/hora do treinamento. |
| status_modelo | VARCHAR(30) | Nao | - | Dominio: `treinado` \| `validado` \| `ativo` \| `inativo`. |
| ativo | BOOLEAN | Nao | - | TRUE = versao ativa em producao. |
| observacao | TEXT | Sim | - | Observacoes tecnicas. |

\* `uq_modelo_preditivo_nome_versao` = UNIQUE (nome_modelo, versao).

### 5.8. metrica_modelo
Metricas de avaliacao e teste de significancia. N:1 com `modelo_preditivo`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_metrica | INTEGER | Nao | PK | Identificador da metrica. |
| id_modelo | INTEGER | Nao | FK | Modelo avaliado. |
| mae | DECIMAL(12,4) | Sim | - | Erro Medio Absoluto (>= 0). |
| rmse | DECIMAL(12,4) | Sim | - | Raiz do Erro Quadratico Medio (>= 0). |
| mape | DECIMAL(8,4) | Sim | - | Erro Percentual Absoluto Medio, em % (>= 0). |
| acerto_direcional | DECIMAL(5,4) | Sim | - | Proporcao de acerto direcional (0 a 1). |
| teste_significancia | VARCHAR(50) | Sim | - | Teste aplicado (ex.: Diebold-Mariano, Wilcoxon). |
| estatistica_teste | DECIMAL(12,6) | Sim | - | Valor da estatistica do teste. |
| p_valor | DECIMAL(8,6) | Sim | - | p-valor do teste (0 a 1). |
| significativo | BOOLEAN | Sim | - | TRUE se a diferenca foi estatisticamente significativa. |
| data_avaliacao | TIMESTAMP | Nao | - | Data/hora da avaliacao. Default CURRENT_TIMESTAMP. |
| base_teste_inicio | DATE | Sim | - | Inicio do periodo de teste (walk-forward). |
| base_teste_fim | DATE | Sim | - | Fim do periodo de teste (>= inicio). |
| observacao | TEXT | Sim | - | Observacoes sobre o desempenho. |

### 5.9. log_processamento
Eventos/erros de processamento. FKs **opcionais** para `arquivo_dados` e
`modelo_preditivo`.

| Coluna | Tipo | Nulo | Chave | Descricao / Dominio |
|--------|------|------|-------|---------------------|
| id_log | INTEGER | Nao | PK | Identificador do log. |
| id_arquivo_dados | INTEGER | Sim | FK | Arquivo relacionado ao evento (opcional). |
| id_modelo | INTEGER | Sim | FK | Modelo relacionado ao evento (opcional). |
| data_hora | TIMESTAMP | Nao | - | Data/hora do evento. Default CURRENT_TIMESTAMP. |
| tipo_evento | VARCHAR(20) | Nao | - | Dominio: `ERRO` \| `ALERTA` \| `INFO`. |
| origem | VARCHAR(100) | Nao | - | Origem (ex.: coleta, tratamento, modelo, api). |
| mensagem | TEXT | Nao | - | Descricao detalhada do evento. |
| stack_trace | TEXT | Sim | - | Rastreamento de pilha do erro, quando aplicavel. |
| status | VARCHAR(30) | Nao | - | Dominio: `resolvido` \| `pendente` \| `interrompido`. |

## 6. Regra da variavel-alvo (casos-proxy)

`quantidade_casos_proxy` / `casos_proxy` representam a contagem de registros com
**PCR_FLUASU preenchido** (regra de proxy de confirmacao de Influenza A definida
no ETL - FEAT-001), agregada por semana epidemiologica no nivel municipal. A
limitacao dessa proxy e a ausencia dos campos de confirmacao laboratorial da
Tabela 1 do TC2 estao documentadas em
[`relatorio_qualidade_dados.md`](relatorio_qualidade_dados.md) (amarradas a
ISO/IEC 25012) e em [`dicionario_dados.md`](dicionario_dados.md).

## 7. Cardinalidades explicadas

| Relacionamento | Cardinalidade | Justificativa |
|----------------|---------------|---------------|
| fonte_dados -> arquivo_dados | 1:N | Uma fonte publica origina varios arquivos (bruto, tratado, backup). |
| arquivo_dados -> registro_epidemiologico | 1:N | Um arquivo tratado gera varios agregados semanais. |
| arquivo_dados -> log_processamento | 1:N | Um arquivo pode gerar varios eventos/erros de processamento. |
| semana_epidemiologica -> registro_epidemiologico | 1:N | Uma semana pode ter varios agregados (por arquivo/unidade). |
| semana_epidemiologica -> serie_temporal | 1:N | Uma semana corresponde a pontos da serie (por unidade). |
| unidade_notificacao -> registro_epidemiologico | 1:N | Uma unidade/municipio agrega varios registros semanais. |
| unidade_notificacao -> serie_temporal | 1:N | Uma unidade/municipio possui varios pontos na serie. |
| modelo_preditivo -> metrica_modelo | 1:N | Um modelo pode ser avaliado varias vezes (versoes/janelas). |
| modelo_preditivo -> log_processamento | 1:N | Um modelo pode gerar varios eventos durante execucao/treino. |

O relacionamento **N:N** original entre bairro e predicao do TC2 (via
`bairro_predicao`) **deixou de existir** com a remocao dessas tabelas (secao 8).

## 8. Nota de escopo: remocao de bairro/regiao/bairro_predicao e pendencia NM_UN_INTE

O modelo original do TC2 (secao 4.9.3) previa as tabelas `bairro`, `regiao`,
`bairro_predicao` (associativa N:N), `tipo_notificacao` e `predicao_epidemiologica`.
Com base nos achados do ETL (FEAT-001):

- **`bairro`, `regiao` e `bairro_predicao` foram REMOVIDAS.** O CSV consolidado
  do SIVEP-Gripe **nao possui granularidade de bairro/regiao** e a modelagem
  preditiva deste projeto e sempre **municipal**. Manter essas tabelas violaria a
  orientacao ao consumidor (dados sem origem real) e criaria estrutura sem dado.
- A entidade **`unidade_notificacao`** substitui esse recorte e preve o campo
  **`nm_un_inte`** (NM_UN_INTE do SIVEP-Gripe). Porem, a **fonte consolidada atual
  NAO popula NM_UN_INTE**: no seed, a unica linha de unidade representa o municipio
  de Sao Paulo com `nm_un_inte = NULL` e `fonte_populada = FALSE`. Essa pendencia
  esta registrada tambem no relatorio de qualidade de dados. A estrutura fica
  pronta para evolucao caso uma fonte com o campo populado seja incorporada.
- `tipo_notificacao` e `predicao_epidemiologica` nao foram incluidas nesta entrega
  de nucleo: o recorte e unico (SRAG/Influenza A, proxy PCR_FLUASU) e as previsoes
  sao servidas pelo backend a partir do modelo, sem necessidade de tabela de
  predicao no escopo minimo. `modelo_preditivo` e `metrica_modelo` cobrem a
  rastreabilidade dos modelos e resultados.

## 9. Justificativa da normalizacao (3FN)

O modelo esta na **Terceira Forma Normal** (Manual, secao 4.3 - "adotar 3FN como
referencia para dados transacionais"):

- **1FN:** todos os atributos sao atomicos; nao ha grupos repetitivos nem listas
  em colunas.
- **2FN:** nao ha chaves compostas com dependencia parcial. As entidades usam
  chave substituta (`id_<entidade>`); atributos dependem da chave inteira.
- **3FN:** nao ha dependencias transitivas. Dados de fonte, arquivo, tempo
  (semana), local (unidade) e modelo foram **decompostos em entidades proprias** e
  referenciados por FK, em vez de repetidos nas tabelas de fato. Ex.: o par
  (ano, semana) vive em `semana_epidemiologica` e nao e repetido em
  `serie_temporal`/`registro_epidemiologico`; o municipio vive em
  `unidade_notificacao`.

Nao ha desnormalizacoes deliberadas. As colunas de contagem
(`quantidade_registros` em `registro_epidemiologico`) sao **fatos aditivos** da
propria granularidade, nao dependencias transitivas.

## 10. Modelo fisico e validacao

- **DDL:** `database/schema.sql` (CREATE TABLE, PK, FK, CHECK, UNIQUE, tipos
  temporais, `COMMENT ON` em toda tabela e coluna).
- **Indices:** `database/indexes.sql` (indices `ix_...` para periodo, municipio,
  unidade e chaves estrangeiras, cada um justificado).
- **Carga inicial:** `database/seed.sql` (gerado por `scripts/gerar_seed_banco.py`
  a partir de `data/processed/serie_temporal_semanal.csv`; sem credenciais).

**Ordem de aplicacao:** `schema.sql` -> `indexes.sql` -> `seed.sql`.

**Validacao realizada (PostgreSQL 16 via container Docker):** os tres scripts
aplicam sem erro; integridade referencial preservada (0 FKs orfas); contagens do
seed: 1 fonte, 2 arquivos, 1 unidade, 832 semanas, 832 pontos de serie (824 de
treino + 8 reservados); nenhuma tabela `bairro`/`regiao`/`bairro_predicao`; 0
tabelas e 0 colunas sem `COMMENT`.

**Compatibilidade SQLite (testes do backend - FEAT-003):** o `schema.sql` (sem as
instrucoes `COMMENT ON`, exclusivas do PostgreSQL) e o `seed.sql` aplicam sem erro
no SQLite. Recomenda-se que o backend gere o schema de teste via SQLAlchemy (que
emite DDL compativel com o dialeto ativo) e reserve os arquivos `.sql` como a
fonte de verdade do PostgreSQL de producao. Os tipos usados (VARCHAR, INTEGER,
SMALLINT, DECIMAL, DATE, TIMESTAMP, BOOLEAN, TEXT) sao ANSI e portaveis; nao ha
recursos exclusivos do PostgreSQL alem de `COMMENT ON`.

## 11. Rastreabilidade das referencias

| Conteudo aplicado | Origem |
|-------------------|--------|
| Convencoes de nomenclatura (PK/FK/ix/uq/ck), regras de modelagem e 3FN, proibicoes (datas como texto, objeto sem descricao, indice sem motivo) | `Documentos_Para_Desenv_TCC/Manual_Padrao_Documentacao_Bancos_de_Dados.docx`, secoes 3-4 |
| Estrutura das tabelas fonte_dados, arquivo_dados, registro_epidemiologico, modelo_preditivo, metrica_modelo, log_processamento e cardinalidades | `Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx`, secao 4.9.3 |
| Regra de proxy PCR_FLUASU, exclusao das 8 semanas recentes, ausencia de NM_UN_INTE e dos campos de confirmacao | FEAT-001: `docs/relatorio_qualidade_dados.md` e `docs/dicionario_dados.md` |
| Metricas MAE/RMSE/MAPE, acerto direcional, teste de significancia (Diebold-Mariano/Wilcoxon), walk-forward, modelo versionado | `context.json` (verification_instructions) e `TCC - C D H M (TC2).docx` |
