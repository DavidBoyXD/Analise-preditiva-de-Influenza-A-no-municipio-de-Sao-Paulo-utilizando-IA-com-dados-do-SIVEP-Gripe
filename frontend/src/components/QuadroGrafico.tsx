"use client";

/**
 * Moldura padrao de um grafico: garante TITULO, PERIODO (subtitulo) e area de
 * conteudo consistentes em todos os graficos do dashboard. A legenda propria
 * de cada serie fica dentro do grafico (Recharts <Legend />).
 */

interface QuadroGraficoProps {
  titulo: string;
  periodo: string;
  /** Conteudo extra no cabecalho (ex.: selo de origem do modelo). */
  acessorio?: React.ReactNode;
  children: React.ReactNode;
}

export default function QuadroGrafico({
  titulo,
  periodo,
  acessorio,
  children,
}: QuadroGraficoProps) {
  return (
    <section className="painel" aria-label={titulo}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2 className="painel-titulo">{titulo}</h2>
          <p className="painel-subtitulo">Periodo: {periodo}</p>
        </div>
        {acessorio ? <div>{acessorio}</div> : null}
      </div>
      <div style={{ marginTop: "0.75rem" }}>{children}</div>
    </section>
  );
}
