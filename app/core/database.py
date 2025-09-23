"""
Configuração do banco de dados
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
from typing import AsyncGenerator

from app.core.config import settings

# Criar engine do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Metadata
metadata = MetaData()


async def init_db():
    """Inicializar banco de dados"""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado com sucesso")


def get_db() -> AsyncGenerator:
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator:
    """Dependency assíncrona para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
