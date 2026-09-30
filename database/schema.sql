-- =============================================================================
-- schema.sql - Modelo relacional (DDL PostgreSQL) do sistema de analise
--              preditiva de Influenza A no municipio de Sao Paulo (RF003).
--
-- Projeto ....: TCC - Analise preditiva de Influenza A no municipio de Sao
--               Paulo utilizando IA com dados do SIVEP-Gripe.
-- SGBD .......: PostgreSQL 16 (transacional). Compatibilidade de tipos pensada
--               tambem para SQLite (banco de testes do backend - FEAT-003):
--               tipos ANSI (VARCHAR, INTEGER, SMALLINT, DECIMAL, DATE,
--               TIMESTAMP, BOOLEAN, TEXT) e chaves substitutas evitam recursos
--               exclusivos do PostgreSQL fora do essencial.
-- Nomenclatura: padrao do "Manual Padrao de Documentacao de Bancos de Dados"
--               (secao 4.2): tabela em singular snake_case; PK id_<entidade>;
--               FK id_<entidade_referenciada>; unico uq_<tabela>_<colunas>;
--               check ck_<tabela>_<regra>. Indices (ix_...) ficam em
--               indexes.sql (secao 6.3 do Manual).
-- Modelagem ..: 3a Forma Normal (3FN) como referencia (Manual, secao 4.3).
-- Escopo .....: as tabelas bairro/regiao/bairro_predicao do TC2 foram
--               REMOVIDAS (o CSV consolidado nao possui granularidade de
--               bairro; a modelagem preditiva e sempre MUNICIPAL). A entidade
--               unidade_notificacao substitui esse recorte e preve o campo
--               NM_UN_INTE, porem a FONTE ATUAL NAO POPULA esse campo
--               (pendencia documentada em docs/dicionario_banco.md).
--
-- Fonte das definicoes de tabela: "TCC - C D H M (TC2).docx", secao 4.9.3.
-- Documentacao completa: docs/dicionario_banco.md.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabela: fonte_dados
-- Origem publica dos dados epidemiologicos (SIVEP-Gripe / SINAN - DATASUS).
-- -----------------------------------------------------------------------------
CREATE TABLE fonte_dados (
    id_fonte_dados   INTEGER      NOT NULL,
    nome_fonte       VARCHAR(100) NOT NULL,
    descricao        TEXT         NOT NULL,
    url_fonte        VARCHAR(500),
    data_inclusao    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fonte_dados PRIMARY KEY (id_fonte_dados),
    CONSTRAINT uq_fonte_dados_nome_fonte UNIQUE (nome_fonte)
);

COMMENT ON TABLE  fonte_dados                 IS 'Origem publica dos dados epidemiologicos utilizados pelo sistema (ex.: SIVEP-Gripe / SINAN - DATASUS). Uma fonte pode conter varios arquivos (1:N com arquivo_dados).';
COMMENT ON COLUMN fonte_dados.id_fonte_dados  IS 'PK. Identificador tecnico imutavel da fonte de dados.';
COMMENT ON COLUMN fonte_dados.nome_fonte      IS 'Nome da fonte utilizada (ex.: "SIVEP-Gripe / SINAN - DATASUS"). Unico.';
COMMENT ON COLUMN fonte_dados.descricao       IS 'Descricao da fonte, natureza dos dados e uso permitido (dados publicos de SRAG).';
COMMENT ON COLUMN fonte_dados.url_fonte       IS 'Endereco publico de referencia/acesso a fonte, quando aplicavel.';
COMMENT ON COLUMN fonte_dados.data_inclusao   IS 'Data e hora de registro da fonte no sistema.';

-- -----------------------------------------------------------------------------
-- Tabela: arquivo_dados
-- Arquivos coletados/tratados/backup - rastreabilidade da origem dos registros.
-- -----------------------------------------------------------------------------
CREATE TABLE arquivo_dados (
    id_arquivo_dados      INTEGER      NOT NULL,
    id_fonte_dados        INTEGER      NOT NULL,
    nome_arquivo          VARCHAR(255) NOT NULL,
    formato_arquivo       VARCHAR(20)  NOT NULL,
    tipo_arquivo          VARCHAR(30)  NOT NULL,
    ano_referencia_inicio SMALLINT,
    ano_referencia_fim    SMALLINT,
    caminho_origem        TEXT,
    caminho_armazenamento TEXT,
    quantidade_registros  INTEGER,
    data_importacao       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_arquivo        VARCHAR(30)  NOT NULL DEFAULT 'importado',
    CONSTRAINT pk_arquivo_dados PRIMARY KEY (id_arquivo_dados),
    CONSTRAINT fk_arquivo_dados_fonte_dados
        FOREIGN KEY (id_fonte_dados) REFERENCES fonte_dados (id_fonte_dados),
    CONSTRAINT ck_arquivo_dados_tipo_arquivo
        CHECK (tipo_arquivo IN ('bruto', 'tratado', 'backup')),
    CONSTRAINT ck_arquivo_dados_status
        CHECK (status_arquivo IN ('importado', 'processado', 'erro')),
    CONSTRAINT ck_arquivo_dados_anos
        CHECK (ano_referencia_fim IS NULL
               OR ano_referencia_inicio IS NULL
               OR ano_referencia_fim >= ano_referencia_inicio),
    CONSTRAINT ck_arquivo_dados_qtd_registros
        CHECK (quantidade_registros IS NULL OR quantidade_registros >= 0)
);

COMMENT ON TABLE  arquivo_dados                       IS 'Arquivos coletados, tratados ou armazenados como backup. Garante a rastreabilidade dos dados (N:1 com fonte_dados; 1:N com registro_epidemiologico e log_processamento).';
COMMENT ON COLUMN arquivo_dados.id_arquivo_dados      IS 'PK. Identificador do arquivo de dados.';
COMMENT ON COLUMN arquivo_dados.id_fonte_dados        IS 'FK -> fonte_dados. Fonte a que o arquivo pertence.';
COMMENT ON COLUMN arquivo_dados.nome_arquivo          IS 'Nome do arquivo coletado ou processado.';
COMMENT ON COLUMN arquivo_dados.formato_arquivo       IS 'Formato do arquivo (ex.: CSV, PARQUET).';
COMMENT ON COLUMN arquivo_dados.tipo_arquivo          IS 'Natureza do arquivo. Dominio: bruto | tratado | backup.';
COMMENT ON COLUMN arquivo_dados.ano_referencia_inicio IS 'Primeiro ano epidemiologico coberto pelo arquivo.';
COMMENT ON COLUMN arquivo_dados.ano_referencia_fim    IS 'Ultimo ano epidemiologico coberto pelo arquivo.';
COMMENT ON COLUMN arquivo_dados.caminho_origem        IS 'Endereco onde o arquivo original esta armazenado (fonte).';
COMMENT ON COLUMN arquivo_dados.caminho_armazenamento IS 'Endereco onde o arquivo foi armazenado no projeto.';
COMMENT ON COLUMN arquivo_dados.quantidade_registros  IS 'Quantidade de registros (linhas de dados) do arquivo. >= 0.';
COMMENT ON COLUMN arquivo_dados.data_importacao       IS 'Data e hora em que o arquivo foi importado.';
COMMENT ON COLUMN arquivo_dados.status_arquivo        IS 'Situacao do arquivo. Dominio: importado | processado | erro.';

-- -----------------------------------------------------------------------------
-- Tabela: unidade_notificacao
-- Recorte de unidade de notificacao (campo NM_UN_INTE do SIVEP-Gripe).
-- SUBSTITUI bairro/regiao do TC2. A FONTE ATUAL NAO POPULA NM_UN_INTE; a
-- estrutura fica prevista para evolucao (pendencia documentada). A modelagem
-- preditiva permanece MUNICIPAL.
-- -----------------------------------------------------------------------------
CREATE TABLE unidade_notificacao (
    id_unidade_notificacao INTEGER      NOT NULL,
    nm_un_inte             VARCHAR(150),
    co_mun_res             VARCHAR(7)   NOT NULL,
    nome_municipio         VARCHAR(120) NOT NULL,
    sg_uf                  VARCHAR(2)   NOT NULL,
    fonte_populada         BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_unidade_notificacao PRIMARY KEY (id_unidade_notificacao),
    CONSTRAINT uq_unidade_notificacao_mun_unidade
        UNIQUE (co_mun_res, nm_un_inte)
);

COMMENT ON TABLE  unidade_notificacao                        IS 'Unidade/local de notificacao (campo NM_UN_INTE do SIVEP-Gripe). Substitui bairro/regiao do TC2. A fonte consolidada atual NAO popula NM_UN_INTE (fonte_populada = FALSE); a modelagem e sempre municipal. Relacao 1:N com registro_epidemiologico.';
COMMENT ON COLUMN unidade_notificacao.id_unidade_notificacao IS 'PK. Identificador da unidade de notificacao.';
COMMENT ON COLUMN unidade_notificacao.nm_un_inte             IS 'Nome da unidade de internacao/notificacao (NM_UN_INTE do SIVEP-Gripe). NULO quando a fonte nao populou o campo (pendencia conhecida).';
COMMENT ON COLUMN unidade_notificacao.co_mun_res             IS 'Codigo IBGE do municipio de residencia (ex.: 355030 = Sao Paulo capital).';
COMMENT ON COLUMN unidade_notificacao.nome_municipio         IS 'Nome do municipio de residencia (ex.: Sao Paulo).';
COMMENT ON COLUMN unidade_notificacao.sg_uf                  IS 'Sigla da Unidade da Federacao de residencia (ex.: SP).';
COMMENT ON COLUMN unidade_notificacao.fonte_populada         IS 'Indica se NM_UN_INTE foi efetivamente populado pela fonte. FALSE registra a pendencia de granularidade da fonte atual.';

-- -----------------------------------------------------------------------------
-- Tabela: semana_epidemiologica
-- Dimensao temporal (ano + numero da semana epidemiologica, com datas DATE).
-- -----------------------------------------------------------------------------
CREATE TABLE semana_epidemiologica (
    id_semana_epidemiologica INTEGER  NOT NULL,
    ano_epidemiologico       SMALLINT NOT NULL,
    numero_semana            SMALLINT NOT NULL,
    data_inicio              DATE,
    data_fim                 DATE,
    CONSTRAINT pk_semana_epidemiologica PRIMARY KEY (id_semana_epidemiologica),
    CONSTRAINT uq_semana_epidemiologica_ano_semana
        UNIQUE (ano_epidemiologico, numero_semana),
    CONSTRAINT ck_semana_epidemiologica_numero
        CHECK (numero_semana BETWEEN 1 AND 53),
    CONSTRAINT ck_semana_epidemiologica_ano
        CHECK (ano_epidemiologico BETWEEN 2000 AND 2100),
    CONSTRAINT ck_semana_epidemiologica_datas
        CHECK (data_inicio IS NULL OR data_fim IS NULL OR data_fim >= data_inicio)
);

COMMENT ON TABLE  semana_epidemiologica                          IS 'Dimensao temporal: uma linha por par (ano epidemiologico, numero da semana). Referenciada por registro_epidemiologico e serie_temporal (1:N). Datas usam tipo DATE (nunca texto).';
COMMENT ON COLUMN semana_epidemiologica.id_semana_epidemiologica IS 'PK. Identificador da semana epidemiologica.';
COMMENT ON COLUMN semana_epidemiologica.ano_epidemiologico       IS 'Ano epidemiologico (ex.: 2009). Dominio: 2000 a 2100.';
COMMENT ON COLUMN semana_epidemiologica.numero_semana            IS 'Numero da semana epidemiologica no ano. Dominio: 1 a 53.';
COMMENT ON COLUMN semana_epidemiologica.data_inicio              IS 'Data (DATE) de inicio da semana epidemiologica, quando conhecida.';
COMMENT ON COLUMN semana_epidemiologica.data_fim                 IS 'Data (DATE) de fim da semana epidemiologica, quando conhecida.';

-- -----------------------------------------------------------------------------
-- Tabela: registro_epidemiologico
-- Fato agregado por semana: contagem de casos-proxy de Influenza A no municipio
-- de SP. Tabela central; FK para arquivo_dados, semana_epidemiologica e
-- (opcionalmente) unidade_notificacao.
-- -----------------------------------------------------------------------------
CREATE TABLE registro_epidemiologico (
    id_registro              INTEGER  NOT NULL,
    id_arquivo_dados         INTEGER  NOT NULL,
    id_semana_epidemiologica INTEGER  NOT NULL,
    id_unidade_notificacao   INTEGER,
    quantidade_casos_proxy   INTEGER  NOT NULL DEFAULT 0,
    quantidade_registros     INTEGER  NOT NULL DEFAULT 0,
    data_referencia          DATE,
    CONSTRAINT pk_registro_epidemiologico PRIMARY KEY (id_registro),
    CONSTRAINT fk_registro_epidemiologico_arquivo_dados
        FOREIGN KEY (id_arquivo_dados) REFERENCES arquivo_dados (id_arquivo_dados),
    CONSTRAINT fk_registro_epidemiologico_semana_epidemiologica
        FOREIGN KEY (id_semana_epidemiologica) REFERENCES semana_epidemiologica (id_semana_epidemiologica),
    CONSTRAINT fk_registro_epidemiologico_unidade_notificacao
        FOREIGN KEY (id_unidade_notificacao) REFERENCES unidade_notificacao (id_unidade_notificacao),
    CONSTRAINT uq_registro_epidemiologico_arquivo_semana_unidade
        UNIQUE (id_arquivo_dados, id_semana_epidemiologica, id_unidade_notificacao),
    CONSTRAINT ck_registro_epidemiologico_casos
        CHECK (quantidade_casos_proxy >= 0),
    CONSTRAINT ck_registro_epidemiologico_registros
        CHECK (quantidade_registros >= 0 AND quantidade_registros >= quantidade_casos_proxy)
);

COMMENT ON TABLE  registro_epidemiologico                          IS 'Fato agregado por semana epidemiologica: contagem de casos-proxy de Influenza A (PCR_FLUASU preenchido) no municipio de Sao Paulo. Tabela central (N:1 com arquivo_dados, semana_epidemiologica e unidade_notificacao).';
COMMENT ON COLUMN registro_epidemiologico.id_registro              IS 'PK. Identificador do registro epidemiologico agregado.';
COMMENT ON COLUMN registro_epidemiologico.id_arquivo_dados         IS 'FK -> arquivo_dados. Arquivo tratado de origem do agregado.';
COMMENT ON COLUMN registro_epidemiologico.id_semana_epidemiologica IS 'FK -> semana_epidemiologica. Semana a que o agregado se refere.';
COMMENT ON COLUMN registro_epidemiologico.id_unidade_notificacao   IS 'FK -> unidade_notificacao. Unidade/municipio do agregado. Pode ser NULO enquanto a fonte nao popula NM_UN_INTE.';
COMMENT ON COLUMN registro_epidemiologico.quantidade_casos_proxy   IS 'Casos-proxy de Influenza A na semana (registros com PCR_FLUASU preenchido). >= 0.';
COMMENT ON COLUMN registro_epidemiologico.quantidade_registros     IS 'Total de registros de SRAG na semana (denominador). >= quantidade_casos_proxy.';
COMMENT ON COLUMN registro_epidemiologico.data_referencia          IS 'Data (DATE) de referencia do agregado (ex.: inicio da semana), quando aplicavel.';

-- -----------------------------------------------------------------------------
-- Tabela: serie_temporal
-- Serie semanal consolidada usada pelo modelo, com a flag de exclusao das 8
-- semanas mais recentes (reservadas por atraso de notificacao).
-- -----------------------------------------------------------------------------
CREATE TABLE serie_temporal (
    id_serie_temporal            INTEGER NOT NULL,
    id_semana_epidemiologica     INTEGER NOT NULL,
    id_unidade_notificacao       INTEGER,
    casos_proxy                  INTEGER NOT NULL DEFAULT 0,
    reservada_atraso_notificacao BOOLEAN NOT NULL DEFAULT FALSE,
    usar_no_treino               BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_serie_temporal PRIMARY KEY (id_serie_temporal),
    CONSTRAINT fk_serie_temporal_semana_epidemiologica
        FOREIGN KEY (id_semana_epidemiologica) REFERENCES semana_epidemiologica (id_semana_epidemiologica),
    CONSTRAINT fk_serie_temporal_unidade_notificacao
        FOREIGN KEY (id_unidade_notificacao) REFERENCES unidade_notificacao (id_unidade_notificacao),
    CONSTRAINT uq_serie_temporal_semana_unidade
        UNIQUE (id_semana_epidemiologica, id_unidade_notificacao),
    CONSTRAINT ck_serie_temporal_casos
        CHECK (casos_proxy >= 0),
    CONSTRAINT ck_serie_temporal_flag_treino
        CHECK ((reservada_atraso_notificacao = TRUE  AND usar_no_treino = FALSE)
            OR (reservada_atraso_notificacao = FALSE AND usar_no_treino = TRUE))
);

COMMENT ON TABLE  serie_temporal                              IS 'Serie temporal semanal consolidada consumida pelo modelo preditivo. Uma linha por semana (municipal). As 8 semanas mais recentes ficam reservadas (nao entram no treino) por atraso de notificacao.';
COMMENT ON COLUMN serie_temporal.id_serie_temporal            IS 'PK. Identificador do ponto da serie temporal.';
COMMENT ON COLUMN serie_temporal.id_semana_epidemiologica     IS 'FK -> semana_epidemiologica. Semana do ponto da serie.';
COMMENT ON COLUMN serie_temporal.id_unidade_notificacao       IS 'FK -> unidade_notificacao. Recorte da serie (municipal). Pode ser NULO enquanto a fonte nao popula NM_UN_INTE.';
COMMENT ON COLUMN serie_temporal.casos_proxy                  IS 'Contagem de casos-proxy de Influenza A na semana (0 quando sem casos). >= 0.';
COMMENT ON COLUMN serie_temporal.reservada_atraso_notificacao IS 'TRUE para as 8 semanas mais recentes (reservadas por atraso de notificacao).';
COMMENT ON COLUMN serie_temporal.usar_no_treino               IS 'FALSE para as semanas reservadas; TRUE caso contrario. Coerente com reservada_atraso_notificacao (ck_serie_temporal_flag_treino).';

-- -----------------------------------------------------------------------------
-- Tabela: modelo_preditivo
-- Metadados do modelo de IA (nome, versao, algoritmo, .joblib, versao ativa).
-- -----------------------------------------------------------------------------
CREATE TABLE modelo_preditivo (
    id_modelo                  INTEGER      NOT NULL,
    nome_modelo                VARCHAR(100) NOT NULL,
    algoritmo                  VARCHAR(150) NOT NULL,
    versao                     VARCHAR(30)  NOT NULL,
    caminho_modelo_serializado TEXT,
    janela_historica_semanas   SMALLINT,
    horizonte_previsao_semanas SMALLINT,
    data_treinamento           TIMESTAMP,
    status_modelo              VARCHAR(30)  NOT NULL DEFAULT 'treinado',
    ativo                      BOOLEAN      NOT NULL DEFAULT FALSE,
    observacao                 TEXT,
    CONSTRAINT pk_modelo_preditivo PRIMARY KEY (id_modelo),
    CONSTRAINT uq_modelo_preditivo_nome_versao UNIQUE (nome_modelo, versao),
    CONSTRAINT ck_modelo_preditivo_status
        CHECK (status_modelo IN ('treinado', 'validado', 'ativo', 'inativo')),
    CONSTRAINT ck_modelo_preditivo_horizonte
        CHECK (horizonte_previsao_semanas IS NULL OR horizonte_previsao_semanas > 0),
    CONSTRAINT ck_modelo_preditivo_janela
        CHECK (janela_historica_semanas IS NULL OR janela_historica_semanas > 0)
);

COMMENT ON TABLE  modelo_preditivo                            IS 'Metadados dos modelos de IA (ex.: Random Forest, SARIMA, baseline). Registra tecnica, versao, caminho do .joblib e qual versao esta ativa. Relacao 1:N com metrica_modelo e log_processamento.';
COMMENT ON COLUMN modelo_preditivo.id_modelo                  IS 'PK. Identificador do modelo preditivo.';
COMMENT ON COLUMN modelo_preditivo.nome_modelo               IS 'Nome do modelo (ex.: random_forest, sarima, baseline_sazonal).';
COMMENT ON COLUMN modelo_preditivo.algoritmo                  IS 'Tecnica/algoritmo utilizado pelo modelo.';
COMMENT ON COLUMN modelo_preditivo.versao                     IS 'Versao do modelo. Unico junto com nome_modelo.';
COMMENT ON COLUMN modelo_preditivo.caminho_modelo_serializado IS 'Caminho do arquivo serializado (ex.: models/random_forest_v1.joblib).';
COMMENT ON COLUMN modelo_preditivo.janela_historica_semanas   IS 'Quantidade de semanas historicas usadas como entrada. > 0.';
COMMENT ON COLUMN modelo_preditivo.horizonte_previsao_semanas IS 'Quantidade de semanas previstas a frente. > 0.';
COMMENT ON COLUMN modelo_preditivo.data_treinamento           IS 'Data e hora do treinamento do modelo.';
COMMENT ON COLUMN modelo_preditivo.status_modelo              IS 'Situacao do modelo. Dominio: treinado | validado | ativo | inativo.';
COMMENT ON COLUMN modelo_preditivo.ativo                      IS 'Indica a versao atualmente ativa em producao (TRUE = ativa).';
COMMENT ON COLUMN modelo_preditivo.observacao                 IS 'Observacoes tecnicas sobre o modelo.';

-- -----------------------------------------------------------------------------
-- Tabela: metrica_modelo
-- Metricas de avaliacao (MAE, RMSE, MAPE, acerto direcional) e resultado do
-- teste de significancia (Diebold-Mariano / Wilcoxon).
-- -----------------------------------------------------------------------------
CREATE TABLE metrica_modelo (
    id_metrica            INTEGER       NOT NULL,
    id_modelo             INTEGER       NOT NULL,
    mae                   DECIMAL(12,4),
    rmse                  DECIMAL(12,4),
    mape                  DECIMAL(8,4),
    acerto_direcional     DECIMAL(5,4),
    teste_significancia   VARCHAR(50),
    estatistica_teste     DECIMAL(12,6),
    p_valor               DECIMAL(8,6),
    significativo         BOOLEAN,
    data_avaliacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    base_teste_inicio     DATE,
    base_teste_fim        DATE,
    observacao            TEXT,
    CONSTRAINT pk_metrica_modelo PRIMARY KEY (id_metrica),
    CONSTRAINT fk_metrica_modelo_modelo_preditivo
        FOREIGN KEY (id_modelo) REFERENCES modelo_preditivo (id_modelo),
    CONSTRAINT ck_metrica_modelo_mae   CHECK (mae   IS NULL OR mae   >= 0),
    CONSTRAINT ck_metrica_modelo_rmse  CHECK (rmse  IS NULL OR rmse  >= 0),
    CONSTRAINT ck_metrica_modelo_mape  CHECK (mape  IS NULL OR mape  >= 0),
    CONSTRAINT ck_metrica_modelo_acerto
        CHECK (acerto_direcional IS NULL OR (acerto_direcional >= 0 AND acerto_direcional <= 1)),
    CONSTRAINT ck_metrica_modelo_pvalor
        CHECK (p_valor IS NULL OR (p_valor >= 0 AND p_valor <= 1)),
    CONSTRAINT ck_metrica_modelo_base_teste
        CHECK (base_teste_inicio IS NULL OR base_teste_fim IS NULL OR base_teste_fim >= base_teste_inicio)
);

COMMENT ON TABLE  metrica_modelo                     IS 'Resultados de avaliacao do modelo preditivo (N:1 com modelo_preditivo). Registra MAE, RMSE, MAPE, acerto direcional e o resultado do teste de significancia (Diebold-Mariano / Wilcoxon) frente aos comparadores.';
COMMENT ON COLUMN metrica_modelo.id_metrica          IS 'PK. Identificador da metrica registrada.';
COMMENT ON COLUMN metrica_modelo.id_modelo           IS 'FK -> modelo_preditivo. Modelo avaliado.';
COMMENT ON COLUMN metrica_modelo.mae                 IS 'Erro Medio Absoluto (Mean Absolute Error). >= 0.';
COMMENT ON COLUMN metrica_modelo.rmse                IS 'Raiz do Erro Quadratico Medio (Root Mean Squared Error). >= 0.';
COMMENT ON COLUMN metrica_modelo.mape                IS 'Erro Percentual Absoluto Medio (Mean Absolute Percentage Error), em %. >= 0.';
COMMENT ON COLUMN metrica_modelo.acerto_direcional   IS 'Proporcao de acerto direcional (sobe/desce) da previsao. Dominio: 0 a 1.';
COMMENT ON COLUMN metrica_modelo.teste_significancia IS 'Nome do teste de significancia aplicado (ex.: Diebold-Mariano, Wilcoxon).';
COMMENT ON COLUMN metrica_modelo.estatistica_teste   IS 'Valor da estatistica do teste de significancia.';
COMMENT ON COLUMN metrica_modelo.p_valor             IS 'p-valor do teste de significancia. Dominio: 0 a 1.';
COMMENT ON COLUMN metrica_modelo.significativo       IS 'TRUE se a diferenca frente ao comparador foi estatisticamente significativa (ao nivel adotado).';
COMMENT ON COLUMN metrica_modelo.data_avaliacao      IS 'Data e hora da avaliacao do modelo.';
COMMENT ON COLUMN metrica_modelo.base_teste_inicio   IS 'Data (DATE) inicial do periodo usado no teste (walk-forward).';
COMMENT ON COLUMN metrica_modelo.base_teste_fim      IS 'Data (DATE) final do periodo usado no teste (walk-forward).';
COMMENT ON COLUMN metrica_modelo.observacao          IS 'Observacoes sobre o desempenho e a configuracao da avaliacao.';

-- -----------------------------------------------------------------------------
-- Tabela: log_processamento
-- Eventos/alertas/erros de coleta, tratamento, treinamento ou execucao.
-- FKs opcionais para arquivo_dados e modelo_preditivo.
-- -----------------------------------------------------------------------------
CREATE TABLE log_processamento (
    id_log           INTEGER      NOT NULL,
    id_arquivo_dados INTEGER,
    id_modelo        INTEGER,
    data_hora        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_evento      VARCHAR(20)  NOT NULL,
    origem           VARCHAR(100) NOT NULL,
    mensagem         TEXT         NOT NULL,
    stack_trace      TEXT,
    status           VARCHAR(30)  NOT NULL DEFAULT 'pendente',
    CONSTRAINT pk_log_processamento PRIMARY KEY (id_log),
    CONSTRAINT fk_log_processamento_arquivo_dados
        FOREIGN KEY (id_arquivo_dados) REFERENCES arquivo_dados (id_arquivo_dados),
    CONSTRAINT fk_log_processamento_modelo_preditivo
        FOREIGN KEY (id_modelo) REFERENCES modelo_preditivo (id_modelo),
    CONSTRAINT ck_log_processamento_tipo_evento
        CHECK (tipo_evento IN ('ERRO', 'ALERTA', 'INFO')),
    CONSTRAINT ck_log_processamento_status
        CHECK (status IN ('resolvido', 'pendente', 'interrompido'))
);

COMMENT ON TABLE  log_processamento                  IS 'Eventos, alertas e erros ocorridos na coleta, tratamento, treinamento ou execucao do modelo. FKs opcionais (um log pode referir-se a um arquivo, a um modelo ou a um processo geral).';
COMMENT ON COLUMN log_processamento.id_log           IS 'PK. Identificador do log.';
COMMENT ON COLUMN log_processamento.id_arquivo_dados IS 'FK -> arquivo_dados (opcional). Arquivo relacionado ao evento, quando aplicavel.';
COMMENT ON COLUMN log_processamento.id_modelo        IS 'FK -> modelo_preditivo (opcional). Modelo relacionado ao evento, quando aplicavel.';
COMMENT ON COLUMN log_processamento.data_hora        IS 'Data e hora em que o evento foi registrado.';
COMMENT ON COLUMN log_processamento.tipo_evento      IS 'Tipo do evento. Dominio: ERRO | ALERTA | INFO.';
COMMENT ON COLUMN log_processamento.origem           IS 'Origem do evento (ex.: coleta, tratamento, modelo, api).';
COMMENT ON COLUMN log_processamento.mensagem         IS 'Descricao detalhada do evento registrado.';
COMMENT ON COLUMN log_processamento.stack_trace      IS 'Rastreamento de pilha (stack trace) do erro, quando aplicavel.';
COMMENT ON COLUMN log_processamento.status           IS 'Situacao do evento. Dominio: resolvido | pendente | interrompido.';
