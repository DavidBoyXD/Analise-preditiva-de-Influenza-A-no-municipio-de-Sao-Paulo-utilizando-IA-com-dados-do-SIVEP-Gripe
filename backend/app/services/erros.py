"""Excecoes de dominio usadas pela camada de servicos."""

from __future__ import annotations


class ErroValidacao(Exception):
    """Erro de validacao de entrada (ex.: intervalo de periodo invertido)."""


class RecursoNaoEncontrado(Exception):
    """Recurso solicitado nao foi encontrado (ex.: modelo ativo inexistente)."""


class PrevisaoIndisponivel(Exception):
    """Falha no modulo preditivo. NAO deve derrubar endpoints de dados historicos."""
