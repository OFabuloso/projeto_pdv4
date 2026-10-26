from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from decimal import Decimal

from sqlalchemy.orm import Session

from models.venda import FormaPagamento
from repositories.venda_repo import TotalPorFormaPagamento, VendaRepository


@dataclass(frozen=True)
class RelatorioVendas:
    linhas: list[TotalPorFormaPagamento]

    @property
    def quantidade_vendas(self) -> int:
        return sum(linha.quantidade_vendas for linha in self.linhas)

    @property
    def total_geral(self) -> Decimal:
        return sum((linha.total for linha in self.linhas), Decimal("0.00"))

    def total_da_forma(self, forma_pagamento: FormaPagamento) -> Decimal:
        for linha in self.linhas:
            if linha.forma_pagamento is forma_pagamento:
                return linha.total
        return Decimal("0.00")


def intervalo_do_dia(dia: date, fuso: tzinfo) -> tuple[datetime, datetime]:
    """Início e fim do dia no fuso informado, convertidos para UTC."""
    inicio = datetime.combine(dia, time.min, tzinfo=fuso)
    fim = inicio + timedelta(days=1)
    # o banco grava em UTC; comparar em UTC evita erro de fuso no SQLite
    return inicio.astimezone(UTC), fim.astimezone(UTC)


class RelatorioService:
    def __init__(self, session: Session) -> None:
        self.vendas = VendaRepository(session)

    def vendas_do_dia(self, dia: date, fuso: tzinfo | None = None) -> RelatorioVendas:
        # sem fuso explícito, usa o do computador do caixa
        fuso_dia = fuso or datetime.now().astimezone().tzinfo or UTC
        inicio, fim = intervalo_do_dia(dia, fuso_dia)
        return RelatorioVendas(self.vendas.totais_por_periodo(inicio, fim))

    def vendas_do_turno(self, turno_caixa_id: int) -> RelatorioVendas:
        return RelatorioVendas(self.vendas.totais_por_turno(turno_caixa_id))
