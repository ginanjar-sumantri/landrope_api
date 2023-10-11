"""tanggal rencana transaksi

Revision ID: 3ac919dea542
Revises: 27fe68641f2c
Create Date: 2023-10-11 17:03:44.680407

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '3ac919dea542'
down_revision = '27fe68641f2c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('termin', sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('termin', 'remark')
    # ### end Alembic commands ###
