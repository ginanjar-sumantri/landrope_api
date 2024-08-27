from sqlmodel import SQLModel, Field
from models.base_model import BaseUUIDModel
from common.enum import StatusBidangEnum, KategoriLahanEnum

from uuid import UUID
from decimal import Decimal
from datetime import date


class PlaningClosingBase(SQLModel):
    planing_id: UUID = Field(nullable=False, foreign_key="planing.id")
    luas: Decimal = Field(nullable=False, default=0)

class PlaningClosingFullBase(BaseUUIDModel, PlaningClosingBase):
    pass

class PlaningClosing(PlaningClosingFullBase, table=True):
    pass