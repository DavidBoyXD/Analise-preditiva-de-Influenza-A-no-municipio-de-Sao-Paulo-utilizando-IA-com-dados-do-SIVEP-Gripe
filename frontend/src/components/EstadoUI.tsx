/**
 * Estados de UI reutilizaveis (carregando / erro / vazio).
 *
 * Padroniza o feedback de todos os blocos que buscam dados, em PT-BR e sem
 * expor stack trace ao usuario. O estado de erro oferece "tentar novamente".
 */

/** Indicador de carregamento com rotulo acessivel. */
export function Carregando({ rotulo = "Carregando dados..." }: { rotulo?: string }) {
  return (
    <div className="estado-ui" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <span>{rotulo}</span>
    </div>
  );
}

/** Mensagem de erro amigavel, opcionalmente com acao de recarregar. */
export function Erro({
  mensagem,
  aoTentarNovamente,
}: {
  mensagem: string;
  aoTentarNovamente?: () => void;
}) {
  return (
    <div className="estado-ui estado-erro" role="alert">
      <span>{mensagem}</span>
      {aoTentarNovamente ? (
        <button
          type="button"
          className="botao botao-secundario"
          onClick={aoTentarNovamente}
        >
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}

/** Estado vazio (consulta valida, porem sem registros). */
export function Vazio({
  mensagem = "Nenhum dado disponivel para o periodo selecionado.",
}: {
  mensagem?: string;
}) {
  return (
    <div className="estado-ui" role="status">
      <span>{mensagem}</span>
    </div>
  );
}
