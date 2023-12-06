"""_m_0039

Revision ID: 5f97439fd629
Revises: 1523f4a7009a
Create Date: 2023-12-06 14:38:58.060880

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '5f97439fd629'
down_revision = '1523f4a7009a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('giro', sa.Column('tanggal', sa.Date(), nullable=True))
    op.add_column('giro', sa.Column('bank_code', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('giro', sa.Column('payment_method', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('giro', 'payment_method')
    op.drop_column('giro', 'bank_code')
    op.drop_column('giro', 'tanggal')
    # ### end Alembic commands ###
