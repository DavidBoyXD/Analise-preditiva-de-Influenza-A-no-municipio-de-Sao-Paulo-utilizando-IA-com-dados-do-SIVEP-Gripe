"""Ponto de entrada da API REST (FastAPI) do TCC de Influenza A.

Inicializa o aplicativo FastAPI, configura CORS, middleware de logs de
requisicoes, handlers globais de excecoes (que retornam o envelope JSON
padronizado sem vazar stack trace) e habilita a documentacao OpenAPI/Swagger
em /docs. O modelo preditivo e carregado em memoria no startup (com fallback
para baseline), garantindo que uma eventual falha do modulo preditivo NAO
derrube os endpoints de dados historicos (RF002 / tolerancia a falhas).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging_config import obter_logger
from app.routes.api import router as api_router
from app.schemas.common import resposta_erro
from app.services.erros import ErroValidacao, PrevisaoIndisponivel, RecursoNaoEncontrado
from app.services.previsao_service import carregar_modelo

logger = obter_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicacao: carrega o modelo no startup.

    A carga do modelo e tolerante a falhas (nunca impede a subida da API); se
    nao houver .joblib, a API segue usando o baseline.
    """
    settings = get_settings()
    logger.info("Iniciando %s v%s.", settings.app_nome, settings.app_versao)
    try:
        carregar_modelo()
    except Exception as exc:  # nunca impedir o startup por falha do modelo
        logger.warning("Falha ao carregar modelo no startup (%s); usando baseline.", exc)
    yield
    logger.info("Encerrando a API.")


def criar_app() -> FastAPI:
    """Cria e configura a instancia do FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_nome,
        version=settings.app_versao,
        description=(
            "API REST para consulta de dados historicos, series temporais, "
            "previsoes e metricas do modelo de analise preditiva de Influenza A "
            "no municipio de Sao Paulo (dados do SIVEP-Gripe/DATASUS). Prototipo "
            "academico (TCC) - nao e ferramenta oficial de vigilancia."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origens,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def registrar_requisicoes(request: Request, call_next):
        """Middleware que registra cada requisicao (metodo, rota, status, tempo)."""
        inicio = time.perf_counter()
        resposta = await call_next(request)
        duracao_ms = (time.perf_counter() - inicio) * 1000
        logger.info(
            "requisicao metodo=%s rota=%s status=%s duracao_ms=%.1f",
            request.method,
            request.url.path,
            resposta.status_code,
            duracao_ms,
        )
        return resposta

    _registrar_handlers(app)
    app.include_router(api_router)

    @app.get("/", tags=["Sistema"], summary="Informacoes basicas da API")
    def raiz() -> dict:
        """Retorna informacoes basicas e o caminho da documentacao."""
        return {
            "sucesso": True,
            "dados": {"documentacao": "/docs", "status": "/api/status"},
            "mensagem": f"{settings.app_nome} - consulte /docs para a documentacao.",
        }

    return app


def _registrar_handlers(app: FastAPI) -> None:
    """Registra os handlers globais de excecao com envelope JSON padronizado."""

    @app.exception_handler(ErroValidacao)
    async def _handler_validacao(request: Request, exc: ErroValidacao):
        logger.info("Validacao rejeitada em %s: %s", request.url.path, exc)
        return JSONResponse(status_code=400, content=resposta_erro(str(exc)))

    @app.exception_handler(RequestValidationError)
    async def _handler_request_validation(request: Request, exc: RequestValidationError):
        logger.info("Parametros invalidos em %s.", request.url.path)
        return JSONResponse(
            status_code=422,
            content=resposta_erro(
                "Parametros de requisicao invalidos. Verifique os valores informados."
            ),
        )

    @app.exception_handler(RecursoNaoEncontrado)
    async def _handler_nao_encontrado(request: Request, exc: RecursoNaoEncontrado):
        logger.info("Recurso nao encontrado em %s: %s", request.url.path, exc)
        return JSONResponse(status_code=404, content=resposta_erro(str(exc)))

    @app.exception_handler(PrevisaoIndisponivel)
    async def _handler_previsao(request: Request, exc: PrevisaoIndisponivel):
        # Falha isolada do modulo preditivo: 503, sem derrubar os demais endpoints.
        logger.warning("Previsao indisponivel em %s: %s", request.url.path, exc)
        return JSONResponse(status_code=503, content=resposta_erro(str(exc)))

    @app.exception_handler(Exception)
    async def _handler_generico(request: Request, exc: Exception):
        # Nunca vaza stack trace ao cliente; detalhes ficam apenas no log.
        logger.error("Erro nao tratado em %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content=resposta_erro("Ocorreu um erro interno. Tente novamente mais tarde."),
        )


app = criar_app()
