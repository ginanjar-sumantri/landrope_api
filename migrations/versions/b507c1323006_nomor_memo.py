"""nomor_memo

Revision ID: b507c1323006
Revises: 9c28a32631ca
Create Date: 2023-10-08 22:51:45.071523

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'b507c1323006'
down_revision = '9c28a32631ca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('termin', sa.Column('nomor_memo', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('termin', 'nomor_memo')
    # ### end Alembic commands ###
