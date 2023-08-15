"""link request petlok with hasi petlok

Revision ID: 0a36f9bd9b51
Revises: 265553125d67
Create Date: 2023-08-15 18:07:13.544613

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '0a36f9bd9b51'
down_revision = '265553125d67'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hasil_peta_lokasi', sa.Column('request_peta_lokasi_id', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.add_column('hasil_peta_lokasi', sa.Column('status_hasil_peta_lokasi', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.create_foreign_key(None, 'hasil_peta_lokasi', 'request_peta_lokasi', ['request_peta_lokasi_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'hasil_peta_lokasi', type_='foreignkey')
    op.drop_column('hasil_peta_lokasi', 'status_hasil_peta_lokasi')
    op.drop_column('hasil_peta_lokasi', 'request_peta_lokasi_id')
    # ### end Alembic commands ###
