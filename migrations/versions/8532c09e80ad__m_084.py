"""_m_084

Revision ID: 8532c09e80ad
Revises: e901140315d5
Create Date: 2024-03-08 19:36:09.864202

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8532c09e80ad'
down_revision = 'e901140315d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('workflow_next_approver',
    sa.Column('workflow_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_next_approver_id'), 'workflow_next_approver', ['id'], unique=False)
    op.drop_table('import_temp_spk')
    op.drop_table('import_temp_komponen')
    op.drop_table('import_temp_kjb_detail')
    op.drop_table('import_temp_request_petlok')
    op.drop_table('import_temp_bidang_recon')
    op.drop_table('import_temp_ttn')
    op.drop_table('import_temp_kjb')
    op.drop_table('import_temp_kjb_termin')
    op.drop_table('import_temp_kjb_beban')
    op.drop_table('import_temp_kjb_harga')
    op.add_column('invoice', sa.Column('payment_status', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('invoice', 'payment_status')
    op.create_table('import_temp_kjb_harga',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('harga_akta', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('harga_transaksi', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_kjb_beban',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('beban_biaya', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_kjb_termin',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('jenis_bayar', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('nilai', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_kjb',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('tanggal_kjb', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('kategori_penjual', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('group_name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('desa', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('luas_kjb', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('manager', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('sales', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('mediator', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('telepon_mediator', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('remark', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('penjual', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('bank', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('nomor_rekening', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('nama_rekening', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('utj_amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_ttn',
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('project', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('desa', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('pemilik', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('tanggal_tanda_terima', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('nomor_tanda_terima', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('notaris', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('luas_surat', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('status_peta_lokasi', sa.VARCHAR(length=50), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_bidang_recon',
    sa.Column('idbidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('idbidanglama', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('pemilik', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('project', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('desa', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ptsk', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('sk_no', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('luas_surat', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('jenis_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('manager', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('sales', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('notaris', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('tahap', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('luas_bayar', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('harga_transaksi', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_request_petlok',
    sa.Column('code', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('tanggal', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('tanggal_terima_berkas', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('remarks', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('tanggal_kirim_dokumen', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('tanggal_pengukuran', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('keterangan', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('penunjuk_batas', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('surveyor', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('luas_ukur', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_kjb_detail',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('jenis_surat', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('posisi_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('harga_akta', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('harga_transaksi', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('luas_surat', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('penjual', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('project', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('desa', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('group_name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('jumlah_waris', sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_komponen',
    sa.Column('id_bidang', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_biaya', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_spk',
    sa.Column('nomor_spk', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('remark', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('id_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_bayar', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('nilai', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.drop_index(op.f('ix_workflow_next_approver_id'), table_name='workflow_next_approver')
    op.drop_table('workflow_next_approver')
    # ### end Alembic commands ###
