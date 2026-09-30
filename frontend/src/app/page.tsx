import Dashboard from "@/components/Dashboard";
import Rodape from "@/components/Rodape";

/**
 * Pagina principal do dashboard de Influenza A (municipio de Sao Paulo).
 *
 * O cabecalho e o rodape (com a ressalva de protótipo academico) sao renderizados
 * no servidor; o corpo interativo (filtros, cards e graficos) fica no
 * componente cliente Dashboard, que consome a API real via a camada de servicos.
 */
export default function Home() {
  return (
    <main className="conteudo-principal">
      <header className="cabecalho-dashboard">
        <h1>Dashboard de Influenza A - Municipio de Sao Paulo</h1>
        <p>
          Analise preditiva de casos-proxy de Influenza A com dados do
          SIVEP-Gripe/DATASUS, por semana epidemiologica.
        </p>
      </header>

      <Dashboard />

      <Rodape />
    </main>
  );
}
