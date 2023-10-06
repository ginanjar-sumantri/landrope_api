"""sub and main project

Revision ID: 4b1f8f4938cb
Revises: 7dba902281ab
Create Date: 2023-10-06 14:33:52.933460

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '4b1f8f4938cb'
down_revision = '7dba902281ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('main_project',
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('last_tahap', sa.Integer(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_main_project_id'), 'main_project', ['id'], unique=False)
    op.create_table('sub_project',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('project_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('main_project_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['main_project_id'], ['main_project.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sub_project_id'), 'sub_project', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_sub_project_id'), table_name='sub_project')
    op.drop_table('sub_project')
    op.drop_index(op.f('ix_main_project_id'), table_name='main_project')
    op.drop_table('main_project')
    # ### end Alembic commands ###
