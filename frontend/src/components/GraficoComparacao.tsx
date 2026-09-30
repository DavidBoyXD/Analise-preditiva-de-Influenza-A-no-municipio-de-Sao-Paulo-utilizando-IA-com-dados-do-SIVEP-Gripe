"use client";

/**
 * Grafico de COMPARACAO REAL x PREVISTO.
 *
 * A serie de previsao fica VISUALMENTE SEPARADA do dado real: cor distinta
 * (laranja) + linha TRACEJADA + legenda propria ("Previsto"), enquanto o real e
 * uma linha continua azul ("Real"). Nunca se misturam no mesmo campo de dados
 * (ver montarComparacao). Exibe a origem do modelo (modelo_treinado/baseline) e
 * o nome quando disponivel.
 *
 * DEGRADACAO ELEGANTE: recebe o estado da previsao por props. Se a previsao
 * estiver indisponivel (503), mostra apenas um aviso neste bloco, sem afetar o
 * historico/cards do restante do dashboard.
 */

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PontoSerie, PrevisaoResposta } from "@/types";
import {
  formatarInteiro,
  montarComparacao,
  rotuloPeriodo,
  rotuloSemana,
} from "@/lib/epidemiologia";

import QuadroGrafico from "./QuadroGrafico";
import { Carregando, Erro, Vazio } from "./EstadoUI";

interface GraficoComparacaoProps {
  serieReal: PontoSerie[];
  previsao: PrevisaoResposta | null;
  carregandoPrevisao: boolean;
  /** True quando a previsao respondeu 503 (indisponivel). */
  previsaoIndisponivel: boolean;
  /** Mensagem de erro geral da previsao (nao 503), quando houver. */
  erroPrevisao: string | null;
  aoTentarNovamente: () => void;
}

function SeloOrigem({ previsao }: { previsao: PrevisaoResposta }) {
  const modeloTreinado = previsao.origem_modelo === "modelo_treinado";
  return (
    <span className={`selo ${modeloTreinado ? "selo-modelo" : "selo-baseline"}`}>
      {modeloTreinado ? "Modelo treinado" : "Baseline"}
      {previsao.nome_modelo ? `: ${previsao.nome_modelo}` : ""}
    </span>
  );
}

export default function GraficoComparacao({
  serieReal,
  previsao,
  carregandoPrevisao,
  previsaoIndisponivel,
  erroPrevisao,
  aoTentarNovamente,
}: GraficoComparacaoProps) {
  const periodo = rotuloPeriodo(serieReal);

  // Corpo interno depende do estado da previsao (degradacao elegante).
  let corpo: React.ReactNode;

  if (serieReal.length === 0) {
    corpo = <Vazio mensagem="Sem serie historica para comparar." />;
  } else if (carregandoPrevisao) {
    corpo = <Carregando rotulo="Carregando previsoes..." />;
  } else if (previsaoIndisponivel) {
    corpo = (
      <div className="aviso-inline" role="status">
        Previsao temporariamente indisponivel. O historico continua disponivel
        nos demais graficos e indicadores.
      </div>
    );
  } else if (erroPrevisao) {
    corpo = <Erro mensagem={erroPrevisao} aoTentarNovamente={aoTentarNovamente} />;
  } else if (!previsao || previsao.previsoes.length === 0) {
    corpo = <Vazio mensagem="Nenhuma previsao retornada pelo modelo." />;
  } else {
    const dados = montarComparacao(serieReal, previsao.previsoes);
    const ultimoReal = serieReal[serieReal.length - 1];
    const marcadorTransicao = ultimoReal
      ? rotuloSemana(ultimoReal.ano, ultimoReal.semana)
      : undefined;

    corpo = (
      <>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={dados} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--cor-borda)" />
            <XAxis
              dataKey="rotulo"
              tick={{ fontSize: 11 }}
              interval="preserveStartEnd"
              minTickGap={24}
            />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip
              formatter={(valor: number, nome: string) => [
                formatarInteiro(valor),
                nome,
              ]}
            />
            <Legend />
            {marcadorTransicao ? (
              <ReferenceLine
                x={marcadorTransicao}
                stroke="var(--cor-texto-suave)"
                strokeDasharray="4 4"
                label={{
                  value: "inicio da previsao",
                  position: "insideTopRight",
                  fontSize: 10,
                  fill: "var(--cor-texto-suave)",
                }}
              />
            ) : null}
            <Line
              type="monotone"
              dataKey="real"
              name="Real (historico)"
              stroke="var(--cor-real)"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="previsto"
              name="Previsto (modelo)"
              stroke="var(--cor-previsto)"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={{ r: 3 }}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="painel-subtitulo" style={{ marginTop: "0.5rem" }}>
          A serie <strong>Real</strong> (linha continua azul) representa o
          historico observado. A serie <strong>Previsto</strong> (linha
          tracejada laranja) representa a estimativa do modelo e nao se mistura
          com o dado real.
        </p>
      </>
    );
  }

  return (
    <QuadroGrafico
      titulo="Comparacao real x previsto"
      periodo={periodo}
      acessorio={previsao && !previsaoIndisponivel ? <SeloOrigem previsao={previsao} /> : null}
    >
      {corpo}
    </QuadroGrafico>
  );
}
