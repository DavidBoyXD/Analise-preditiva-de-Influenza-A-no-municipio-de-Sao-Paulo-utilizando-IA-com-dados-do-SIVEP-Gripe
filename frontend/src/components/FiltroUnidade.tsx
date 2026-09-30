"use client";

/**
 * Filtro de UNIDADE DE NOTIFICACAO alimentado por /api/unidades-notificacao.
 *
 * TRATAMENTO HONESTO da pendencia de dados: a fonte atual NAO popula
 * NM_UN_INTE (fonte_populada=false, nm_un_inte=null). Nesse caso o seletor
 * permanece DESABILITADO e exibe uma mensagem clara da pendencia documentada.
 * NUNCA inventamos/fabricamos unidades. Se, no futuro, a fonte popular o campo,
 * o seletor passa a listar as unidades reais automaticamente.
 */

import { useCallback, useEffect, useState } from "react";

import { getUnidadesNotificacao } from "@/services";
import { ErroApi } from "@/services";
import type { UnidadeNotificacao } from "@/types";

import { Carregando, Erro } from "./EstadoUI";

const MENSAGEM_PENDENCIA =
  "Filtro por unidade indisponivel: a fonte de dados atual nao populou NM_UN_INTE (pendencia documentada). O prototipo trabalha no agregado do municipio de Sao Paulo.";

export default function FiltroUnidade() {
  const [unidades, setUnidades] = useState<UnidadeNotificacao[] | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await getUnidadesNotificacao();
      setUnidades(resultado);
    } catch (e) {
      const mensagem =
        e instanceof ErroApi
          ? e.message
          : "Nao foi possivel carregar as unidades de notificacao.";
      setErro(mensagem);
      setUnidades(null);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  // Unidades efetivamente utilizaveis: apenas as com fonte populada e nome.
  const unidadesUtilizaveis = (unidades ?? []).filter(
    (u) => u.fonte_populada && u.nm_un_inte,
  );
  const fonteNaoPopulada =
    unidades !== null && unidadesUtilizaveis.length === 0;

  return (
    <section className="painel" aria-labelledby="titulo-filtro-unidade">
      <h2 id="titulo-filtro-unidade" className="painel-titulo">
        Filtro por unidade de notificacao
      </h2>
      <p className="painel-subtitulo">
        Unidades dentro do municipio de Sao Paulo (campo NM_UN_INTE).
      </p>

      <div style={{ marginTop: "0.75rem" }}>
        {carregando ? (
          <Carregando rotulo="Carregando unidades..." />
        ) : erro ? (
          <Erro mensagem={erro} aoTentarNovamente={carregar} />
        ) : fonteNaoPopulada ? (
          <>
            <div className="campo">
              <label htmlFor="filtro-unidade">Unidade</label>
              <select id="filtro-unidade" disabled aria-describedby="aviso-unidade">
                <option>Sem unidades disponiveis</option>
              </select>
            </div>
            <p id="aviso-unidade" className="aviso-inline" style={{ marginTop: "0.6rem" }}>
              {MENSAGEM_PENDENCIA}
            </p>
          </>
        ) : (
          <div className="campo">
            <label htmlFor="filtro-unidade">Unidade</label>
            <select id="filtro-unidade">
              <option value="">Todas as unidades</option>
              {unidadesUtilizaveis.map((u) => (
                <option key={u.id_unidade_notificacao} value={u.id_unidade_notificacao}>
                  {u.nm_un_inte}
                </option>
              ))}
            </select>
            <p className="painel-subtitulo" style={{ marginTop: "0.4rem" }}>
              Observacao: a API ainda nao expoe consulta filtrada por unidade; o
              seletor lista as unidades reais quando a fonte as popula.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
