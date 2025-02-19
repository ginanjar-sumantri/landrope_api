"""_m_083

Revision ID: e901140315d5
Revises: 54b1884817ed
Create Date: 2024-03-08 19:25:13.303645

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'e901140315d5'
down_revision = '54b1884817ed'
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
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_workflow_next_approver_id'), table_name='workflow_next_approver')
    op.drop_table('workflow_next_approver')
    # ### end Alembic commands ###
