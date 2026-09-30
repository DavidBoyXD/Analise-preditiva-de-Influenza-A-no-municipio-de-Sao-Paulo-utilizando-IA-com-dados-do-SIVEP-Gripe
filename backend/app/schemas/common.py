"""Envelope JSON padronizado de resposta da API.

Todas as respostas da API seguem o formato {sucesso, dados, mensagem} para
padronizar o consumo pelo frontend e simplificar o tratamento de erros.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class RespostaPadrao(BaseModel, Generic[T]):
    """Envelope padrao de resposta da API.

    Atributos:
        sucesso: Indica se a operacao foi concluida com sucesso.
        dados: Carga util da resposta (pode ser objeto, lista ou nulo).
        mensagem: Mensagem descritiva em Portugues-Brasil.
    """

    sucesso: bool = Field(description="Indica se a requisicao foi bem-sucedida.")
    dados: T | None = Field(
        default=None, description="Conteudo retornado pela operacao (dados de negocio)."
    )
    mensagem: str = Field(description="Mensagem descritiva do resultado (Portugues-Brasil).")


def resposta_ok(dados: object, mensagem: str = "Operacao realizada com sucesso.") -> dict:
    """Monta um envelope de sucesso.

    Args:
        dados: Carga util a ser retornada.
        mensagem: Mensagem descritiva.

    Returns:
        Dicionario no formato padronizado {sucesso, dados, mensagem}.
    """
    return {"sucesso": True, "dados": dados, "mensagem": mensagem}


def resposta_erro(mensagem: str, dados: object | None = None) -> dict:
    """Monta um envelope de erro (sem vazar detalhes internos).

    Args:
        mensagem: Mensagem de erro clara para o consumidor.
        dados: Detalhes adicionais opcionais (nunca stack trace).

    Returns:
        Dicionario no formato padronizado {sucesso, dados, mensagem}.
    """
    return {"sucesso": False, "dados": dados, "mensagem": mensagem}
