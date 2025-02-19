"""_m_0060

Revision ID: f4ffedeed413
Revises: d529205ae69d
Create Date: 2024-01-25 17:48:12.030452

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'f4ffedeed413'
down_revision = 'd529205ae69d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bundle_dt', 'history_data')
    op.add_column('dokumen', sa.Column('is_multiple', sa.Boolean(), nullable=True))
    op.create_unique_constraint(None, 'kjb_hd', ['code'])
    op.drop_column('tanda_terima_notaris_dt', 'history_data')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tanda_terima_notaris_dt', sa.Column('history_data', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'kjb_hd', type_='unique')
    op.drop_column('dokumen', 'is_multiple')
    op.add_column('bundle_dt', sa.Column('history_data', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
