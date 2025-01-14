"""_m_0052

Revision ID: 9ba12b67c9a9
Revises: efd562e1ce39
Create Date: 2023-12-29 20:54:28.672847

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '9ba12b67c9a9'
down_revision = 'efd562e1ce39'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('workflow',
    sa.Column('reference_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('step_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_status', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_status_at', sa.DateTime(), nullable=True),
    sa.Column('last_step_app_email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_step_app_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_step_app_action', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_step_app_action_at', sa.DateTime(), nullable=True),
    sa.Column('last_step_app_action_remarks', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('entity', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('flow_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_id'), 'workflow', ['id'], unique=False)
    op.create_table('workflow_template',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('entity', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('flow_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_template_id'), 'workflow_template', ['id'], unique=False)
    op.create_table('workflow_history',
    sa.Column('workflow_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('step_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_status', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_status_at', sa.DateTime(), nullable=True),
    sa.Column('last_step_app_email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_step_app_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_step_app_action', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_step_app_action_at', sa.DateTime(), nullable=True),
    sa.Column('last_step_app_action_remarks', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
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
    op.create_index(op.f('ix_workflow_history_id'), 'workflow_history', ['id'], unique=False)
    op.drop_table('import_bidang_paid')
    op.add_column('beban_biaya', sa.Column('formula', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('beban_biaya', 'is_njop')
    op.add_column('bidang_komponen_biaya', sa.Column('estimated_amount', sa.Numeric(), nullable=True))
    op.add_column('bidang_komponen_biaya', sa.Column('formula', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('bidang_komponen_biaya', 'is_use')
    op.add_column('draft', sa.Column('gps_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('gps', sa.Column('alashak', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('gps', sa.Column('tanggal', sa.Date(), nullable=True))
    op.add_column('gps', sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('gps', sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_foreign_key(None, 'gps', 'planing', ['planing_id'], ['id'])
    op.drop_column('gps', 'alas_hak')
    op.drop_column('gps', 'desa')
    op.add_column('hasil_peta_lokasi', sa.Column('luas_pbt_perorangan', sa.Numeric(), nullable=True))
    op.add_column('hasil_peta_lokasi', sa.Column('luas_pbt_pt', sa.Numeric(), nullable=True))
    op.add_column('invoice_detail', sa.Column('amount', sa.Numeric(), nullable=True))
    op.add_column('kjb_dt', sa.Column('group', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('payment', sa.Column('bank_code', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('spk', sa.Column('is_void', sa.Boolean(), nullable=True))
    op.add_column('spk', sa.Column('void_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('spk', sa.Column('void_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('spk', sa.Column('void_at', sa.Date(), nullable=True))
    op.create_foreign_key(None, 'spk', 'worker', ['void_by_id'], ['id'])
    op.add_column('tanda_terima_notaris_hd', sa.Column('group', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('termin', sa.Column('void_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('termin', sa.Column('void_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('termin', sa.Column('void_at', sa.Date(), nullable=True))
    op.create_foreign_key(None, 'termin', 'worker', ['void_by_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'termin', type_='foreignkey')
    op.drop_column('termin', 'void_at')
    op.drop_column('termin', 'void_reason')
    op.drop_column('termin', 'void_by_id')
    op.drop_column('tanda_terima_notaris_hd', 'group')
    op.drop_constraint(None, 'spk', type_='foreignkey')
    op.drop_column('spk', 'void_at')
    op.drop_column('spk', 'void_reason')
    op.drop_column('spk', 'void_by_id')
    op.drop_column('spk', 'is_void')
    op.drop_column('payment', 'bank_code')
    op.drop_column('kjb_dt', 'group')
    op.drop_column('invoice_detail', 'amount')
    op.drop_column('hasil_peta_lokasi', 'luas_pbt_pt')
    op.drop_column('hasil_peta_lokasi', 'luas_pbt_perorangan')
    op.add_column('gps', sa.Column('desa', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('gps', sa.Column('alas_hak', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'gps', type_='foreignkey')
    op.drop_column('gps', 'remark')
    op.drop_column('gps', 'planing_id')
    op.drop_column('gps', 'tanggal')
    op.drop_column('gps', 'alashak')
    op.drop_column('draft', 'gps_id')
    op.add_column('bidang_komponen_biaya', sa.Column('is_use', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('bidang_komponen_biaya', 'formula')
    op.drop_column('bidang_komponen_biaya', 'estimated_amount')
    op.add_column('beban_biaya', sa.Column('is_njop', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('beban_biaya', 'formula')
    op.create_table('import_bidang_paid',
    sa.Column('id_bidang_lama', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('no_tahap', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('luas_bayar', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('harga_transaksi', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.Column('paid_amount', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id_bidang_lama', name='import_bidang_paid_pkey')
    )
    op.drop_index(op.f('ix_workflow_history_id'), table_name='workflow_history')
    op.drop_table('workflow_history')
    op.drop_index(op.f('ix_workflow_template_id'), table_name='workflow_template')
    op.drop_table('workflow_template')
    op.drop_index(op.f('ix_workflow_id'), table_name='workflow')
    op.drop_table('workflow')
    # ### end Alembic commands ###
