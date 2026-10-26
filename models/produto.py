from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.venda import ItemVenda


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        CheckConstraint("preco >= 0", name="ck_produtos_preco_nao_negativo"),
        CheckConstraint("estoque_atual >= 0", name="ck_produtos_estoque_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_barras: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(150))
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estoque_atual: Mapped[int] = mapped_column(default=0)
    # exclusão lógica: produto inativo some do caixa, mas o histórico de vendas fica
    ativo: Mapped[bool] = mapped_column(default=True, server_default=true())
    itens: Mapped[list[ItemVenda]] = relationship(back_populates="produto")
