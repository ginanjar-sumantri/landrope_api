"""spk, termin, invoice

Revision ID: fc6026423099
Revises: 
Create Date: 2023-09-25 16:37:47.368141

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fc6026423099'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payment',
    sa.Column('payment_method', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('giro_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['giro_id'], ['giro.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_id'), 'payment', ['id'], unique=False)
    op.create_table('tahap',
    sa.Column('nomor_tahap', sa.Integer(), nullable=False),
    sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('ptsk_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('group', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['planing_id'], ['planing.id'], ),
    sa.ForeignKeyConstraint(['ptsk_id'], ['ptsk.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tahap_id'), 'tahap', ['id'], unique=False)
    op.create_table('termin',
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('tahap_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('kjb_hd_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('jenis_bayar', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('is_void', sa.Boolean(), nullable=False),
    sa.Column('tanggal_transaksi', sa.Date(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['kjb_hd_id'], ['kjb_hd.id'], ),
    sa.ForeignKeyConstraint(['tahap_id'], ['tahap.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_termin_id'), 'termin', ['id'], unique=False)
    op.create_table('bidang_komponen_biaya',
    sa.Column('bidang_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('beban_biaya_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('beban_pembeli', sa.Boolean(), nullable=True),
    sa.Column('is_use', sa.Boolean(), nullable=True),
    sa.Column('tanggal_bayar', sa.Date(), nullable=True),
    sa.Column('is_paid', sa.Boolean(), nullable=True),
    sa.Column('is_void', sa.Boolean(), nullable=True),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['beban_biaya_id'], ['beban_biaya.id'], ),
    sa.ForeignKeyConstraint(['bidang_id'], ['bidang.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bidang_komponen_biaya_id'), 'bidang_komponen_biaya', ['id'], unique=False)
    op.create_table('tahap_detail',
    sa.Column('tahap_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('bidang_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('is_void', sa.Boolean(), nullable=True),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['bidang_id'], ['bidang.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['tahap_id'], ['tahap.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tahap_detail_id'), 'tahap_detail', ['id'], unique=False)
    op.create_table('invoice',
    sa.Column('termin_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('spk_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('bidang_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('amount', sa.Numeric(scale=2), nullable=True),
    sa.Column('is_void', sa.Boolean(), nullable=True),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['bidang_id'], ['bidang.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['spk_id'], ['spk.id'], ),
    sa.ForeignKeyConstraint(['termin_id'], ['termin.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_id'), 'invoice', ['id'], unique=False)
    op.create_table('invoice_detail',
    sa.Column('invoice_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('bidang_komponen_biaya_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('amount', sa.Numeric(scale=2), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['bidang_komponen_biaya_id'], ['bidang_komponen_biaya.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_detail_id'), 'invoice_detail', ['id'], unique=False)
    op.drop_index('ix_spk_beban_biaya_id', table_name='spk_beban_biaya')
    op.drop_table('spk_beban_biaya')
    op.add_column('beban_biaya', sa.Column('is_tax', sa.Boolean(), nullable=True))
    op.add_column('beban_biaya', sa.Column('satuan_bayar', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('beban_biaya', sa.Column('satuan_harga', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('beban_biaya', sa.Column('amount', sa.Numeric(scale=2), nullable=True))
    op.alter_column('beban_biaya', 'name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('beban_biaya', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.add_column('bidang', sa.Column('harga_akta', sa.Numeric(scale=2), nullable=True))
    op.add_column('bidang', sa.Column('harga_transaksi', sa.Numeric(scale=2), nullable=True))
    op.add_column('section', sa.Column('last_tahap', sa.Integer(), nullable=True))
    op.add_column('spk', sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('spk', 'code')
    op.drop_column('section', 'last_tahap')
    op.drop_column('bidang', 'harga_transaksi')
    op.drop_column('bidang', 'harga_akta')
    op.alter_column('beban_biaya', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('beban_biaya', 'name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('beban_biaya', 'amount')
    op.drop_column('beban_biaya', 'satuan_harga')
    op.drop_column('beban_biaya', 'satuan_bayar')
    op.drop_column('beban_biaya', 'is_tax')
    op.create_table('spk_beban_biaya',
    sa.Column('spk_id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('beban_biaya_id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_by_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['beban_biaya_id'], ['beban_biaya.id'], name='spk_beban_biaya_beban_biaya_id_fkey'),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], name='spk_beban_biaya_created_by_id_fkey'),
    sa.ForeignKeyConstraint(['spk_id'], ['spk.id'], name='spk_beban_biaya_spk_id_fkey'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], name='spk_beban_biaya_updated_by_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='spk_beban_biaya_pkey')
    )
    op.create_index('ix_spk_beban_biaya_id', 'spk_beban_biaya', ['id'], unique=False)
    op.drop_index(op.f('ix_invoice_detail_id'), table_name='invoice_detail')
    op.drop_table('invoice_detail')
    op.drop_index(op.f('ix_invoice_id'), table_name='invoice')
    op.drop_table('invoice')
    op.drop_index(op.f('ix_tahap_detail_id'), table_name='tahap_detail')
    op.drop_table('tahap_detail')
    op.drop_index(op.f('ix_bidang_komponen_biaya_id'), table_name='bidang_komponen_biaya')
    op.drop_table('bidang_komponen_biaya')
    op.drop_index(op.f('ix_termin_id'), table_name='termin')
    op.drop_table('termin')
    op.drop_index(op.f('ix_tahap_id'), table_name='tahap')
    op.drop_table('tahap')
    op.drop_index(op.f('ix_payment_id'), table_name='payment')
    op.drop_table('payment')
    # ### end Alembic commands ###
