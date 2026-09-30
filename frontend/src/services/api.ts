/**
 * Cliente HTTP tipado da API FastAPI.
 *
 * Uma funcao por endpoint. Todas leem a base de NEXT_PUBLIC_API_URL, adicionam
 * o prefixo /api, desempacotam o envelope { sucesso, dados, mensagem } e lancam
 * erros tipados (ErroApi / PrevisaoIndisponivelError) para a UI distinguir os
 * casos. O caminho padrao e a API REAL; o mock (NEXT_PUBLIC_USAR_MOCK) e apenas
 * um fallback de desenvolvimento claramente marcado.
 */

import type {
  MetricaResposta,
  PontoSerie,
  PrevisaoResposta,
  RespostaPadrao,
  StatusResposta,
  UnidadeNotificacao,
} from "@/types";

import { ErroApi, PrevisaoIndisponivelError } from "./erros";
import {
  dadosMock,
  metricasMock,
  previsoesMock,
  seriesTemporaisMock,
  statusMock,
  unidadesNotificacaoMock,
} from "./mock";

/** URL base da API (sem barra final). Prefixo /api adicionado nas requisicoes. */
const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

/**
 * Ativa o modo mock (fallback de desenvolvimento SEM backend).
 * NUNCA e o caminho padrao: so vale quando NEXT_PUBLIC_USAR_MOCK === "true".
 */
export const USANDO_MOCK = process.env.NEXT_PUBLIC_USAR_MOCK === "true";

/** Parametros de filtro por periodo do endpoint /api/dados. */
export interface FiltroPeriodo {
  ano_inicio?: number;
  semana_inicio?: number;
  ano_fim?: number;
  semana_fim?: number;
}

/** Monta uma query string ignorando valores nulos/indefinidos. */
function montarQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== null) {
      query.append(chave, String(valor));
    }
  }
  const texto = query.toString();
  return texto ? `?${texto}` : "";
}

/**
 * Executa uma requisicao GET e desempacota o envelope RespostaPadrao<T>.
 *
 * @param caminho Caminho relativo ao prefixo /api (ex.: "/status").
 * @returns O conteudo de `dados` do envelope.
 * @throws ErroApi em falha de rede, HTTP nao-2xx ou envelope malsucedido.
 */
async function requisitarGet<T>(caminho: string): Promise<T> {
  const url = `${API_URL}/api${caminho}`;

  let resposta: Response;
  try {
    resposta = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (erro) {
    throw new ErroApi(
      `Falha de conexao com a API (${url}): ${
        erro instanceof Error ? erro.message : "erro desconhecido"
      }`,
      0,
    );
  }

  let corpo: RespostaPadrao<T> | null = null;
  try {
    corpo = (await resposta.json()) as RespostaPadrao<T>;
  } catch {
    corpo = null;
  }

  if (!resposta.ok) {
    const mensagem = corpo?.mensagem ?? `Erro HTTP ${resposta.status} ao acessar ${caminho}.`;
    throw new ErroApi(mensagem, resposta.status);
  }

  if (!corpo || corpo.sucesso !== true) {
    throw new ErroApi(corpo?.mensagem ?? "A API retornou um resultado sem sucesso.", resposta.status);
  }

  return corpo.dados as T;
}

/** GET /api/status - healthcheck da API, banco e modelo. */
export async function getStatus(): Promise<StatusResposta> {
  if (USANDO_MOCK) return statusMock;
  return requisitarGet<StatusResposta>("/status");
}

/** GET /api/dados - serie historica filtrada por periodo (semana/ano). */
export async function getDados(filtro: FiltroPeriodo = {}): Promise<PontoSerie[]> {
  if (USANDO_MOCK) return dadosMock;
  const query = montarQuery({
    ano_inicio: filtro.ano_inicio,
    semana_inicio: filtro.semana_inicio,
    ano_fim: filtro.ano_fim,
    semana_fim: filtro.semana_fim,
  });
  return requisitarGet<PontoSerie[]>(`/dados${query}`);
}

/** GET /api/series-temporais - serie temporal semanal (opcionalmente apenas treino). */
export async function getSeriesTemporais(
  opcoes: { apenas_treino?: boolean } = {},
): Promise<PontoSerie[]> {
  if (USANDO_MOCK) {
    return opcoes.apenas_treino
      ? seriesTemporaisMock.filter((ponto) => ponto.usar_no_treino)
      : seriesTemporaisMock;
  }
  const query = montarQuery({ apenas_treino: opcoes.apenas_treino });
  return requisitarGet<PontoSerie[]>(`/series-temporais${query}`);
}

/**
 * GET /api/previsoes - estimativas de casos-proxy para as proximas semanas.
 *
 * IMPORTANTE: o HTTP 503 (PrevisaoIndisponivel) e traduzido para
 * PrevisaoIndisponivelError, um estado especifico distinto de erro geral, para
 * permitir degradacao elegante (o historico continua visivel na UI).
 *
 * @throws PrevisaoIndisponivelError quando a API responde 503.
 * @throws ErroApi para os demais erros.
 */
export async function getPrevisoes(
  opcoes: { horizonte?: number } = {},
): Promise<PrevisaoResposta> {
  if (USANDO_MOCK) return previsoesMock;
  const query = montarQuery({ horizonte: opcoes.horizonte });
  try {
    return await requisitarGet<PrevisaoResposta>(`/previsoes${query}`);
  } catch (erro) {
    if (erro instanceof ErroApi && erro.status === 503) {
      throw new PrevisaoIndisponivelError(erro.message);
    }
    throw erro;
  }
}

/** GET /api/metricas - metricas de avaliacao do modelo ativo. */
export async function getMetricas(): Promise<MetricaResposta> {
  if (USANDO_MOCK) return metricasMock;
  return requisitarGet<MetricaResposta>("/metricas");
}

/** GET /api/unidades-notificacao - unidades cadastradas (NM_UN_INTE pode ser nulo). */
export async function getUnidadesNotificacao(): Promise<UnidadeNotificacao[]> {
  if (USANDO_MOCK) return unidadesNotificacaoMock;
  return requisitarGet<UnidadeNotificacao[]>("/unidades-notificacao");
}
