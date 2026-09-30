/**
 * Tipos TypeScript do contrato da API FastAPI.
 *
 * Espelham EXATAMENTE os schemas Pydantic do backend:
 *   - backend/app/schemas/common.py       -> RespostaPadrao
 *   - backend/app/schemas/epidemiologia.py -> demais payloads
 *
 * Toda resposta da API usa o envelope { sucesso, dados, mensagem }.
 */

/** Envelope padrao de TODA resposta da API. */
export interface RespostaPadrao<T> {
  /** Indica se a requisicao foi bem-sucedida. */
  sucesso: boolean;
  /** Conteudo de negocio retornado (pode ser objeto, lista ou nulo). */
  dados: T | null;
  /** Mensagem descritiva do resultado (Portugues-Brasil). */
  mensagem: string;
}

/** Ponto semanal da serie temporal municipal de casos-proxy de Influenza A. */
export interface PontoSerie {
  /** Ano epidemiologico (ex.: 2024). */
  ano: number;
  /** Numero da semana epidemiologica (1 a 53). */
  semana: number;
  /** Casos-proxy de Influenza A na semana (>= 0). */
  casos_proxy: number;
  /** TRUE para as 8 semanas mais recentes reservadas por atraso de notificacao. */
  reservada_atraso_notificacao: boolean;
  /** FALSE para semanas reservadas; TRUE caso contrario. */
  usar_no_treino: boolean;
}

/** Payload do healthcheck da API. */
export interface StatusResposta {
  /** Situacao geral da API (ex.: "ok" ou "degradado"). */
  status: string;
  /** Nome da aplicacao. */
  aplicacao: string;
  /** Versao da API. */
  versao: string;
  /** Indica se o banco respondeu a um SELECT 1. */
  banco_conectado: boolean;
  /** Indica se ha um modelo preditivo carregado em memoria. */
  modelo_carregado: boolean;
}

/** Estimativa de casos-proxy para uma semana futura. */
export interface PrevisaoSemana {
  /** Posicao no horizonte de previsao (1 a N). */
  horizonte: number;
  /** Ano epidemiologico estimado. */
  ano: number;
  /** Semana epidemiologica estimada. */
  semana: number;
  /** Estimativa de casos-proxy (>= 0). */
  casos_previstos: number;
}

/** Origem do modelo utilizado na previsao. */
export type OrigemModelo = "modelo_treinado" | "baseline";

/** Conjunto de previsoes e a origem do modelo utilizado. */
export interface PrevisaoResposta {
  /** Origem da previsao: "modelo_treinado" ou "baseline". */
  origem_modelo: OrigemModelo;
  /** Nome/versao do modelo ativo, quando disponivel. */
  nome_modelo: string | null;
  /** Quantidade de semanas previstas. */
  horizonte_semanas: number;
  /** Lista de previsoes semanais. */
  previsoes: PrevisaoSemana[];
}

/** Metricas de avaliacao do modelo ativo lidas do banco. */
export interface MetricaResposta {
  /** Nome do modelo avaliado. */
  nome_modelo: string;
  /** Versao do modelo avaliado. */
  versao: string;
  /** Algoritmo/tecnica do modelo. */
  algoritmo: string;
  /** Erro Medio Absoluto. */
  mae: number | null;
  /** Raiz do Erro Quadratico Medio. */
  rmse: number | null;
  /** Erro Percentual Absoluto Medio (%). */
  mape: number | null;
  /** Proporcao de acerto direcional (0 a 1). */
  acerto_direcional: number | null;
  /** Teste de significancia aplicado (ex.: Diebold-Mariano). */
  teste_significancia: string | null;
  /** p-valor do teste (0 a 1). */
  p_valor: number | null;
  /** Se a diferenca frente ao comparador foi significativa. */
  significativo: boolean | null;
}

/** Unidade de notificacao. A fonte atual pode nao popular NM_UN_INTE. */
export interface UnidadeNotificacao {
  /** Identificador da unidade. */
  id_unidade_notificacao: number;
  /** Nome da unidade (NM_UN_INTE). NULO quando a fonte nao popula o campo. */
  nm_un_inte: string | null;
  /** Codigo IBGE do municipio (ex.: "355030"). */
  co_mun_res: string;
  /** Nome do municipio. */
  nome_municipio: string;
  /** Sigla da UF. */
  sg_uf: string;
  /** Indica se NM_UN_INTE foi efetivamente populado pela fonte. */
  fonte_populada: boolean;
}
