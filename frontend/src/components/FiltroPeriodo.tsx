"use client";

/**
 * Filtro de PERIODO por ano/semana epidemiologica de inicio e fim.
 *
 * Semana epidemiologica no intervalo 1..53. Ao aplicar, chama `aoAplicar` com o
 * filtro (campos vazios viram undefined, para nao restringir a consulta). Os
 * rotulos sao associados aos controles via htmlFor/id para acessibilidade.
 */

import { useState } from "react";

import type { FiltroPeriodo as FiltroPeriodoParams } from "@/services";

interface FiltroPeriodoProps {
  /** Valor atual aplicado (para inicializar os campos). */
  valorInicial?: FiltroPeriodoParams;
  /** Chamado ao aplicar o filtro. */
  aoAplicar: (filtro: FiltroPeriodoParams) => void;
  /** Desabilita os controles (ex.: durante carregamento). */
  desabilitado?: boolean;
}

/** Converte string do input para numero ou undefined. */
function paraNumero(valor: string): number | undefined {
  if (valor.trim() === "") {
    return undefined;
  }
  const n = Number(valor);
  return Number.isFinite(n) ? n : undefined;
}

export default function FiltroPeriodo({
  valorInicial = {},
  aoAplicar,
  desabilitado = false,
}: FiltroPeriodoProps) {
  const [anoInicio, setAnoInicio] = useState(
    valorInicial.ano_inicio?.toString() ?? "",
  );
  const [semanaInicio, setSemanaInicio] = useState(
    valorInicial.semana_inicio?.toString() ?? "",
  );
  const [anoFim, setAnoFim] = useState(valorInicial.ano_fim?.toString() ?? "");
  const [semanaFim, setSemanaFim] = useState(
    valorInicial.semana_fim?.toString() ?? "",
  );

  function aplicar(evento: React.FormEvent) {
    evento.preventDefault();
    aoAplicar({
      ano_inicio: paraNumero(anoInicio),
      semana_inicio: paraNumero(semanaInicio),
      ano_fim: paraNumero(anoFim),
      semana_fim: paraNumero(semanaFim),
    });
  }

  function limpar() {
    setAnoInicio("");
    setSemanaInicio("");
    setAnoFim("");
    setSemanaFim("");
    aoAplicar({});
  }

  return (
    <form className="painel" onSubmit={aplicar} aria-labelledby="titulo-filtro-periodo">
      <h2 id="titulo-filtro-periodo" className="painel-titulo">
        Filtro por periodo
      </h2>
      <p className="painel-subtitulo">
        Ano e semana epidemiologica (1 a 53) de inicio e fim.
      </p>

      <div className="grupo-campos" style={{ marginTop: "0.75rem" }}>
        <div className="campo">
          <label htmlFor="ano-inicio">Ano inicio</label>
          <input
            id="ano-inicio"
            name="ano-inicio"
            type="number"
            inputMode="numeric"
            min={2000}
            max={2100}
            placeholder="ex.: 2022"
            value={anoInicio}
            onChange={(e) => setAnoInicio(e.target.value)}
            disabled={desabilitado}
          />
        </div>
        <div className="campo">
          <label htmlFor="semana-inicio">Semana inicio</label>
          <input
            id="semana-inicio"
            name="semana-inicio"
            type="number"
            inputMode="numeric"
            min={1}
            max={53}
            placeholder="1-53"
            value={semanaInicio}
            onChange={(e) => setSemanaInicio(e.target.value)}
            disabled={desabilitado}
          />
        </div>
        <div className="campo">
          <label htmlFor="ano-fim">Ano fim</label>
          <input
            id="ano-fim"
            name="ano-fim"
            type="number"
            inputMode="numeric"
            min={2000}
            max={2100}
            placeholder="ex.: 2024"
            value={anoFim}
            onChange={(e) => setAnoFim(e.target.value)}
            disabled={desabilitado}
          />
        </div>
        <div className="campo">
          <label htmlFor="semana-fim">Semana fim</label>
          <input
            id="semana-fim"
            name="semana-fim"
            type="number"
            inputMode="numeric"
            min={1}
            max={53}
            placeholder="1-53"
            value={semanaFim}
            onChange={(e) => setSemanaFim(e.target.value)}
            disabled={desabilitado}
          />
        </div>
        <div className="campo" style={{ flexDirection: "row", gap: "0.5rem" }}>
          <button type="submit" className="botao" disabled={desabilitado}>
            Aplicar
          </button>
          <button
            type="button"
            className="botao botao-secundario"
            onClick={limpar}
            disabled={desabilitado}
          >
            Limpar
          </button>
        </div>
      </div>
    </form>
  );
}
