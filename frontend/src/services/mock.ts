/**
 * Fixtures de MOCK apenas para desenvolvimento SEM backend.
 *
 * ATENCAO: este NAO e o caminho padrao. Os dados aqui sao ficticios e servem
 * exclusivamente para desenvolver a UI quando a API real nao esta disponivel.
 * O mock so e ativado quando NEXT_PUBLIC_USAR_MOCK === "true" (ver api.ts).
 * A versao final SEMPRE consome a API real.
 */

import type {
  MetricaResposta,
  PontoSerie,
  PrevisaoResposta,
  StatusResposta,
  UnidadeNotificacao,
} from "@/types";

/** Gera uma serie temporal ficticia com sazonalidade simples. */
function gerarSerieMock(): PontoSerie[] {
  const pontos: PontoSerie[] = [];
  const totalSemanas = 60;
  const ano = 2024;
  for (let i = 0; i < totalSemanas; i += 1) {
    const semana = (i % 52) + 1;
    const anoPonto = ano + Math.floor(i / 52);
    const base = 40 + Math.round(30 * Math.sin((i / 52) * 2 * Math.PI));
    const ruido = Math.round(Math.random() * 10);
    // As 8 semanas mais recentes sao reservadas por atraso de notificacao.
    const reservada = i >= totalSemanas - 8;
    pontos.push({
      ano: anoPonto,
      semana,
      casos_proxy: Math.max(0, base + ruido),
      reservada_atraso_notificacao: reservada,
      usar_no_treino: !reservada,
    });
  }
  return pontos;
}

const serieMock = gerarSerieMock();

export const statusMock: StatusResposta = {
  status: "ok",
  aplicacao: "API Influenza A (MOCK)",
  versao: "0.0.0-mock",
  banco_conectado: true,
  modelo_carregado: true,
};

export const dadosMock: PontoSerie[] = serieMock;

export const seriesTemporaisMock: PontoSerie[] = serieMock;

export const previsoesMock: PrevisaoResposta = {
  origem_modelo: "baseline",
  nome_modelo: "baseline-mock",
  horizonte_semanas: 6,
  previsoes: Array.from({ length: 6 }, (_, i) => ({
    horizonte: i + 1,
    ano: 2024,
    semana: 53 + i,
    casos_previstos: 45 + Math.round(Math.random() * 15),
  })),
};

export const metricasMock: MetricaResposta = {
  nome_modelo: "random_forest_mock",
  versao: "0.0.0-mock",
  algoritmo: "RandomForestRegressor",
  mae: 8.42,
  rmse: 11.7,
  mape: 0.19,
  acerto_direcional: 0.71,
  teste_significancia: "Diebold-Mariano",
  p_valor: 0.03,
  significativo: true,
};

export const unidadesNotificacaoMock: UnidadeNotificacao[] = [
  {
    id_unidade_notificacao: 1,
    nm_un_inte: null,
    co_mun_res: "355030",
    nome_municipio: "Sao Paulo",
    sg_uf: "SP",
    fonte_populada: false,
  },
];
