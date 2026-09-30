"""Configuracao de logs estruturados da aplicacao.

Emite logs em formato estruturado (timestamp, nivel, origem, mensagem) para a
saida padrao. E usado pelo middleware de requisicoes e pelos servicos.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURADO = False


def configurar_logs(nivel: int = logging.INFO) -> None:
    """Configura o logger raiz uma unica vez.

    Args:
        nivel: Nivel minimo de log (padrao INFO).
    """
    global _CONFIGURADO
    if _CONFIGURADO:
        return

    formato = "%(asctime)s | %(levelname)s | origem=%(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(formato, datefmt="%Y-%m-%dT%H:%M:%S%z"))

    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    # Evita handlers duplicados quando o modulo e importado mais de uma vez.
    for existente in list(raiz.handlers):
        raiz.removeHandler(existente)
    raiz.addHandler(handler)

    _CONFIGURADO = True


def obter_logger(nome: str) -> logging.Logger:
    """Retorna um logger nomeado, garantindo que os logs estejam configurados.

    Args:
        nome: Nome/origem do logger (ex.: "api.dados").

    Returns:
        Instancia de :class:`logging.Logger`.
    """
    configurar_logs()
    return logging.getLogger(nome)
