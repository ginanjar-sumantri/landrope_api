"""_m_0076

Revision ID: 1ea446e5e65b
Revises: 3773b9f50575
Create Date: 2024-02-28 14:24:05.761635

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '1ea446e5e65b'
down_revision = '3773b9f50575'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bidang', sa.Column('parent_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_foreign_key(None, 'bidang', 'bidang', ['parent_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'bidang', type_='foreignkey')
    op.drop_column('bidang', 'parent_id')
    # ### end Alembic commands ###
