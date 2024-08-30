"""30 Agustus 2024 Add field is_lock peminjaman_header

Revision ID: 0cc9e3089319
Revises: dcd0a57357f9
Create Date: 2024-08-30 17:05:59.321038

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '0cc9e3089319'
down_revision = 'dcd0a57357f9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('peminjaman_header', sa.Column('is_lock', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('peminjaman_header', 'is_lock')
    # ### end Alembic commands ###
