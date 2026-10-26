from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from models.venda import FormaPagamento, Venda


@dataclass(frozen=True)
class TotalPorFormaPagamento:
    forma_pagamento: FormaPagamento
    quantidade_vendas: int
    total: Decimal


class VendaRepository:
    """Consultas agregadas de vendas. Não faz commit: a transação é do serviço."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _totais_por_forma(
        self, *condicoes: ColumnElement[bool]
    ) -> list[TotalPorFormaPagamento]:
        consulta = (
            select(Venda.forma_pagamento, func.count(Venda.id), func.sum(Venda.total))
            .where(*condicoes)
            .group_by(Venda.forma_pagamento)
            .order_by(Venda.forma_pagamento)
        )
        return [
            TotalPorFormaPagamento(forma, quantidade, total)
            for forma, quantidade, total in self.session.execute(consulta).tuples()
        ]

    def totais_por_periodo(
        self, inicio: datetime, fim: datetime
    ) -> list[TotalPorFormaPagamento]:
        """Totais das vendas com início <= data_hora < fim."""
        return self._totais_por_forma(Venda.data_hora >= inicio, Venda.data_hora < fim)

    def totais_por_turno(self, turno_caixa_id: int) -> list[TotalPorFormaPagamento]:
        return self._totais_por_forma(Venda.turno_caixa_id == turno_caixa_id)
