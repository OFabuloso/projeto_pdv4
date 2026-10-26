"""Exclusão lógica de produto, restrições de integridade e data/hora com fuso.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26

Atenção: se o banco já tiver estoque negativo (efeito do bug antigo), a
restrição ck_produtos_estoque_nao_negativo vai falhar. Corrija antes com:
    UPDATE produtos SET estoque_atual = 0 WHERE estoque_atual < 0;
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("produtos") as tabela:
        tabela.add_column(
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        tabela.create_check_constraint("ck_produtos_preco_nao_negativo", "preco >= 0")
        tabela.create_check_constraint(
            "ck_produtos_estoque_nao_negativo", "estoque_atual >= 0"
        )

    with op.batch_alter_table("vendas") as tabela:
        # no PostgreSQL as datas antigas são lidas no fuso da sessão do banco
        tabela.alter_column(
            "data_hora",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        )
        tabela.create_check_constraint("ck_vendas_total_nao_negativo", "total >= 0")

    with op.batch_alter_table("itens_venda") as tabela:
        tabela.create_check_constraint(
            "ck_itens_venda_quantidade_positiva", "quantidade > 0"
        )
        tabela.create_check_constraint(
            "ck_itens_venda_preco_nao_negativo", "preco_unitario >= 0"
        )


def downgrade() -> None:
    with op.batch_alter_table("itens_venda") as tabela:
        tabela.drop_constraint("ck_itens_venda_preco_nao_negativo", type_="check")
        tabela.drop_constraint("ck_itens_venda_quantidade_positiva", type_="check")

    with op.batch_alter_table("vendas") as tabela:
        tabela.drop_constraint("ck_vendas_total_nao_negativo", type_="check")
        tabela.alter_column(
            "data_hora",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            nullable=True,
            server_default=None,
        )

    with op.batch_alter_table("produtos") as tabela:
        tabela.drop_constraint("ck_produtos_estoque_nao_negativo", type_="check")
        tabela.drop_constraint("ck_produtos_preco_nao_negativo", type_="check")
        tabela.drop_column("ativo")
