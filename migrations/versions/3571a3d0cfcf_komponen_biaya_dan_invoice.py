"""komponen biaya dan invoice

Revision ID: 3571a3d0cfcf
Revises: 780736b4d186
Create Date: 2023-09-19 14:08:07.416697

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3571a3d0cfcf'
down_revision = '780736b4d186'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('termin',
    sa.Column('tahap_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('kjb_hd_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('jenis_bayar', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
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
    sa.Column('tanggungan_biaya', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
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
    op.drop_constraint('tahap_penampung_id_fkey', 'tahap', type_='foreignkey')
    op.drop_column('tahap', 'penampung_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tahap', sa.Column('penampung_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('tahap_penampung_id_fkey', 'tahap', 'ptsk', ['penampung_id'], ['id'])
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
    op.drop_index(op.f('ix_bidang_komponen_biaya_id'), table_name='bidang_komponen_biaya')
    op.drop_table('bidang_komponen_biaya')
    op.drop_index(op.f('ix_termin_id'), table_name='termin')
    op.drop_table('termin')
    # ### end Alembic commands ###
