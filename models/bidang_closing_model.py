from sqlmodel import SQLModel, Field
from models.base_model import BaseUUIDModel
from common.enum import StatusBidangEnum, KategoriLahanEnum

from uuid import UUID
from decimal import Decimal
from datetime import date


class BidangClosingBase(SQLModel):
    bidang_id: UUID = Field(nullable=False, foreign_key="bidang.id")
    planing_id: UUID = Field(nullable=False, foreign_key="planing.id")
    status: StatusBidangEnum = Field(nullable=False)
    luas_surat: Decimal = Field(default=0, nullable=False)
    luas_bayar: Decimal = Field(default=0, nullable=False)
    kategori_lahan: KategoriLahanEnum = Field(default=KategoriLahanEnum.DARAT, nullable=False)
    date_cut_off: date = Field(nullable=False)
    kategori_id: UUID | None = Field(nullable=True, foreign_key="kategori.id")

class BidangClosingFullBase(BaseUUIDModel, BidangClosingBase):
    pass

class BidangClosing(BidangClosingFullBase, table=True):
    pass