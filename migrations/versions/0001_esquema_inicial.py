"""Esquema inicial (o mesmo que o create_all antigo gerava).

Revision ID: 0001
Revises:
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "produtos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo_barras", sa.String(50), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("estoque_atual", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_produtos_codigo_barras", "produtos", ["codigo_barras"], unique=True
    )
    op.create_table(
        "vendas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data_hora", sa.DateTime(), nullable=True),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("forma_pagamento", sa.String(30), nullable=False),
    )
    op.create_table(
        "itens_venda",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venda_id", sa.Integer(), sa.ForeignKey("vendas.id"), nullable=False),
        sa.Column(
            "produto_id", sa.Integer(), sa.ForeignKey("produtos.id"), nullable=False
        ),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("itens_venda")
    op.drop_table("vendas")
    op.drop_index("ix_produtos_codigo_barras", table_name="produtos")
    op.drop_table("produtos")
