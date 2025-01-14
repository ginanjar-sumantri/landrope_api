"""_m_0005

Revision ID: b90e8680ad4c
Revises: 5e0ee09a382e
Create Date: 2023-10-13 16:47:48.135966

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'b90e8680ad4c'
down_revision = '5e0ee09a382e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hasil_peta_lokasi', sa.Column('sub_project_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_foreign_key(None, 'hasil_peta_lokasi', 'sub_project', ['sub_project_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'hasil_peta_lokasi', type_='foreignkey')
    op.drop_column('hasil_peta_lokasi', 'sub_project_id')
    # ### end Alembic commands ###
