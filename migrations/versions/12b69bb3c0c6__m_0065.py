"""_m_0065

Revision ID: 12b69bb3c0c6
Revises: 96f37bf66baf
Create Date: 2024-01-30 11:02:58.151906

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '12b69bb3c0c6'
down_revision = '96f37bf66baf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('kjb_hd', 'desa_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('kjb_hd', 'desa_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    # ### end Alembic commands ###
