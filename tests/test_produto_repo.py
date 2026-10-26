from sqlalchemy.orm import Session

from models import Produto
from repositories.produto_repo import ProdutoRepository


def test_baixar_estoque_com_saldo(sessao: Session, cafe: Produto) -> None:
    repositorio = ProdutoRepository(sessao)
    assert repositorio.baixar_estoque(cafe.id, 2) is True
    assert cafe.estoque_atual == 0


def test_baixar_estoque_sem_saldo_nao_altera(sessao: Session, cafe: Produto) -> None:
    repositorio = ProdutoRepository(sessao)
    assert repositorio.baixar_estoque(cafe.id, 3) is False
    sessao.refresh(cafe)
    assert cafe.estoque_atual == 2


def test_desativar_produto_esconde_do_caixa(sessao: Session, cafe: Produto) -> None:
    repositorio = ProdutoRepository(sessao)
    assert repositorio.desativar_produto(cafe.id) is True
    sessao.commit()
    assert repositorio.buscar_por_codigo("789") is None
    # o registro continua no banco, preservando o histórico de vendas
    assert sessao.get(Produto, cafe.id) is not None


def test_desativar_produto_inexistente(sessao: Session) -> None:
    repositorio = ProdutoRepository(sessao)
    assert repositorio.desativar_produto(999) is False
