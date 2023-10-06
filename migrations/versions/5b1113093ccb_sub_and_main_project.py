"""sub and main project

Revision ID: 5b1113093ccb
Revises: 1298bb73b8a9
Create Date: 2023-10-06 16:07:21.545846

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '5b1113093ccb'
down_revision = '1298bb73b8a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'project', 'main_project', ['main_project_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'project', type_='foreignkey')
    # ### end Alembic commands ###
