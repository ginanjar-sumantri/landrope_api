"""1_init_db_landrope

Revision ID: 8a27e44a2c5c
Revises: 
Create Date: 2023-07-03 11:05:53.718393

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '8a27e44a2c5c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('skpt_dt',
    sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('planing_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('skpt_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('luas', sa.Numeric(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['planing_id'], ['planing.id'], ),
    sa.ForeignKeyConstraint(['skpt_id'], ['skpt.id'], ),
    sa.PrimaryKeyConstraint('planing_id', 'skpt_id', 'id')
    )
    # op.create_index('idx_skpt_dt_geom', 'skpt_dt', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_skpt_dt_id'), 'skpt_dt', ['id'], unique=False)
    op.drop_index('idx_skpt_geom', table_name='skpt')
    op.drop_column('skpt', 'geom')
    op.drop_column('skpt', 'luas')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('skpt', sa.Column('luas', sa.NUMERIC(), autoincrement=False, nullable=True))
    op.add_column('skpt', sa.Column('geom', geoalchemy2.types.Geometry(from_text='ST_GeomFromEWKT', name='geometry', _spatial_index_reflected=True), autoincrement=False, nullable=True))
    op.create_index('idx_skpt_geom', 'skpt', ['geom'], unique=False)
    op.drop_index(op.f('ix_skpt_dt_id'), table_name='skpt_dt')
    op.drop_index('idx_skpt_dt_geom', table_name='skpt_dt', postgresql_using='gist')
    op.drop_table('skpt_dt')
    # ### end Alembic commands ###
