"""__is ptsl on bidang

Revision ID: 2e7f3c8a436b
Revises: b1a85abe0876
Create Date: 2024-06-03 06:30:14.104160

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '2e7f3c8a436b'
down_revision = 'b1a85abe0876'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bidang', sa.Column('is_ptsl', sa.Boolean(), nullable=True))
    op.add_column('bidangorigin', sa.Column('is_ptsl', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bidangorigin', 'is_ptsl')
    op.drop_column('bidang', 'is_ptsl')
    # ### end Alembic commands ###