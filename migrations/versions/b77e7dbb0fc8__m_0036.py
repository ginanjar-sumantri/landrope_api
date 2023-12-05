"""_m_0036

Revision ID: b77e7dbb0fc8
Revises: adfaf46a0279
Create Date: 2023-12-05 11:15:55.781512

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'b77e7dbb0fc8'
down_revision = 'adfaf46a0279'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bidang_komponen_biaya', sa.Column('paid_amount', sa.Numeric(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bidang_komponen_biaya', 'paid_amount')
    # ### end Alembic commands ###
