"use client";

/**
 * Painel de METRICAS de avaliacao do modelo (/api/metricas).
 *
 * Exibe MAE/RMSE/MAPE, acerto direcional e o teste de significancia com
 * HONESTIDADE: campos null viram placeholder claro. Deixa explicito que e a
 * avaliacao do prototipo, nao um indicador oficial. Estados de loading/erro/
 * vazio proprios. A falha aqui nao afeta o restante do dashboard.
 */

import { useCallback, useEffect, useState } from "react";

import { ErroApi, getMetricas } from "@/services";
import type { MetricaResposta } from "@/types";
import {
  formatarDecimal,
  formatarPercentual,
} from "@/lib/epidemiologia";

import { Carregando, Erro, Vazio } from "./EstadoUI";

function Linha({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <tr>
      <th scope="row" style={{ fontWeight: 600 }}>
        {rotulo}
      </th>
      <td>{valor}</td>
    </tr>
  );
}

export default function PainelMetricas() {
  const [metricas, setMetricas] = useState<MetricaResposta | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await getMetricas();
      setMetricas(resultado);
    } catch (e) {
      setErro(
        e instanceof ErroApi
          ? e.message
          : "Nao foi possivel carregar as metricas do modelo.",
      );
      setMetricas(null);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  let corpo: React.ReactNode;
  if (carregando) {
    corpo = <Carregando rotulo="Carregando metricas..." />;
  } else if (erro) {
    corpo = <Erro mensagem={erro} aoTentarNovamente={carregar} />;
  } else if (!metricas) {
    corpo = <Vazio mensagem="Sem metricas de avaliacao disponiveis." />;
  } else {
    const significancia =
      metricas.significativo === null
        ? "indisponivel"
        : metricas.significativo
          ? "significativo"
          : "nao significativo";
    corpo = (
      <table className="legenda-tabela">
        <caption className="visualmente-oculto">
          Metricas de avaliacao do modelo preditivo do prototipo.
        </caption>
        <tbody>
          <Linha rotulo="Modelo" valor={metricas.nome_modelo} />
          <Linha rotulo="Versao" valor={metricas.versao} />
          <Linha rotulo="Algoritmo" valor={metricas.algoritmo} />
          <Linha rotulo="MAE" valor={formatarDecimal(metricas.mae)} />
          <Linha rotulo="RMSE" valor={formatarDecimal(metricas.rmse)} />
          <Linha rotulo="MAPE" valor={formatarPercentual(metricas.mape)} />
          <Linha
            rotulo="Acerto direcional"
            valor={formatarPercentual(metricas.acerto_direcional)}
          />
          <Linha
            rotulo="Teste de significancia"
            valor={metricas.teste_significancia ?? "indisponivel"}
          />
          <Linha rotulo="p-valor" valor={formatarDecimal(metricas.p_valor, 3)} />
          <Linha rotulo="Resultado" valor={significancia} />
        </tbody>
      </table>
    );
  }

  return (
    <section className="painel" aria-labelledby="titulo-metricas">
      <h2 id="titulo-metricas" className="painel-titulo">
        Avaliacao do modelo (prototipo)
      </h2>
      <p className="painel-subtitulo">
        Metricas do prototipo academico. Nao constituem indicador oficial de
        desempenho.
      </p>
      <div style={{ marginTop: "0.75rem" }}>{corpo}</div>
    </section>
  );
}
