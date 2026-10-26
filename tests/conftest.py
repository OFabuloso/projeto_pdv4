from collections.abc import Iterator
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from models import Produto, TurnoCaixa
from models.base import Base, criar_engine, criar_fabrica_sessoes


@pytest.fixture
def sessao() -> Iterator[Session]:
    # banco SQLite em memória: cada teste começa com as tabelas vazias
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    with criar_fabrica_sessoes(engine)() as sessao_teste:
        yield sessao_teste
    engine.dispose()


@pytest.fixture
def cafe(sessao: Session) -> Produto:
    produto = Produto(
        codigo_barras="789", nome="Café", preco=Decimal("10.00"), estoque_atual=2
    )
    sessao.add(produto)
    sessao.commit()
    return produto


@pytest.fixture
def turno(sessao: Session) -> TurnoCaixa:
    turno_aberto = TurnoCaixa(operador="Ana", valor_abertura=Decimal("50.00"))
    sessao.add(turno_aberto)
    sessao.commit()
    return turno_aberto
