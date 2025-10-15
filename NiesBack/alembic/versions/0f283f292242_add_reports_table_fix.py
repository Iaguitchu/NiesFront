"""add reports table (fix)

Revision ID: 0f283f292242
Revises: a0803ff7c469
Create Date: 2025-10-15 11:34:57.623098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f283f292242'
down_revision: Union[str, Sequence[str], None] = 'a0803ff7c469'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("group_id", sa.String(length=64),
                  sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("report_id", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    # cria 1 único índice para acelerar consultas por group_id
    op.create_index("ix_reports_group_id", "reports", ["group_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_reports_group_id", table_name="reports")
    op.drop_table("reports")
