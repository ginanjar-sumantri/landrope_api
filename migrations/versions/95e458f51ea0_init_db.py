"""init_db

Revision ID: 50c085e575b1
Revises: 
Create Date: 2023-03-20 19:55:53.990354

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '95e458f51ea0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('desa',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('luas', sa.Numeric(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_index('idx_desa_geom', 'desa', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_desa_id'), 'desa', ['id'], unique=False)
    op.create_table('jenis_lahan',
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jenis_lahan_id'), 'jenis_lahan', ['id'], unique=False)
    op.create_table('ptsk',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('kategori', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('luas', sa.Integer(), nullable=False),
    sa.Column('nomor_sk', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
    sa.Column('tanggal_tahun_SK', sa.Date(), nullable=True),
    sa.Column('tanggal_jatuh_tempo', sa.Date(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_index('idx_ptsk_geom', 'ptsk', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_ptsk_id'), 'ptsk', ['id'], unique=False)
    op.create_table('section',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_section_id'), 'section', ['id'], unique=False)
    op.create_table('project',
    sa.Column('section_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['section_id'], ['section.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_id'), 'project', ['id'], unique=False)
    op.create_table('planing',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('project_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('desa_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('luas', sa.Numeric(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['desa_id'], ['desa.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_index('idx_planing_geom', 'planing', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_planing_id'), 'planing', ['id'], unique=False)
    op.create_table('mappingplaningptsk',
    sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('ptsk_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['planing_id'], ['planing.id'], ),
    sa.ForeignKeyConstraint(['ptsk_id'], ['ptsk.id'], ),
    sa.PrimaryKeyConstraint('planing_id', 'ptsk_id')
    )
    op.create_table('rincik',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('id_rincik', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('estimasi_nama_pemilik', sqlmodel.sql.sqltypes.AutoString(length=250), nullable=False),
    sa.Column('luas', sa.Numeric(), nullable=False),
    sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('alas_hak', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('jenis_dokumen', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('no_peta', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('jenis_lahan_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('ptsk_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['jenis_lahan_id'], ['jenis_lahan.id'], ),
    sa.ForeignKeyConstraint(['planing_id'], ['planing.id'], ),
    sa.ForeignKeyConstraint(['ptsk_id'], ['ptsk.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_index('idx_rincik_geom', 'rincik', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_rincik_id'), 'rincik', ['id'], unique=False)
    op.create_table('bidang',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('id_bidang', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('nama_pemilik', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('luas_surat', sa.Numeric(), nullable=False),
    sa.Column('alas_hak', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('no_peta', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('ptsk_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('rincik_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['planing_id'], ['planing.id'], ),
    sa.ForeignKeyConstraint(['ptsk_id'], ['ptsk.id'], ),
    sa.ForeignKeyConstraint(['rincik_id'], ['rincik.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_index('idx_bidang_geom', 'bidang', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_bidang_id'), 'bidang', ['id'], unique=False)
    op.create_table('bidangoverlap',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('id_bidang', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('nama_pemilik', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('luas_surat', sa.Numeric(), nullable=False),
    sa.Column('alas_hak', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('no_peta', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('ptsk_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('rincik_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['planing_id'], ['planing.id'], ),
    sa.ForeignKeyConstraint(['ptsk_id'], ['ptsk.id'], ),
    sa.ForeignKeyConstraint(['rincik_id'], ['rincik.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_index('idx_bidangoverlap_geom', 'bidangoverlap', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_bidangoverlap_id'), 'bidangoverlap', ['id'], unique=False)
    op.create_table('mappingbidangoverlap',
    sa.Column('bidang_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('bidang_overlap_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('luas', sa.Numeric(), nullable=False),
    sa.ForeignKeyConstraint(['bidang_id'], ['bidang.id'], ),
    sa.ForeignKeyConstraint(['bidang_overlap_id'], ['bidangoverlap.id'], ),
    sa.PrimaryKeyConstraint('bidang_id', 'bidang_overlap_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('mappingbidangoverlap')
    op.drop_index(op.f('ix_bidangoverlap_id'), table_name='bidangoverlap')
    op.drop_index('idx_bidangoverlap_geom', table_name='bidangoverlap', postgresql_using='gist')
    op.drop_table('bidangoverlap')
    op.drop_index(op.f('ix_bidang_id'), table_name='bidang')
    op.drop_index('idx_bidang_geom', table_name='bidang', postgresql_using='gist')
    op.drop_table('bidang')
    op.drop_index(op.f('ix_rincik_id'), table_name='rincik')
    op.drop_index('idx_rincik_geom', table_name='rincik', postgresql_using='gist')
    op.drop_table('rincik')
    op.drop_table('mappingplaningptsk')
    op.drop_index(op.f('ix_planing_id'), table_name='planing')
    op.drop_index('idx_planing_geom', table_name='planing', postgresql_using='gist')
    op.drop_table('planing')
    op.drop_index(op.f('ix_project_id'), table_name='project')
    op.drop_table('project')
    op.drop_index(op.f('ix_section_id'), table_name='section')
    op.drop_table('section')
    op.drop_index(op.f('ix_ptsk_id'), table_name='ptsk')
    op.drop_index('idx_ptsk_geom', table_name='ptsk', postgresql_using='gist')
    op.drop_table('ptsk')
    op.drop_index(op.f('ix_jenis_lahan_id'), table_name='jenis_lahan')
    op.drop_table('jenis_lahan')
    op.drop_index(op.f('ix_desa_id'), table_name='desa')
    op.drop_index('idx_desa_geom', table_name='desa', postgresql_using='gist')
    op.drop_table('desa')
    # ### end Alembic commands ###
