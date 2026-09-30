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

/** Limites de dominio validados no cliente (espelham o contrato do backend). */
const ANO_MINIMO = 2000;
const ANO_MAXIMO = 2100;
const SEMANA_MINIMA = 1;
const SEMANA_MAXIMA = 53;

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

/**
 * Valida o dominio do filtro no cliente antes de chamar a API.
 *
 * Regras (espelham o contrato do backend):
 *  - ano (quando informado) inteiro entre 2000 e 2100;
 *  - semana (quando informada) inteiro entre 1 e 53;
 *  - o par inicio (ano/semana) nao pode ser posterior ao par fim.
 *
 * Retorna a primeira mensagem de erro em PT-BR, ou `null` quando valido.
 */
function validarFiltro(filtro: FiltroPeriodoParams): string | null {
  const { ano_inicio, semana_inicio, ano_fim, semana_fim } = filtro;

  const anos: Array<[number | undefined, string]> = [
    [ano_inicio, "Ano inicio"],
    [ano_fim, "Ano fim"],
  ];
  for (const [ano, rotulo] of anos) {
    if (ano === undefined) {
      continue;
    }
    if (!Number.isInteger(ano) || ano < ANO_MINIMO || ano > ANO_MAXIMO) {
      return `${rotulo} deve ser um ano inteiro entre ${ANO_MINIMO} e ${ANO_MAXIMO}.`;
    }
  }

  const semanas: Array<[number | undefined, string]> = [
    [semana_inicio, "Semana inicio"],
    [semana_fim, "Semana fim"],
  ];
  for (const [semana, rotulo] of semanas) {
    if (semana === undefined) {
      continue;
    }
    if (
      !Number.isInteger(semana) ||
      semana < SEMANA_MINIMA ||
      semana > SEMANA_MAXIMA
    ) {
      return `${rotulo} deve ser uma semana epidemiologica inteira entre ${SEMANA_MINIMA} e ${SEMANA_MAXIMA}.`;
    }
  }

  // Ordem inicio <= fim, comparando por (ano, semana) quando ambos existem.
  if (ano_inicio !== undefined && ano_fim !== undefined) {
    if (ano_inicio > ano_fim) {
      return "O periodo de inicio nao pode ser posterior ao periodo de fim.";
    }
    if (
      ano_inicio === ano_fim &&
      semana_inicio !== undefined &&
      semana_fim !== undefined &&
      semana_inicio > semana_fim
    ) {
      return "No mesmo ano, a semana de inicio nao pode ser posterior a semana de fim.";
    }
  }

  return null;
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
  const [erroValidacao, setErroValidacao] = useState<string | null>(null);

  function aplicar(evento: React.FormEvent) {
    evento.preventDefault();
    const filtro: FiltroPeriodoParams = {
      ano_inicio: paraNumero(anoInicio),
      semana_inicio: paraNumero(semanaInicio),
      ano_fim: paraNumero(anoFim),
      semana_fim: paraNumero(semanaFim),
    };

    // Validacao de dominio no cliente: bloqueia submit invalido antes da API.
    const erro = validarFiltro(filtro);
    if (erro !== null) {
      setErroValidacao(erro);
      return;
    }

    setErroValidacao(null);
    aoAplicar(filtro);
  }

  function limpar() {
    setAnoInicio("");
    setSemanaInicio("");
    setAnoFim("");
    setSemanaFim("");
    setErroValidacao(null);
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

      {erroValidacao ? (
        <p
          className="aviso-inline"
          role="alert"
          aria-live="assertive"
          style={{ marginTop: "0.75rem" }}
        >
          {erroValidacao}
        </p>
      ) : null}
    </form>
  );
}
