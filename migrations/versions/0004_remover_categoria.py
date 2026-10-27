"""Remove a tabela categoria, sobra do create_all antigo e sem uso nos models.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # bancos criados só pelas migrações nunca tiveram essa tabela
    if sa.inspect(op.get_bind()).has_table("categoria"):
        op.drop_table("categoria")


def downgrade() -> None:
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome_categoria", sa.String(50), nullable=False),
    )
