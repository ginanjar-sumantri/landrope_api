"""_m_0006

Revision ID: 786780e01a5c
Revises: b90e8680ad4c
Create Date: 2023-10-15 20:20:52.320754

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '786780e01a5c'
down_revision = 'b90e8680ad4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bidang', sa.Column('geom_ori', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))
    # op.create_index('idx_bidang_geom_ori', 'bidang', ['geom_ori'], unique=False, postgresql_using='gist')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_bidang_geom_ori', table_name='bidang', postgresql_using='gist')
    op.drop_column('bidang', 'geom_ori')
    # ### end Alembic commands ###
