"""28 AGUSTUS 2024 15:09 - Date cut off on Closing

Revision ID: d1f3d985f113
Revises: 4254c6bccf17
Create Date: 2024-08-28 15:08:38.745720

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'd1f3d985f113'
down_revision = '4254c6bccf17'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('planing_closing', sa.Column('date_cut_off', sa.Date(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('planing_closing', 'date_cut_off')
    # ### end Alembic commands ###