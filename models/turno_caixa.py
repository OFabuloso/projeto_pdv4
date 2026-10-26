from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.venda import Venda


class TurnoCaixa(Base):
    """Período entre a abertura e o fechamento do caixa por um operador."""

    __tablename__ = "turnos_caixa"
    __table_args__ = (
        CheckConstraint(
            "valor_abertura >= 0", name="ck_turnos_caixa_abertura_nao_negativa"
        ),
        CheckConstraint(
            "valor_fechamento IS NULL OR valor_fechamento >= 0",
            name="ck_turnos_caixa_fechamento_nao_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    operador: Mapped[str] = mapped_column(String(100))
    aberto_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # enquanto fechado_em for nulo, o turno está aberto
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # troco inicial colocado na gaveta
    valor_abertura: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # dinheiro contado na gaveta no fechamento
    valor_fechamento: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    vendas: Mapped[list[Venda]] = relationship(back_populates="turno_caixa")

    @property
    def aberto(self) -> bool:
        return self.fechado_em is None
