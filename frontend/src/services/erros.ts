/**
 * Erros tipados da camada de servicos, para que a UI distinga os casos.
 */

/** Erro geral de comunicacao/negocio com a API (rede, 4xx, 5xx, envelope falho). */
export class ErroApi extends Error {
  /** Codigo HTTP quando disponivel (0 para falha de rede). */
  readonly status: number;

  constructor(mensagem: string, status = 0) {
    super(mensagem);
    this.name = "ErroApi";
    this.status = status;
  }
}

/**
 * Estado especifico de "previsao indisponivel" (HTTP 503 em /api/previsoes).
 *
 * Distinto de um erro geral: permite degradacao elegante, mantendo o historico
 * visivel mesmo quando o preditor esta fora do ar. A UI deve tratar este caso
 * como um aviso ("previsao temporariamente indisponivel"), nao como falha.
 */
export class PrevisaoIndisponivelError extends ErroApi {
  constructor(mensagem = "Previsao temporariamente indisponivel.") {
    super(mensagem, 503);
    this.name = "PrevisaoIndisponivelError";
  }
}
