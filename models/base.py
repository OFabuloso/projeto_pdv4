import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Classe base de todos os modelos ORM."""


def obter_url_banco() -> str:
    # a URL do banco vem da variável de ambiente, para a senha não ficar no código
    url_banco = os.environ.get("PDV_DATABASE_URL")
    if url_banco is None:
        raise RuntimeError(
            "Defina a variável de ambiente PDV_DATABASE_URL, por exemplo: "
            'export PDV_DATABASE_URL="postgresql+psycopg2://usuario:senha@localhost/projeto_pdv"'
        )
    return url_banco


def criar_engine(url_banco: str | None = None) -> Engine:
    # sem URL explícita, usa a da variável de ambiente
    return create_engine(url_banco or obter_url_banco())


def criar_fabrica_sessoes(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)
