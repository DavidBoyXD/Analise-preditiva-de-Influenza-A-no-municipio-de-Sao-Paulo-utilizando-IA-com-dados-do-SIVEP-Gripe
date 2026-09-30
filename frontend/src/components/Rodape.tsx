import AvisoPrototipo from "./AvisoPrototipo";

/**
 * Rodape do dashboard com a ressalva de protótipo academico (reutiliza
 * AvisoPrototipo) e a atribuicao da fonte de dados.
 */
export default function Rodape() {
  return (
    <footer className="rodape-dashboard">
      <AvisoPrototipo />
      <p style={{ marginTop: "0.75rem" }}>
        Protótipo academico (TCC). Nao e ferramenta oficial de vigilancia
        epidemiologica. Fonte: SIVEP-Gripe/DATASUS. Recorte: municipio de Sao
        Paulo.
      </p>
    </footer>
  );
}
