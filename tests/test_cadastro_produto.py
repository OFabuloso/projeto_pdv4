from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from models import Produto
from services.cadastro_produto import CadastroProdutoService


def test_cadastrar_produto(sessao: Session) -> None:
    cadastro = CadastroProdutoService(sessao)
    produto = cadastro.cadastrar(" 123 ", " Leite ", Decimal("5.50"), 10)
    assert produto.id is not None
    assert produto.codigo_barras == "123"
    assert produto.nome == "Leite"
    assert produto.ativo is True
    assert cadastro.listar() == [produto]


@pytest.mark.parametrize(
    ("codigo_barras", "nome", "preco", "estoque_inicial", "mensagem"),
    [
        ("", "Leite", Decimal("1"), 0, "código de barras"),
        ("123", " ", Decimal("1"), 0, "nome"),
        ("123", "Leite", Decimal("-1"), 0, "preço"),
        ("123", "Leite", Decimal("1"), -1, "estoque"),
    ],
)
def test_cadastrar_valida_campos(
    sessao: Session,
    codigo_barras: str,
    nome: str,
    preco: Decimal,
    estoque_inicial: int,
    mensagem: str,
) -> None:
    cadastro = CadastroProdutoService(sessao)
    with pytest.raises(ValueError, match=mensagem):
        cadastro.cadastrar(codigo_barras, nome, preco, estoque_inicial)


def test_cadastrar_codigo_repetido_mesmo_inativo(
    sessao: Session, cafe: Produto
) -> None:
    cadastro = CadastroProdutoService(sessao)
    cadastro.desativar("789")
    with pytest.raises(ValueError, match="Já existe"):
        cadastro.cadastrar("789", "Outro café", Decimal("1.00"))


def test_alterar_preco(sessao: Session, cafe: Produto) -> None:
    cadastro = CadastroProdutoService(sessao)
    cadastro.alterar_preco("789", Decimal("12.90"))
    sessao.refresh(cafe)
    assert cafe.preco == Decimal("12.90")
    with pytest.raises(ValueError, match="negativo"):
        cadastro.alterar_preco("789", Decimal("-1"))


def test_repor_estoque(sessao: Session, cafe: Produto) -> None:
    cadastro = CadastroProdutoService(sessao)
    produto = cadastro.repor_estoque("789", 5)
    assert produto.estoque_atual == 7
    with pytest.raises(ValueError, match="maior que zero"):
        cadastro.repor_estoque("789", 0)


def test_desativar_some_da_lista(sessao: Session, cafe: Produto) -> None:
    cadastro = CadastroProdutoService(sessao)
    cadastro.desativar("789")
    assert cadastro.listar() == []
    with pytest.raises(ValueError, match="não encontrado"):
        cadastro.desativar("789")
