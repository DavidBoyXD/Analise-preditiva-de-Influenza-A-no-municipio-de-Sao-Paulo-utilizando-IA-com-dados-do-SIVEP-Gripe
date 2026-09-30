"use client";

/**
 * Orquestrador do dashboard (client component).
 *
 * Responsabilidades:
 *  - manter o filtro de periodo e refazer a consulta a /api/dados ao aplicar;
 *  - buscar as previsoes de /api/previsoes de forma INDEPENDENTE do historico,
 *    para permitir DEGRADACAO ELEGANTE: se a previsao falhar (503), o historico
 *    e os cards continuam renderizando; apenas o bloco de previsao mostra aviso;
 *  - distribuir os dados para cards e graficos.
 *
 * Toda a busca de dados passa pela camada de servicos da FEAT-001 (API real via
 * NEXT_PUBLIC_API_URL). O mock e apenas fallback de desenvolvimento marcado.
 */

import { useCallback, useEffect, useState } from "react";

import {
  ErroApi,
  PrevisaoIndisponivelError,
  USANDO_MOCK,
  getDados,
  getPrevisoes,
} from "@/services";
import type { FiltroPeriodo as FiltroPeriodoParams } from "@/services";
import type { PontoSerie, PrevisaoResposta } from "@/types";

import CardsIndicadores from "./CardsIndicadores";
import FiltroPeriodo from "./FiltroPeriodo";
import FiltroUnidade from "./FiltroUnidade";
import GraficoBarras from "./GraficoBarras";
import GraficoComparacao from "./GraficoComparacao";
import GraficoLinha from "./GraficoLinha";
import PainelMetricas from "./PainelMetricas";
import { Carregando, Erro, Vazio } from "./EstadoUI";

/** Horizonte padrao de previsao (semanas). */
const HORIZONTE_PADRAO = 6;

export default function Dashboard() {
  const [filtro, setFiltro] = useState<FiltroPeriodoParams>({});

  // Estado da serie historica (/api/dados).
  const [serie, setSerie] = useState<PontoSerie[] | null>(null);
  const [carregandoSerie, setCarregandoSerie] = useState(true);
  const [erroSerie, setErroSerie] = useState<string | null>(null);

  // Estado das previsoes (/api/previsoes) - independente do historico.
  const [previsao, setPrevisao] = useState<PrevisaoResposta | null>(null);
  const [carregandoPrevisao, setCarregandoPrevisao] = useState(true);
  const [previsaoIndisponivel, setPrevisaoIndisponivel] = useState(false);
  const [erroPrevisao, setErroPrevisao] = useState<string | null>(null);

  const carregarSerie = useCallback(async (filtroAtual: FiltroPeriodoParams) => {
    setCarregandoSerie(true);
    setErroSerie(null);
    try {
      const resultado = await getDados(filtroAtual);
      setSerie(resultado);
    } catch (e) {
      setErroSerie(
        e instanceof ErroApi
          ? e.message
          : "Nao foi possivel carregar a serie historica.",
      );
      setSerie(null);
    } finally {
      setCarregandoSerie(false);
    }
  }, []);

  const carregarPrevisao = useCallback(async () => {
    setCarregandoPrevisao(true);
    setErroPrevisao(null);
    setPrevisaoIndisponivel(false);
    try {
      const resultado = await getPrevisoes({ horizonte: HORIZONTE_PADRAO });
      setPrevisao(resultado);
    } catch (e) {
      // 503 = degradacao elegante (aviso apenas no bloco de previsao).
      if (e instanceof PrevisaoIndisponivelError) {
        setPrevisaoIndisponivel(true);
        setPrevisao(null);
      } else {
        setErroPrevisao(
          e instanceof ErroApi
            ? e.message
            : "Nao foi possivel carregar as previsoes.",
        );
        setPrevisao(null);
      }
    } finally {
      setCarregandoPrevisao(false);
    }
  }, []);

  useEffect(() => {
    void carregarSerie(filtro);
  }, [carregarSerie, filtro]);

  useEffect(() => {
    void carregarPrevisao();
  }, [carregarPrevisao]);

  const serieSegura = serie ?? [];
  const origemModelo = previsao?.origem_modelo ?? null;
  const nomeModelo = previsao?.nome_modelo ?? null;

  return (
    <>
      {USANDO_MOCK ? (
        <div className="aviso-inline" role="note" style={{ marginBottom: "1rem" }}>
          Modo de desenvolvimento com dados fictícios (mock) ativo. Esta NAO e a
          versao final; a versao final consome a API real.
        </div>
      ) : null}

      {/* Filtros */}
      <div className="barra-filtros">
        <FiltroPeriodo
          valorInicial={filtro}
          aoAplicar={setFiltro}
          desabilitado={carregandoSerie}
        />
        <FiltroUnidade />
      </div>

      {/* Cards de indicadores (dependem apenas do historico) */}
      <section aria-label="Indicadores" style={{ marginBottom: "0.5rem" }}>
        {carregandoSerie ? (
          <div className="painel">
            <Carregando rotulo="Carregando indicadores..." />
          </div>
        ) : erroSerie ? (
          <div className="painel">
            <Erro mensagem={erroSerie} aoTentarNovamente={() => carregarSerie(filtro)} />
          </div>
        ) : serieSegura.length === 0 ? (
          <div className="painel">
            <Vazio />
          </div>
        ) : (
          <CardsIndicadores
            serie={serieSegura}
            origemModelo={origemModelo}
            nomeModelo={nomeModelo}
            previsaoIndisponivel={previsaoIndisponivel}
            erroPrevisao={erroPrevisao !== null}
          />
        )}
      </section>

      {/* Graficos */}
      <div className="grid-graficos">
        <div className="grid-graficos-largo">
          {carregandoSerie ? (
            <div className="painel">
              <Carregando rotulo="Carregando serie historica..." />
            </div>
          ) : erroSerie ? (
            <div className="painel">
              <Erro
                mensagem={erroSerie}
                aoTentarNovamente={() => carregarSerie(filtro)}
              />
            </div>
          ) : (
            <GraficoLinha serie={serieSegura} />
          )}
        </div>

        {carregandoSerie ? (
          <div className="painel">
            <Carregando rotulo="Carregando grafico de barras..." />
          </div>
        ) : erroSerie ? (
          <div className="painel">
            <Erro mensagem={erroSerie} aoTentarNovamente={() => carregarSerie(filtro)} />
          </div>
        ) : (
          <GraficoBarras serie={serieSegura} />
        )}

        <PainelMetricas />

        {/* Comparacao real x previsto: degrada de forma independente */}
        <div className="grid-graficos-largo">
          {carregandoSerie ? (
            <div className="painel">
              <Carregando rotulo="Carregando comparacao..." />
            </div>
          ) : erroSerie ? (
            <div className="painel">
              <Erro
                mensagem={erroSerie}
                aoTentarNovamente={() => carregarSerie(filtro)}
              />
            </div>
          ) : (
            <GraficoComparacao
              serieReal={serieSegura}
              previsao={previsao}
              carregandoPrevisao={carregandoPrevisao}
              previsaoIndisponivel={previsaoIndisponivel}
              erroPrevisao={erroPrevisao}
              aoTentarNovamente={carregarPrevisao}
            />
          )}
        </div>
      </div>
    </>
  );
}
