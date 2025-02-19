"""_m_0077

Revision ID: e6072474d967
Revises: 1ea446e5e65b
Create Date: 2024-02-29 13:57:30.892236

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'e6072474d967'
down_revision = '1ea446e5e65b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_table('import_bidang_paid')
    op.add_column('dokumen', sa.Column('is_exclude_printout', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dokumen', 'is_exclude_printout')
    op.create_table('import_bidang_paid',
    sa.Column('id_bidang_lama', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('no_tahap', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('luas_bayar', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('harga_transaksi', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('paid_amount', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('cutoff_date', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id_bidang_lama', name='import_bidang_paid_pkey')
    )
    # ### end Alembic commands ###
