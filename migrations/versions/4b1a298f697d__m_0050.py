"""_m_0050

Revision ID: 4b1a298f697d
Revises: 8d035631f4fb
Create Date: 2023-12-27 15:17:53.658476

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4b1a298f697d'
down_revision = '8d035631f4fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('draft', sa.Column('gps_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('gps', sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.drop_constraint('gps_desa_id_fkey', 'gps', type_='foreignkey')
    op.create_foreign_key(None, 'gps', 'planing', ['planing_id'], ['id'])
    op.drop_column('gps', 'desa_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('gps', sa.Column('desa_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'gps', type_='foreignkey')
    op.create_foreign_key('gps_desa_id_fkey', 'gps', 'desa', ['desa_id'], ['id'])
    op.drop_column('gps', 'planing_id')
    op.drop_column('draft', 'gps_id')
    # ### end Alembic commands ###
