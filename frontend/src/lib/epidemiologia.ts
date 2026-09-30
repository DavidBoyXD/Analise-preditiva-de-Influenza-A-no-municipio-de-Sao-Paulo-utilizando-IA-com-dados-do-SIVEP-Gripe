/**
 * Utilitarios de dominio para a serie epidemiologica semanal.
 *
 * Reune formatacao de valores, rotulos de semana/ano e pequenas agregacoes
 * usadas pelos graficos e cards. Mantido puro (sem React) para reuso e teste.
 */

import type { PontoSerie, PrevisaoSemana } from "@/types";

/** Placeholder padrao para valores ausentes/nulos na UI. */
export const PLACEHOLDER_VAZIO = "indisponivel";

/** Formata um numero inteiro no padrao pt-BR (ex.: 1234 -> "1.234"). */
export function formatarInteiro(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return PLACEHOLDER_VAZIO;
  }
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(valor);
}

/** Formata um numero com casas decimais no padrao pt-BR. */
export function formatarDecimal(
  valor: number | null | undefined,
  casas = 2,
): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return PLACEHOLDER_VAZIO;
  }
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(valor);
}

/** Formata uma proporcao (0 a 1) como percentual pt-BR (ex.: 0.71 -> "71,0%"). */
export function formatarPercentual(
  valor: number | null | undefined,
  casas = 1,
): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return PLACEHOLDER_VAZIO;
  }
  return `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(valor * 100)}%`;
}

/** Rotulo curto de uma semana epidemiologica (ex.: "2024-S05"). */
export function rotuloSemana(ano: number, semana: number): string {
  return `${ano}-S${String(semana).padStart(2, "0")}`;
}

/** Rotulo textual de um periodo a partir do primeiro e ultimo ponto. */
export function rotuloPeriodo(pontos: Array<{ ano: number; semana: number }>): string {
  if (pontos.length === 0) {
    return "sem dados no periodo";
  }
  const primeiro = pontos[0];
  const ultimo = pontos[pontos.length - 1];
  return `${rotuloSemana(primeiro.ano, primeiro.semana)} a ${rotuloSemana(
    ultimo.ano,
    ultimo.semana,
  )}`;
}

/** Soma dos casos-proxy de uma serie. */
export function somarCasos(pontos: PontoSerie[]): number {
  return pontos.reduce((total, ponto) => total + ponto.casos_proxy, 0);
}

/** Ponto de pico (maior casos_proxy). Retorna null para serie vazia. */
export function encontrarPico(pontos: PontoSerie[]): PontoSerie | null {
  if (pontos.length === 0) {
    return null;
  }
  return pontos.reduce((maior, ponto) =>
    ponto.casos_proxy > maior.casos_proxy ? ponto : maior,
  );
}

/**
 * Ultima semana consolidada (usar_no_treino=true e nao reservada).
 * As semanas reservadas por atraso de notificacao nao sao consideradas
 * consolidadas. Retorna null quando nao houver.
 */
export function ultimaSemanaConsolidada(pontos: PontoSerie[]): PontoSerie | null {
  for (let i = pontos.length - 1; i >= 0; i -= 1) {
    const ponto = pontos[i];
    if (ponto.usar_no_treino && !ponto.reservada_atraso_notificacao) {
      return ponto;
    }
  }
  return null;
}

/** Agrega os casos-proxy por ano epidemiologico. */
export function agregarPorAno(
  pontos: PontoSerie[],
): Array<{ ano: number; casos_proxy: number; semanas: number }> {
  const mapa = new Map<number, { casos_proxy: number; semanas: number }>();
  for (const ponto of pontos) {
    const atual = mapa.get(ponto.ano) ?? { casos_proxy: 0, semanas: 0 };
    atual.casos_proxy += ponto.casos_proxy;
    atual.semanas += 1;
    mapa.set(ponto.ano, atual);
  }
  return Array.from(mapa.entries())
    .map(([ano, valor]) => ({ ano, ...valor }))
    .sort((a, b) => a.ano - b.ano);
}

/** Ponto de grafico combinado com series "real" e "previsto" separadas. */
export interface PontoComparacao {
  rotulo: string;
  ano: number;
  semana: number;
  /** Valor real (historico). Ausente nos pontos futuros previstos. */
  real?: number;
  /** Valor previsto. Ausente nos pontos historicos reais. */
  previsto?: number;
}

/**
 * Combina a serie real com as previsoes para o grafico real x previsto,
 * mantendo as duas series em campos DISTINTOS (real vs previsto) para que
 * nunca se misturem visualmente. Um ponto de "ancora" liga a ultima observacao
 * real ao inicio da linha prevista (continuidade visual sem sobrepor valores).
 */
export function montarComparacao(
  serieReal: PontoSerie[],
  previsoes: PrevisaoSemana[],
): PontoComparacao[] {
  const pontos: PontoComparacao[] = serieReal.map((ponto) => ({
    rotulo: rotuloSemana(ponto.ano, ponto.semana),
    ano: ponto.ano,
    semana: ponto.semana,
    real: ponto.casos_proxy,
  }));

  // Ancora: repete o ultimo valor real tambem no campo previsto para que a
  // linha tracejada comece a partir do ultimo dado observado.
  const ultimoReal = serieReal[serieReal.length - 1];
  if (ultimoReal && pontos.length > 0) {
    pontos[pontos.length - 1].previsto = ultimoReal.casos_proxy;
  }

  for (const previsao of previsoes) {
    pontos.push({
      rotulo: rotuloSemana(previsao.ano, previsao.semana),
      ano: previsao.ano,
      semana: previsao.semana,
      previsto: previsao.casos_previstos,
    });
  }

  return pontos;
}
