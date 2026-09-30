"use client";

/**
 * Grafico de BARRAS: casos-proxy agregados por ano epidemiologico no periodo
 * filtrado. Titulo, periodo e legenda obrigatorios.
 */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PontoSerie } from "@/types";
import { agregarPorAno, formatarInteiro, rotuloPeriodo } from "@/lib/epidemiologia";

import QuadroGrafico from "./QuadroGrafico";
import { Vazio } from "./EstadoUI";

interface GraficoBarrasProps {
  serie: PontoSerie[];
}

export default function GraficoBarras({ serie }: GraficoBarrasProps) {
  const periodo = rotuloPeriodo(serie);

  if (serie.length === 0) {
    return (
      <QuadroGrafico titulo="Casos-proxy por ano epidemiologico" periodo={periodo}>
        <Vazio />
      </QuadroGrafico>
    );
  }

  const dados = agregarPorAno(serie).map((item) => ({
    ano: String(item.ano),
    casos: item.casos_proxy,
    semanas: item.semanas,
  }));

  return (
    <QuadroGrafico titulo="Casos-proxy por ano epidemiologico" periodo={periodo}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={dados} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--cor-borda)" />
          <XAxis dataKey="ano" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
          <Tooltip
            formatter={(valor: number) => [formatarInteiro(valor), "Casos-proxy"]}
            labelFormatter={(rotulo: string) => `Ano ${rotulo}`}
          />
          <Legend />
          <Bar
            dataKey="casos"
            name="Casos-proxy (total no ano)"
            fill="var(--cor-real)"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      <p className="painel-subtitulo" style={{ marginTop: "0.5rem" }}>
        Soma dos casos-proxy semanais em cada ano epidemiologico do periodo
        filtrado.
      </p>
    </QuadroGrafico>
  );
}
