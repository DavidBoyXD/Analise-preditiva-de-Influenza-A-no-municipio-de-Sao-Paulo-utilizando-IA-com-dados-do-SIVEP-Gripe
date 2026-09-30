-- =============================================================================
-- indexes.sql - Indices do modelo relacional (RF003).
--
-- Padrao de nomenclatura (Manual, secao 4.2): ix_<tabela>_<colunas>.
-- Justificativa de desempenho (Manual, secao 4.5 - "Proibido: indice sem
-- motivacao"): cada indice abaixo tem comentario explicando a consulta que ele
-- acelera. As consultas criticas do sistema sao por periodo (semana/ano),
-- por municipio/unidade de notificacao e por modelo (metricas/logs).
--
-- Observacao: PKs e restricoes UNIQUE ja criam indices implicitos (ex.: o par
-- ano/semana em semana_epidemiologica). Os indices abaixo cobrem colunas de
-- FK e filtros frequentes que NAO sao cobertos por esses indices implicitos.
--
-- Compatibilidade: sintaxe "CREATE INDEX ... ON tabela (colunas)" e valida
-- tanto em PostgreSQL quanto em SQLite. COMMENT ON INDEX e especifico do
-- PostgreSQL; a justificativa fica tambem como comentario de linha para o
-- SQLite/leitura humana.
-- =============================================================================

-- Consulta por periodo: filtrar/ordenar semanas por ano e numero da semana.
CREATE INDEX ix_semana_epidemiologica_ano_semana
    ON semana_epidemiologica (ano_epidemiologico, numero_semana);
COMMENT ON INDEX ix_semana_epidemiologica_ano_semana
    IS 'Acelera consultas por periodo (filtro/ordenacao por ano e semana epidemiologica), padrao dominante nas visualizacoes temporais.';

-- Consulta por unidade/municipio: filtrar unidades por codigo de municipio.
CREATE INDEX ix_unidade_notificacao_co_mun_res
    ON unidade_notificacao (co_mun_res);
COMMENT ON INDEX ix_unidade_notificacao_co_mun_res
    IS 'Acelera filtros por municipio (CO_MUN_RES, ex.: 355030 = Sao Paulo) e futura consulta por unidade de notificacao.';

-- FK -> arquivo_dados em registro_epidemiologico (rastreabilidade/joins).
CREATE INDEX ix_registro_epidemiologico_arquivo_dados
    ON registro_epidemiologico (id_arquivo_dados);
COMMENT ON INDEX ix_registro_epidemiologico_arquivo_dados
    IS 'Acelera joins e rastreabilidade dos registros por arquivo de origem (coluna de FK).';

-- FK -> semana_epidemiologica em registro_epidemiologico (agregacao temporal).
CREATE INDEX ix_registro_epidemiologico_semana_epidemiologica
    ON registro_epidemiologico (id_semana_epidemiologica);
COMMENT ON INDEX ix_registro_epidemiologico_semana_epidemiologica
    IS 'Acelera a agregacao/consulta de casos por semana epidemiologica (coluna de FK).';

-- FK -> unidade_notificacao em registro_epidemiologico (consulta por unidade).
CREATE INDEX ix_registro_epidemiologico_unidade_notificacao
    ON registro_epidemiologico (id_unidade_notificacao);
COMMENT ON INDEX ix_registro_epidemiologico_unidade_notificacao
    IS 'Acelera consultas por unidade de notificacao/municipio (coluna de FK), quando o campo NM_UN_INTE passar a ser populado.';

-- FK -> semana_epidemiologica em serie_temporal (leitura da serie do modelo).
CREATE INDEX ix_serie_temporal_semana_epidemiologica
    ON serie_temporal (id_semana_epidemiologica);
COMMENT ON INDEX ix_serie_temporal_semana_epidemiologica
    IS 'Acelera a leitura ordenada da serie temporal semanal consumida pelo modelo (coluna de FK).';

-- Filtro da serie pelas semanas efetivamente usadas no treino.
CREATE INDEX ix_serie_temporal_usar_no_treino
    ON serie_temporal (usar_no_treino);
COMMENT ON INDEX ix_serie_temporal_usar_no_treino
    IS 'Acelera a selecao das semanas de treino (usar_no_treino = TRUE), excluindo as 8 semanas recentes reservadas.';

-- FK -> modelo_preditivo em metrica_modelo (avaliacoes por modelo).
CREATE INDEX ix_metrica_modelo_modelo
    ON metrica_modelo (id_modelo);
COMMENT ON INDEX ix_metrica_modelo_modelo
    IS 'Acelera a consulta das metricas de avaliacao por modelo (coluna de FK).';

-- FKs de log_processamento (busca de logs por arquivo ou modelo).
CREATE INDEX ix_log_processamento_arquivo_dados
    ON log_processamento (id_arquivo_dados);
COMMENT ON INDEX ix_log_processamento_arquivo_dados
    IS 'Acelera a busca de logs relacionados a um arquivo especifico (coluna de FK opcional).';

CREATE INDEX ix_log_processamento_modelo
    ON log_processamento (id_modelo);
COMMENT ON INDEX ix_log_processamento_modelo
    IS 'Acelera a busca de logs relacionados a um modelo especifico (coluna de FK opcional).';

-- Consulta operacional de logs por data e tipo de evento (ex.: erros recentes).
CREATE INDEX ix_log_processamento_data_hora_tipo
    ON log_processamento (data_hora, tipo_evento);
COMMENT ON INDEX ix_log_processamento_data_hora_tipo
    IS 'Acelera a consulta operacional de eventos por data e tipo (ex.: ERRO/ALERTA recentes) para monitoramento.';
