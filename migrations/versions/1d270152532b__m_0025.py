"""_m_0025

Revision ID: 1d270152532b
Revises: f15139c2828b
Create Date: 2023-11-24 11:48:35.704289

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '1d270152532b'
down_revision = 'f15139c2828b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('beban_biaya', 'is_retur')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('beban_biaya', sa.Column('is_retur', sa.BOOLEAN(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
