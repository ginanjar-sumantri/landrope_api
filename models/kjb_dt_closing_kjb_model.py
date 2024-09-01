from sqlmodel import SQLModel, Field
from models.base_model import BaseUUIDModel

from uuid import UUID
from decimal import Decimal
from datetime import date


class KjbDtClosingKjbBase(SQLModel):
    kjb_dt_id: UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    project_id: UUID | None = Field(nullable=True, foreign_key="project.id")
    desa_id: UUID | None = Field(nullable=True, foreign_key="desa.id")
    luas_surat: Decimal = Field(nullable=False, default=0)
    date_cut_off: date = Field(nullable=False)

class KjbDtClosingKjbFullBase(BaseUUIDModel, KjbDtClosingKjbBase):
    pass

class KjbDtClosingKjb(KjbDtClosingKjbFullBase, table=True):
    pass