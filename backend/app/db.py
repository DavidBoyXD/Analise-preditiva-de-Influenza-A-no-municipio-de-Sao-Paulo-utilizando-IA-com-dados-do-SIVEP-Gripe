"""Engine e sessao do SQLAlchemy.

Cria o engine a partir de `DATABASE_URL` (via configuracoes). O codigo e
compativel tanto com PostgreSQL (producao) quanto com SQLite (testes e
desenvolvimento local): para SQLite adiciona-se `check_same_thread=False` para
uso com o TestClient do FastAPI.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Classe base declarativa dos modelos ORM."""


def _criar_engine():
    """Cria o engine do SQLAlchemy conforme o dialeto de `DATABASE_URL`."""
    settings = get_settings()
    url = settings.database_url
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # Necessario para uso do SQLite com multiplas threads (TestClient).
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, future=True)


engine = _criar_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Dependencia do FastAPI que fornece uma sessao de banco por requisicao.

    Yields:
        Sessao SQLAlchemy encerrada automaticamente ao final da requisicao.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
