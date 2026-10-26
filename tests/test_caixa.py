from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import FormaPagamento, ItemVenda, Produto, TurnoCaixa, Venda
from services.caixa import CaixaService


def test_produto_inexistente_lanca_erro(sessao: Session, turno: TurnoCaixa) -> None:
    caixa = CaixaService(sessao, turno)
    with pytest.raises(ValueError, match="não encontrado"):
        caixa.adicionar_item("000")


@pytest.mark.parametrize("quantidade_invalida", [0, -5])
def test_quantidade_nao_positiva_e_rejeitada(
    sessao: Session, turno: TurnoCaixa, cafe: Produto, quantidade_invalida: int
) -> None:
    caixa = CaixaService(sessao, turno)
    with pytest.raises(ValueError, match="maior que zero"):
        caixa.adicionar_item("789", quantidade=quantidade_invalida)
    assert caixa.itens == []


def test_estoque_considera_o_que_ja_esta_no_carrinho(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    caixa.adicionar_item("789")
    with pytest.raises(ValueError, match="Estoque insuficiente"):
        caixa.adicionar_item("789")


def test_mesmo_produto_soma_na_mesma_linha(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    caixa.adicionar_item("789")
    assert len(caixa.itens) == 1
    assert caixa.itens[0].quantidade == 2


def test_total_soma_com_decimal(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    sessao.add(
        Produto(codigo_barras="456", nome="Pão", preco=Decimal("0.10"), estoque_atual=5)
    )
    sessao.commit()
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    caixa.adicionar_item("456", quantidade=3)
    assert caixa.total() == Decimal("10.30")


def test_finalizar_grava_venda_e_baixa_estoque(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789", quantidade=2)

    venda = caixa.finalizar(FormaPagamento.PIX)

    venda_gravada = sessao.get(Venda, venda.id)
    assert venda_gravada is not None
    assert venda_gravada.total == Decimal("20.00")
    assert venda_gravada.forma_pagamento is FormaPagamento.PIX
    assert venda_gravada.data_hora is not None
    item_gravado = sessao.scalars(select(ItemVenda)).one()
    assert item_gravado.quantidade == 2
    assert item_gravado.preco_unitario == Decimal("10.00")
    assert cafe.estoque_atual == 0
    assert caixa.itens == []


def test_finalizar_venda_vazia_lanca_erro(sessao: Session, turno: TurnoCaixa) -> None:
    caixa = CaixaService(sessao, turno)
    with pytest.raises(ValueError, match="Venda vazia"):
        caixa.finalizar(FormaPagamento.DINHEIRO)


def test_finalizar_falha_se_outro_caixa_vendeu_antes(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789", quantidade=2)
    # simula outro caixa levando uma unidade entre o bip e a finalização
    cafe.estoque_atual = 1
    sessao.commit()

    with pytest.raises(ValueError, match="Estoque insuficiente para Café"):
        caixa.finalizar(FormaPagamento.DINHEIRO, Decimal("20.00"))

    # rollback: nada foi gravado e o estoque não mudou
    assert sessao.scalars(select(Venda)).all() == []
    sessao.refresh(cafe)
    assert cafe.estoque_atual == 1


def test_finalizar_vincula_venda_ao_turno(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    venda = caixa.finalizar(FormaPagamento.PIX)
    assert venda.turno_caixa_id == turno.id


def test_finalizar_em_dinheiro_calcula_troco(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    venda = caixa.finalizar(FormaPagamento.DINHEIRO, Decimal("50.00"))
    assert venda.valor_recebido == Decimal("50.00")
    assert venda.troco == Decimal("40.00")


@pytest.mark.parametrize("valor_recebido", [None, Decimal("9.99")])
def test_finalizar_em_dinheiro_exige_valor_suficiente(
    sessao: Session,
    turno: TurnoCaixa,
    cafe: Produto,
    valor_recebido: Decimal | None,
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    with pytest.raises(ValueError, match="Valor recebido menor"):
        caixa.finalizar(FormaPagamento.DINHEIRO, valor_recebido)
    assert len(caixa.itens) == 1


def test_pagamento_sem_dinheiro_nao_tem_troco(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    venda = caixa.finalizar(FormaPagamento.CARTAO_DEBITO, Decimal("100.00"))
    assert venda.valor_recebido is None
    assert venda.troco == Decimal("0.00")


def test_finalizar_com_caixa_fechado_lanca_erro(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    turno.fechado_em = datetime.now(UTC)
    with pytest.raises(ValueError, match="caixa está fechado"):
        caixa.finalizar(FormaPagamento.PIX)


def test_remover_item_parcial_e_total(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789", quantidade=2)
    caixa.remover_item("789", quantidade=1)
    assert caixa.itens[0].quantidade == 1
    caixa.remover_item("789")
    assert caixa.itens == []


def test_remover_item_valida_entrada(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    with pytest.raises(ValueError, match="não está na venda"):
        caixa.remover_item("789")
    caixa.adicionar_item("789")
    with pytest.raises(ValueError, match="só 1 unidade"):
        caixa.remover_item("789", quantidade=2)
    with pytest.raises(ValueError, match="maior que zero"):
        caixa.remover_item("789", quantidade=0)


def test_cancelar_esvazia_carrinho(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    caixa.cancelar()
    assert caixa.itens == []
