"""__is draft in spk and termin

Revision ID: d365e90322f6
Revises: 47339d08c42d
Create Date: 2024-06-20 22:17:32.442142

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd365e90322f6'
down_revision = '47339d08c42d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_table('import_temp_ttn')
    # op.drop_table('import_temp_kjb_harga')
    # op.drop_table('import_temp_komponen')
    # op.drop_table('import_temp_spk')
    # op.drop_table('temp_pemilik')
    # op.drop_table('termin_temp')
    # op.drop_table('import_history_update_bidang')
    # op.drop_table('import_temp_kjb_detail')
    # op.drop_table('import_temp_request_petlok')
    # op.drop_table('pemilik_name_temp')
    # op.drop_table('import_bidang_paid')
    # op.drop_table('import_temp_bidang_recon')
    # op.drop_table('import_id_bidang_lama')
    # op.drop_table('import_temp_kjb_termin')
    # op.drop_table('tahap_backup')
    # op.drop_table('import_temp_kjb_beban')
    # op.drop_table('import_temp_kjb')
    op.add_column('spk', sa.Column('is_draft', sa.Boolean(), nullable=True))
    op.add_column('termin', sa.Column('is_draft', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('termin', 'is_draft')
    op.drop_column('spk', 'is_draft')
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
    op.create_table('import_temp_kjb_beban',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('beban_biaya', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False)
    )
    op.create_table('tahap_backup',
    sa.Column('nomor_tahap', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('planing_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('ptsk_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('group', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_by_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('sub_project_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('harga_standard_girik', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('harga_standard_sertifikat', sa.NUMERIC(), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_kjb_termin',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('jenis_bayar', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('nilai', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_id_bidang_lama',
    sa.Column('id_bidang_lama', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id_bidang_lama', name='import_id_bidang_lama_pkey')
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
    op.create_table('import_bidang_paid',
    sa.Column('id_bidang_lama', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('no_tahap', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('luas_bayar', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('harga_transaksi', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('pengajuan_pembayaran', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('pembayaran_cair', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('paid_amount', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('cutoff_date', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id_bidang_lama', name='import_bidang_paid_pkey')
    )
    op.create_table('pemilik_name_temp',
    sa.Column('pemilik_name', sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_request_petlok',
    sa.Column('code', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('tanggal', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('tanggal_terima_berkas', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('nomor_kjb', sa.VARCHAR(), autoincrement=False, nullable=False),
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
    sa.Column('id_bidang_lama', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
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
    op.create_table('import_history_update_bidang',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('kjb_dt_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('bidang_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_surat_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('pemilik_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('imported_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True)
    )
    op.create_table('termin_temp',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('termin_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='termin_temp_pkey')
    )
    op.create_table('temp_pemilik',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('pemilik_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='temp_pemilik_pkey')
    )
    op.create_table('import_temp_spk',
    sa.Column('nomor_spk', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('remark', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('id_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_bayar', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('nilai', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.create_table('import_temp_komponen',
    sa.Column('id_bidang', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_biaya', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_kjb_harga',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('harga_akta', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('harga_transaksi', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_ttn',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('project', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('desa', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('pemilik', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('tanggal_tanda_terima', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('nomor_tanda_terima', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('notaris', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('luas_surat', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('status_peta_lokasi', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('nop', sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###
