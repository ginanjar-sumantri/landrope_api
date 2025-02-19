"""_m_0044

Revision ID: 9445d914b469
Revises: 58ac70f90c4d
Create Date: 2023-12-15 05:41:20.797080

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '9445d914b469'
down_revision = '58ac70f90c4d'
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
    op.add_column('beban_biaya', sa.Column('formula', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('beban_biaya', 'is_njop')
    op.add_column('bidang_komponen_biaya', sa.Column('estimated_amount', sa.Numeric(), nullable=True))
    op.add_column('bidang_komponen_biaya', sa.Column('formula', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('bidang_komponen_biaya', 'is_use')
    op.add_column('invoice_detail', sa.Column('amount', sa.Numeric(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('invoice_detail', 'amount')
    op.add_column('bidang_komponen_biaya', sa.Column('is_use', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('bidang_komponen_biaya', 'formula')
    op.drop_column('bidang_komponen_biaya', 'estimated_amount')
    op.add_column('beban_biaya', sa.Column('is_njop', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('beban_biaya', 'formula')
    op.drop_index(op.f('ix_workflow_history_id'), table_name='workflow_history')
    op.drop_table('workflow_history')
    op.drop_index(op.f('ix_workflow_template_id'), table_name='workflow_template')
    op.drop_table('workflow_template')
    op.drop_index(op.f('ix_workflow_id'), table_name='workflow')
    op.drop_table('workflow')
    # ### end Alembic commands ###
