from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.produto import Produto
    from models.turno_caixa import TurnoCaixa


class FormaPagamento(enum.Enum):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CARTAO_DEBITO = "cartao_debito"
    CARTAO_CREDITO = "cartao_credito"


def _valores_forma_pagamento(classe_enum: type[FormaPagamento]) -> list[str]:
    # grava no banco o valor ("dinheiro") e não o nome do membro ("DINHEIRO")
    return [membro.value for membro in classe_enum]


class Venda(Base):
    __tablename__ = "vendas"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_vendas_total_nao_negativo"),
        CheckConstraint(
            "valor_recebido IS NULL OR valor_recebido >= total",
            name="ck_vendas_valor_recebido_cobre_total",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # hora gerada pelo servidor do banco, com fuso horário
    data_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # native_enum=False guarda como VARCHAR, compatível com a coluna antiga
    forma_pagamento: Mapped[FormaPagamento] = mapped_column(
        Enum(
            FormaPagamento,
            native_enum=False,
            length=30,
            values_callable=_valores_forma_pagamento,
        )
    )
    # só é preenchido em dinheiro; nas outras formas o valor pago é o total
    valor_recebido: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    # nulo apenas nas vendas feitas antes de existir controle de turno
    turno_caixa_id: Mapped[int | None] = mapped_column(
        ForeignKey("turnos_caixa.id", name="fk_vendas_turno_caixa_id_turnos_caixa")
    )
    turno_caixa: Mapped[TurnoCaixa | None] = relationship(back_populates="vendas")
    itens: Mapped[list[ItemVenda]] = relationship(
        back_populates="venda", cascade="all, delete-orphan"
    )

    @property
    def troco(self) -> Decimal:
        if self.valor_recebido is None:
            return Decimal("0.00")
        return self.valor_recebido - self.total


class ItemVenda(Base):
    __tablename__ = "itens_venda"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_itens_venda_quantidade_positiva"),
        CheckConstraint(
            "preco_unitario >= 0", name="ck_itens_venda_preco_nao_negativo"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[int]
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    venda: Mapped[Venda] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship(back_populates="itens")
