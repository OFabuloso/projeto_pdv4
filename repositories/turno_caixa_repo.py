from sqlalchemy import select
from sqlalchemy.orm import Session

from models.turno_caixa import TurnoCaixa


class TurnoCaixaRepository:
    """Acesso a dados de TurnoCaixa. Não faz commit: a transação é do serviço."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar_aberto(self) -> TurnoCaixa | None:
        consulta = select(TurnoCaixa).where(TurnoCaixa.fechado_em.is_(None))
        return self.session.scalars(consulta).first()

    def adicionar(self, turno: TurnoCaixa) -> None:
        self.session.add(turno)
        self.session.flush()
