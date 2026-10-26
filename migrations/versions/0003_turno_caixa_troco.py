"""Turnos de caixa (abertura/fechamento) e valor recebido para o troco.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "turnos_caixa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operador", sa.String(100), nullable=False),
        sa.Column(
            "aberto_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("fechado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valor_abertura", sa.Numeric(10, 2), nullable=False),
        sa.Column("valor_fechamento", sa.Numeric(10, 2), nullable=True),
        sa.CheckConstraint(
            "valor_abertura >= 0", name="ck_turnos_caixa_abertura_nao_negativa"
        ),
        sa.CheckConstraint(
            "valor_fechamento IS NULL OR valor_fechamento >= 0",
            name="ck_turnos_caixa_fechamento_nao_negativo",
        ),
    )

    with op.batch_alter_table("vendas") as tabela:
        tabela.add_column(sa.Column("valor_recebido", sa.Numeric(10, 2), nullable=True))
        tabela.add_column(sa.Column("turno_caixa_id", sa.Integer(), nullable=True))
        tabela.create_foreign_key(
            "fk_vendas_turno_caixa_id_turnos_caixa",
            "turnos_caixa",
            ["turno_caixa_id"],
            ["id"],
        )
        tabela.create_check_constraint(
            "ck_vendas_valor_recebido_cobre_total",
            "valor_recebido IS NULL OR valor_recebido >= total",
        )


def downgrade() -> None:
    with op.batch_alter_table("vendas") as tabela:
        tabela.drop_constraint("ck_vendas_valor_recebido_cobre_total", type_="check")
        tabela.drop_constraint(
            "fk_vendas_turno_caixa_id_turnos_caixa", type_="foreignkey"
        )
        tabela.drop_column("turno_caixa_id")
        tabela.drop_column("valor_recebido")

    op.drop_table("turnos_caixa")
