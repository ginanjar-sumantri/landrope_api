"""_m_095

Revision ID: b372abd1fdca
Revises: c7bc87e93289
Create Date: 2024-03-24 12:53:18.570730

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b372abd1fdca'
down_revision = 'c7bc87e93289'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('beban_biaya', sa.Column('is_exclude_printout', sa.Boolean(), nullable=True))
    op.add_column('bidang_komponen_biaya', sa.Column('order_number', sa.Integer(), nullable=True))
    op.alter_column('payment', 'payment_method',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('payment', 'pay_to',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_constraint('payment_termin_id_fkey', 'payment', type_='foreignkey')
    op.drop_column('payment', 'termin_id')
    op.add_column('payment_giro_detail', sa.Column('pay_to', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.alter_column('payment_giro_detail', 'giro_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    op.add_column('spk_kelengkapan_dokumen', sa.Column('order_number', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('spk_kelengkapan_dokumen', 'order_number')
    op.alter_column('payment_giro_detail', 'giro_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    op.drop_column('payment_giro_detail', 'pay_to')
    op.add_column('payment', sa.Column('termin_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('payment_termin_id_fkey', 'payment', 'termin', ['termin_id'], ['id'])
    op.alter_column('payment', 'pay_to',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('payment', 'payment_method',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('bidang_komponen_biaya', 'order_number')
    op.drop_column('beban_biaya', 'is_exclude_printout')
    # ### end Alembic commands ###
