"""_m_0047

Revision ID: ba2a39901cb6
Revises: 676be63e7355
Create Date: 2023-12-20 19:22:36.238381

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'ba2a39901cb6'
down_revision = '676be63e7355'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment', sa.Column('bank_code', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('payment', 'bank_code')
    # ### end Alembic commands ###
