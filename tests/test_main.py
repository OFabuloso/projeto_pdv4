from collections.abc import Callable
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from interface.venda import executar_venda, ler_forma_pagamento
from models import FormaPagamento, Produto, TurnoCaixa, Venda


@pytest.fixture
def digitar(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Simula o operador digitando as respostas na ordem dada."""

    def configurar(*respostas: str) -> None:
        sequencia = iter(respostas)
        monkeypatch.setattr("builtins.input", lambda _mensagem="": next(sequencia))

    return configurar


def test_ler_forma_pagamento_repete_ate_opcao_valida(
    digitar: Callable[..., None],
) -> None:
    digitar("9", "abc", "2")
    assert ler_forma_pagamento() is FormaPagamento.PIX


def test_venda_completa_em_dinheiro_com_troco(
    sessao: Session,
    turno: TurnoCaixa,
    cafe: Produto,
    digitar: Callable[..., None],
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 2 cafés, remove 1, finaliza em dinheiro (opção 1) com valor baixo e depois 50
    digitar("2*789", "r", "789", "1", "F", "1", "5", "50")

    executar_venda(sessao, turno)

    venda = sessao.scalars(select(Venda)).one()
    assert venda.total == Decimal("10.00")
    assert venda.troco == Decimal("40.00")
    saida = capsys.readouterr().out
    assert "pelo menos R$ 10,00" in saida
    assert "Troco: R$ 40,00" in saida


def test_venda_cancelada_nao_grava(
    sessao: Session,
    turno: TurnoCaixa,
    cafe: Produto,
    digitar: Callable[..., None],
    capsys: pytest.CaptureFixture[str],
) -> None:
    digitar("f", "000", "789", "c")

    executar_venda(sessao, turno)

    assert sessao.scalars(select(Venda)).all() == []
    saida = capsys.readouterr().out
    assert "Nenhum item na venda." in saida
    assert "Produto não encontrado." in saida
    assert "Venda cancelada." in saida
