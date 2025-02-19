"""_m_0068

Revision ID: 9ea151fd8c0b
Revises: 8dac6356ba81
Create Date: 2024-02-01 14:42:34.578213

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '9ea151fd8c0b'
down_revision = '8dac6356ba81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment', sa.Column('tanggal_cair', sa.Date(), nullable=True))
    op.add_column('payment', sa.Column('tanggal_buka', sa.Date(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('payment', 'tanggal_buka')
    op.drop_column('payment', 'tanggal_cair')
    # ### end Alembic commands ###
