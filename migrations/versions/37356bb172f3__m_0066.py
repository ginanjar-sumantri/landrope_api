"""_m_0066

Revision ID: 37356bb172f3
Revises: 12b69bb3c0c6
Create Date: 2024-01-30 11:44:25.034110

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '37356bb172f3'
down_revision = '12b69bb3c0c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('keterangan_req_petlok',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keterangan_req_petlok_id'), 'keterangan_req_petlok', ['id'], unique=False)
    op.add_column('request_peta_lokasi', sa.Column('keterangan_req_petlok_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_foreign_key(None, 'request_peta_lokasi', 'keterangan_req_petlok', ['keterangan_req_petlok_id'], ['id'])
    op.drop_column('request_peta_lokasi', 'is_disabled')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('request_peta_lokasi', sa.Column('is_disabled', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'request_peta_lokasi', type_='foreignkey')
    op.drop_column('request_peta_lokasi', 'keterangan_req_petlok_id')
    op.drop_index(op.f('ix_keterangan_req_petlok_id'), table_name='keterangan_req_petlok')
    op.drop_table('keterangan_req_petlok')
    # ### end Alembic commands ###
