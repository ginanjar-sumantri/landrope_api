"""_m_0055

Revision ID: 84ff66b465a8
Revises: 2bb75981a16b
Create Date: 2024-01-08 19:57:56.148334

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '84ff66b465a8'
down_revision = '2bb75981a16b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dokumen', sa.Column('additional_info', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('dokumen', 'is_repeat')
    op.add_column('harga_standard', sa.Column('jenis_alashak', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('harga_standard', 'jenis_alashak')
    op.add_column('dokumen', sa.Column('is_repeat', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('dokumen', 'additional_info')
    # ### end Alembic commands ###
