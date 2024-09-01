from sqlmodel import SQLModel, Field
from models.base_model import BaseUUIDModel

from uuid import UUID
from decimal import Decimal
from datetime import date


class KjbDtClosingTtnBase(SQLModel):
    kjb_dt_id: UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    project_by_ttn_id: UUID | None = Field(nullable=True, foreign_key="project.id")
    desa_by_ttn_id: UUID | None = Field(nullable=True, foreign_key="desa.id")
    luas_surat_by_ttn: Decimal = Field(nullable=False, default=0)
    date_cut_off: date = Field(nullable=False)

class KjbDtClosingTtnFullBase(BaseUUIDModel, KjbDtClosingTtnBase):
    pass

class KjbDtClosingTtn(KjbDtClosingTtnFullBase, table=True):
    pass