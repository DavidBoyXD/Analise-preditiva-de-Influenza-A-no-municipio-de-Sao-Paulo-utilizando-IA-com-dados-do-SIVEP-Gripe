"use client";

/**
 * Grafico de LINHA da serie historica de casos-proxy.
 *
 * Sinaliza visualmente as semanas com reservada_atraso_notificacao=true (as 8
 * mais recentes, que nao entram no treino) por meio de uma faixa sombreada
 * (ReferenceArea) e um marcador distinto nos pontos reservados. Titulo, periodo
 * e legenda sao obrigatorios (ver QuadroGrafico + <Legend />).
 */

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PontoSerie } from "@/types";
import { formatarInteiro, rotuloPeriodo, rotuloSemana } from "@/lib/epidemiologia";

import QuadroGrafico from "./QuadroGrafico";
import { Vazio } from "./EstadoUI";

interface GraficoLinhaProps {
  serie: PontoSerie[];
}

interface LinhaDado {
  rotulo: string;
  casos: number;
  reservada: boolean;
}

/** Marcador que destaca os pontos reservados por atraso de notificacao. */
function PontoReservado(props: {
  cx?: number;
  cy?: number;
  payload?: LinhaDado;
}) {
  const { cx, cy, payload } = props;
  if (cx === undefined || cy === undefined || !payload?.reservada) {
    return <g />;
  }
  return (
    <circle
      cx={cx}
      cy={cy}
      r={4}
      fill="var(--cor-reservada)"
      stroke="#8a6d1f"
      strokeWidth={1}
    />
  );
}

export default function GraficoLinha({ serie }: GraficoLinhaProps) {
  const periodo = rotuloPeriodo(serie);

  if (serie.length === 0) {
    return (
      <QuadroGrafico titulo="Serie historica de casos-proxy" periodo={periodo}>
        <Vazio />
      </QuadroGrafico>
    );
  }

  const dados: LinhaDado[] = serie.map((p) => ({
    rotulo: rotuloSemana(p.ano, p.semana),
    casos: p.casos_proxy,
    reservada: p.reservada_atraso_notificacao,
  }));

  // Faixa das semanas reservadas (primeira ate a ultima reservada).
  const indices = dados
    .map((d, i) => (d.reservada ? i : -1))
    .filter((i) => i >= 0);
  const inicioReserva = indices.length > 0 ? dados[indices[0]].rotulo : null;
  const fimReserva =
    indices.length > 0 ? dados[indices[indices.length - 1]].rotulo : null;

  return (
    <QuadroGrafico titulo="Serie historica de casos-proxy" periodo={periodo}>
      <ResponsiveContainer width="100%" height={300}>
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
            formatter={(valor: number) => [formatarInteiro(valor), "Casos-proxy"]}
          />
          <Legend />
          {inicioReserva && fimReserva ? (
            <ReferenceArea
              x1={inicioReserva}
              x2={fimReserva}
              fill="var(--cor-reservada)"
              fillOpacity={0.18}
              label={{
                value: "Reservadas (atraso de notificacao)",
                position: "insideTop",
                fontSize: 10,
                fill: "#8a6d1f",
              }}
            />
          ) : null}
          <Line
            type="monotone"
            dataKey="casos"
            name="Casos-proxy (semanal)"
            stroke="var(--cor-real)"
            strokeWidth={2}
            dot={<PontoReservado />}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="painel-subtitulo" style={{ marginTop: "0.5rem" }}>
        A faixa sombreada e os marcadores em destaque indicam as 8 semanas mais
        recentes reservadas por atraso de notificacao (nao entram no treino).
      </p>
    </QuadroGrafico>
  );
}
