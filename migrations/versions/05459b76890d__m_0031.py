"""_m_0031

Revision ID: 05459b76890d
Revises: 4bf2cee65c1a
Create Date: 2023-11-29 11:52:17.818465

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '05459b76890d'
down_revision = '4bf2cee65c1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('utj_khusus',
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('pay_to', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=False),
    sa.Column('kjb_hd_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('payment_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.Column('updated_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['worker.id'], ),
    sa.ForeignKeyConstraint(['kjb_hd_id'], ['kjb_hd.id'], ),
    sa.ForeignKeyConstraint(['payment_id'], ['payment.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_utj_khusus_id'), 'utj_khusus', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_utj_khusus_id'), table_name='utj_khusus')
    op.drop_table('utj_khusus')
    # ### end Alembic commands ###
