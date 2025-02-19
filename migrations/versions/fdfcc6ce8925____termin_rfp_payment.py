"""___termin rfp payment

Revision ID: fdfcc6ce8925
Revises: c6bb484eafd2
Create Date: 2024-05-03 15:26:22.913216

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'fdfcc6ce8925'
down_revision = 'c6bb484eafd2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('terminrfppaymentlink',
    sa.Column('termin_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('rfp_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('payment_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['payment_id'], ['payment.id'], ),
    sa.ForeignKeyConstraint(['termin_id'], ['termin.id'], ),
    sa.PrimaryKeyConstraint('termin_id', 'rfp_id', 'payment_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('terminrfppaymentlink')
    # ### end Alembic commands ###
