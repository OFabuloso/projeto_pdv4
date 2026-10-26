from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models.turno_caixa import TurnoCaixa
from models.venda import FormaPagamento
from repositories.turno_caixa_repo import TurnoCaixaRepository
from services.relatorio import RelatorioService, RelatorioVendas


@dataclass(frozen=True)
class ResumoFechamento:
    turno: TurnoCaixa
    vendas: RelatorioVendas
    # troco inicial + vendas em dinheiro (o troco dado já sai do valor recebido)
    esperado_em_dinheiro: Decimal

    @property
    def diferenca(self) -> Decimal:
        """Positivo = sobra na gaveta; negativo = falta."""
        valor_contado = self.turno.valor_fechamento or Decimal("0.00")
        return valor_contado - self.esperado_em_dinheiro


class TurnoCaixaService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.turnos = TurnoCaixaRepository(session)
        self.relatorios = RelatorioService(session)

    def turno_aberto(self) -> TurnoCaixa | None:
        return self.turnos.buscar_aberto()

    def abrir(self, operador: str, valor_abertura: Decimal) -> TurnoCaixa:
        operador = operador.strip()
        if not operador:
            raise ValueError("Informe o nome do operador.")
        if valor_abertura < 0:
            raise ValueError("O valor de abertura não pode ser negativo.")
        if self.turnos.buscar_aberto() is not None:
            raise ValueError("Já existe um caixa aberto.")
        turno = TurnoCaixa(operador=operador, valor_abertura=valor_abertura)
        try:
            self.turnos.adicionar(turno)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return turno

    def fechar(self, turno: TurnoCaixa, valor_contado: Decimal) -> ResumoFechamento:
        if not turno.aberto:
            raise ValueError("Este caixa já foi fechado.")
        if valor_contado < 0:
            raise ValueError("O valor contado não pode ser negativo.")
        vendas = self.relatorios.vendas_do_turno(turno.id)
        esperado_em_dinheiro = turno.valor_abertura + vendas.total_da_forma(
            FormaPagamento.DINHEIRO
        )
        try:
            turno.valor_fechamento = valor_contado
            turno.fechado_em = datetime.now(UTC)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return ResumoFechamento(turno, vendas, esperado_em_dinheiro)
