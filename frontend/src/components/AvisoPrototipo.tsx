/**
 * Ressalva visivel de protótipo academico.
 *
 * O Manual (secao 2) exige deixar claro que esta ferramenta NAO e um
 * instrumento oficial de vigilancia epidemiologica.
 */
export default function AvisoPrototipo() {
  return (
    <div
      role="note"
      style={{
        background: "var(--cor-aviso-fundo)",
        border: "1px solid var(--cor-aviso-borda)",
        color: "var(--cor-aviso-texto)",
        borderRadius: "var(--raio)",
        padding: "0.75rem 1rem",
        fontSize: "0.9rem",
      }}
    >
      <strong>Protótipo academico (TCC).</strong> Esta aplicacao tem finalidade
      exclusivamente educacional e de pesquisa. Nao constitui ferramenta oficial
      de vigilancia epidemiologica nem substitui fontes oficiais de saude
      publica.
    </div>
  );
}
