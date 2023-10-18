"""_m_0007

Revision ID: 962ffd1ad3fa
Revises: 786780e01a5c
Create Date: 2023-10-18 12:00:21.297189

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '962ffd1ad3fa'
down_revision = '786780e01a5c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bidang_overlap', sa.Column('geom_temp', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))
    op.alter_column('bidang_overlap', 'parent_bidang_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    op.alter_column('bidang_overlap', 'parent_bidang_intersect_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    op.alter_column('bidang_overlap', 'luas',
               existing_type=sa.NUMERIC(),
               nullable=True)
    # op.create_index('idx_bidang_overlap_geom_temp', 'bidang_overlap', ['geom_temp'], unique=False, postgresql_using='gist')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_bidang_overlap_geom_temp', table_name='bidang_overlap', postgresql_using='gist')
    op.alter_column('bidang_overlap', 'luas',
               existing_type=sa.NUMERIC(),
               nullable=False)
    op.alter_column('bidang_overlap', 'parent_bidang_intersect_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    op.alter_column('bidang_overlap', 'parent_bidang_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    op.drop_column('bidang_overlap', 'geom_temp')
    # ### end Alembic commands ###
