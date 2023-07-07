"""7_history_data_in_bundle_dt

Revision ID: 6d48f77f9ba7
Revises: e6961c0d8ea6
Create Date: 2023-07-07 17:02:29.093651

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '6d48f77f9ba7'
down_revision = 'e6961c0d8ea6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bundle_dt', sa.Column('history_data', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bundle_dt', 'history_data')
    # ### end Alembic commands ###
