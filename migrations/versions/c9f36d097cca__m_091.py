"""_m_091

Revision ID: c9f36d097cca
Revises: 62f231715ac3
Create Date: 2024-03-24 06:37:57.298032

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c9f36d097cca'
down_revision = '62f231715ac3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('payment_giro_detail', 'giro_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('payment_giro_detail', 'giro_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    # ### end Alembic commands ###
