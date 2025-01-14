"""_m_104

Revision ID: 02b0f3249fde
Revises: 8d42d13a185b
Create Date: 2024-04-05 19:32:19.251258

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '02b0f3249fde'
down_revision = '8d42d13a185b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invoice_bayar',
    sa.Column('termin_bayar_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('invoice_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.ForeignKeyConstraint(['termin_bayar_id'], ['termin_bayar.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_bayar_id'), 'invoice_bayar', ['id'], unique=False)
    # op.drop_table('import_temp_spk')
    # op.drop_table('import_temp_kjb_harga')
    # op.drop_table('import_temp_kjb')
    # op.drop_table('import_id_bidang_lama')
    # op.drop_table('import_bidang_paid')
    # op.drop_table('import_temp_kjb_detail')
    op.drop_table('bidang_coba')
    # op.drop_table('import_temp_bidang_recon')
    # op.drop_table('import_temp_kjb_beban')
    # op.drop_table('import_temp_ttn')
    # op.drop_table('import_temp_request_petlok')
    # op.drop_table('import_temp_kjb_termin')
    # op.drop_table('import_temp_komponen')
    # op.drop_table('termin_temp')
    op.add_column('beban_biaya', sa.Column('default_spk_girik', sa.Boolean(), nullable=True))
    op.add_column('beban_biaya', sa.Column('default_spk_sertifikat', sa.Boolean(), nullable=True))
    op.add_column('bidang_komponen_biaya', sa.Column('is_exclude_spk', sa.Boolean(), nullable=True))
    op.add_column('tahap', sa.Column('harga_standard_girik', sa.Numeric(), nullable=True))
    op.add_column('tahap', sa.Column('harga_standard_sertifikat', sa.Numeric(), nullable=True))
    op.add_column('termin_bayar', sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('termin_bayar', sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('termin_bayar', sa.Column('activity', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('termin_bayar', 'activity')
    op.drop_column('termin_bayar', 'remark')
    op.drop_column('termin_bayar', 'name')
    op.drop_column('tahap', 'harga_standard_sertifikat')
    op.drop_column('tahap', 'harga_standard_girik')
    op.drop_column('bidang_komponen_biaya', 'is_exclude_spk')
    op.drop_column('beban_biaya', 'default_spk_sertifikat')
    op.drop_column('beban_biaya', 'default_spk_girik')
    op.create_table('termin_temp',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('termin_id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='termin_temp_pkey')
    )
    op.create_table('import_temp_komponen',
    sa.Column('id_bidang', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_biaya', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_kjb_termin',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('jenis_bayar', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('nilai', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
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
    op.create_table('import_temp_kjb_beban',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('beban_biaya', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('beban_pembeli', sa.BOOLEAN(), autoincrement=False, nullable=False)
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
    op.create_table('bidang_coba',
    sa.Column('geom', geoalchemy2.types.Geometry(spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', _spatial_index_reflected=True), autoincrement=False, nullable=True),
    sa.Column('id_bidang', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('luas_surat', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('no_peta', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('planing_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('skpt_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('id_bidang_lama', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_by_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('pemilik_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('jenis_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('group', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_surat_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('kategori_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('kategori_sub_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('kategori_proyek_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('penampung_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('manager_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('sales_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('mediator', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('telepon_mediator', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('notaris_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('informasi_tambahan', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('luas_ukur', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_gu_perorangan', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_gu_pt', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_nett', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_clear', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_pbt_perorangan', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_pbt_pt', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('bundle_hd_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('luas_bayar', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('harga_akta', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('harga_transaksi', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('sub_project_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('geom_ori', geoalchemy2.types.Geometry(spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', _spatial_index_reflected=True), autoincrement=False, nullable=True),
    sa.Column('tahap', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('njop', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_proses', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('luas_produk', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('status_pembebasan', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('parent_id', postgresql.UUID(), autoincrement=False, nullable=True)
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
    op.create_table('import_id_bidang_lama',
    sa.Column('id_bidang_lama', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id_bidang_lama', name='import_id_bidang_lama_pkey')
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
    op.create_table('import_temp_kjb_harga',
    sa.Column('kjb_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('jenis_alashak', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('harga_akta', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('harga_transaksi', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False)
    )
    op.create_table('import_temp_spk',
    sa.Column('nomor_spk', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('remark', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('id_bidang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('alashak', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('jenis_bayar', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('nilai', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.drop_index(op.f('ix_invoice_bayar_id'), table_name='invoice_bayar')
    op.drop_table('invoice_bayar')
    # ### end Alembic commands ###
