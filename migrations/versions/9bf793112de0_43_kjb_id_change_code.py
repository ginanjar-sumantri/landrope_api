"""43 kjb_id change code

Revision ID: 9bf793112de0
Revises: 892a9f30fc2d
Create Date: 2023-06-23 20:11:15.931258

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '9bf793112de0'
down_revision = '892a9f30fc2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('kjb_hd', sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.drop_column('kjb_hd', 'kjb_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('kjb_hd', sa.Column('kjb_id', sa.VARCHAR(length=500), autoincrement=False, nullable=False))
    op.drop_column('kjb_hd', 'code')
    # ### end Alembic commands ###
