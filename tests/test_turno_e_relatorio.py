from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from models import FormaPagamento, Produto, TurnoCaixa, Venda
from services.caixa import CaixaService
from services.relatorio import RelatorioService, intervalo_do_dia
from services.turno_caixa import TurnoCaixaService

FUSO_BRASILIA = timezone(timedelta(hours=-3))


def vender(
    sessao: Session,
    turno: TurnoCaixa,
    forma_pagamento: FormaPagamento,
    valor_recebido: Decimal | None = None,
) -> Venda:
    caixa = CaixaService(sessao, turno)
    caixa.adicionar_item("789")
    return caixa.finalizar(forma_pagamento, valor_recebido)


def test_abrir_caixa(sessao: Session) -> None:
    servico = TurnoCaixaService(sessao)
    turno = servico.abrir(" Ana ", Decimal("100.00"))
    assert turno.operador == "Ana"
    assert turno.aberto
    assert servico.turno_aberto() is turno


def test_nao_abre_dois_caixas(sessao: Session, turno: TurnoCaixa) -> None:
    with pytest.raises(ValueError, match="Já existe um caixa aberto"):
        TurnoCaixaService(sessao).abrir("Bia", Decimal("0"))


@pytest.mark.parametrize(
    ("operador", "valor_abertura", "mensagem"),
    [(" ", Decimal("0"), "operador"), ("Ana", Decimal("-1"), "negativo")],
)
def test_abrir_valida_campos(
    sessao: Session, operador: str, valor_abertura: Decimal, mensagem: str
) -> None:
    with pytest.raises(ValueError, match=mensagem):
        TurnoCaixaService(sessao).abrir(operador, valor_abertura)


def test_fechar_caixa_confere_dinheiro(
    sessao: Session, turno: TurnoCaixa, cafe: Produto
) -> None:
    vender(sessao, turno, FormaPagamento.DINHEIRO, Decimal("50.00"))
    vender(sessao, turno, FormaPagamento.PIX)
    servico = TurnoCaixaService(sessao)

    # abertura 50 + venda em dinheiro 10 = 60 esperados; contou 58 -> falta 2
    resumo = servico.fechar(turno, Decimal("58.00"))

    assert resumo.esperado_em_dinheiro == Decimal("60.00")
    assert resumo.diferenca == Decimal("-2.00")
    assert resumo.vendas.quantidade_vendas == 2
    assert resumo.vendas.total_geral == Decimal("20.00")
    assert not turno.aberto
    assert servico.turno_aberto() is None
    with pytest.raises(ValueError, match="já foi fechado"):
        servico.fechar(turno, Decimal("58.00"))


def test_fechar_caixa_rejeita_valor_negativo(
    sessao: Session, turno: TurnoCaixa
) -> None:
    with pytest.raises(ValueError, match="negativo"):
        TurnoCaixaService(sessao).fechar(turno, Decimal("-1"))
    assert turno.aberto


def test_intervalo_do_dia_converte_para_utc() -> None:
    inicio, fim = intervalo_do_dia(date(2026, 10, 26), FUSO_BRASILIA)
    assert inicio == datetime(2026, 10, 26, 3, tzinfo=UTC)
    assert fim == datetime(2026, 10, 27, 3, tzinfo=UTC)


def test_relatorio_do_dia_agrupa_por_forma(sessao: Session, turno: TurnoCaixa) -> None:
    def venda_em(
        hora_utc: datetime, forma_pagamento: FormaPagamento, total: str
    ) -> Venda:
        return Venda(
            data_hora=hora_utc,
            total=Decimal(total),
            forma_pagamento=forma_pagamento,
            turno_caixa=turno,
        )

    def utc(dia_mes: int, hora: int, minuto: int = 0) -> datetime:
        return datetime(2026, 10, dia_mes, hora, minuto, tzinfo=UTC)

    dia = date(2026, 10, 26)
    pix = FormaPagamento.PIX
    sessao.add_all(
        [
            # 26/10 00:30 em Brasília = 03:30 UTC: entra no dia
            venda_em(utc(26, 3, 30), pix, "5.00"),
            venda_em(utc(26, 15), pix, "7.50"),
            venda_em(utc(26, 18), FormaPagamento.DINHEIRO, "3.00"),
            # 25/10 23:30 em Brasília: fica de fora
            venda_em(utc(26, 2, 30), pix, "99.00"),
        ]
    )
    sessao.commit()

    relatorio = RelatorioService(sessao).vendas_do_dia(dia, FUSO_BRASILIA)

    assert relatorio.quantidade_vendas == 3
    assert relatorio.total_geral == Decimal("15.50")
    assert relatorio.total_da_forma(FormaPagamento.PIX) == Decimal("12.50")
    assert relatorio.total_da_forma(FormaPagamento.DINHEIRO) == Decimal("3.00")
    assert relatorio.total_da_forma(FormaPagamento.CARTAO_CREDITO) == Decimal("0.00")


def test_relatorio_sem_vendas(sessao: Session) -> None:
    relatorio = RelatorioService(sessao).vendas_do_dia(date(2026, 1, 1), UTC)
    assert relatorio.linhas == []
    assert relatorio.total_geral == Decimal("0.00")
