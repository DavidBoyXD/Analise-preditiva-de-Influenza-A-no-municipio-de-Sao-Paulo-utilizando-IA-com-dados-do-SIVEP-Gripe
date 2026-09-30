"use client";

/**
 * Cards de indicadores do periodo filtrado.
 *
 * Mostra: total de casos-proxy, semana/ano de pico, ultima semana consolidada
 * (usar_no_treino=true e nao reservada) e origem do modelo de previsao
 * (modelo_treinado vs baseline). Valores ausentes usam placeholder claro.
 */

import type { OrigemModelo, PontoSerie } from "@/types";
import {
  encontrarPico,
  formatarInteiro,
  rotuloSemana,
  somarCasos,
  ultimaSemanaConsolidada,
} from "@/lib/epidemiologia";

interface CardsIndicadoresProps {
  serie: PontoSerie[];
  /** Origem do modelo, ou null quando a previsao esta indisponivel. */
  origemModelo: OrigemModelo | null;
  /** Nome do modelo, quando disponivel. */
  nomeModelo: string | null;
  /** True quando a previsao falhou (503) e nao ha origem para exibir. */
  previsaoIndisponivel: boolean;
}

function Card({
  rotulo,
  valor,
  detalhe,
  children,
}: {
  rotulo: string;
  valor?: string;
  detalhe?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="card-indicador">
      <span className="rotulo">{rotulo}</span>
      {valor !== undefined ? <span className="valor">{valor}</span> : null}
      {children}
      {detalhe ? <span className="detalhe">{detalhe}</span> : null}
    </div>
  );
}

export default function CardsIndicadores({
  serie,
  origemModelo,
  nomeModelo,
  previsaoIndisponivel,
}: CardsIndicadoresProps) {
  const total = somarCasos(serie);
  const pico = encontrarPico(serie);
  const consolidada = ultimaSemanaConsolidada(serie);

  return (
    <div className="grid-cards" aria-label="Indicadores do periodo">
      <Card
        rotulo="Total de casos-proxy"
        valor={serie.length > 0 ? formatarInteiro(total) : "indisponivel"}
        detalhe={`${serie.length} semana(s) no periodo`}
      />
      <Card
        rotulo="Semana de pico"
        valor={pico ? rotuloSemana(pico.ano, pico.semana) : "indisponivel"}
        detalhe={pico ? `${formatarInteiro(pico.casos_proxy)} casos-proxy` : undefined}
      />
      <Card
        rotulo="Ultima semana consolidada"
        valor={
          consolidada
            ? rotuloSemana(consolidada.ano, consolidada.semana)
            : "indisponivel"
        }
        detalhe={
          consolidada
            ? `${formatarInteiro(consolidada.casos_proxy)} casos-proxy (usada no treino)`
            : "sem semana consolidada no periodo"
        }
      />
      <Card rotulo="Origem da previsao">
        {previsaoIndisponivel || origemModelo === null ? (
          <span className="detalhe">Previsao indisponivel</span>
        ) : (
          <>
            <span
              className={`selo ${
                origemModelo === "modelo_treinado" ? "selo-modelo" : "selo-baseline"
              }`}
            >
              {origemModelo === "modelo_treinado" ? "Modelo treinado" : "Baseline"}
            </span>
            <span className="detalhe">{nomeModelo ?? "modelo sem nome informado"}</span>
          </>
        )}
      </Card>
    </div>
  );
}
