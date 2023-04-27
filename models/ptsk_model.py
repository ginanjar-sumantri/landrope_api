from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingPlaningPtsk
from enum import Enum
from datetime import date
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.skpt_model import Skpt
    # from models.rincik_model import Rincik
    # from models.bidang_model import Bidang, Bidangoverlap

# class StatusSKEnum(str, Enum):
#     Belum_Pengajuan_SK = "Belum_Pengajuan_SK"
#     Pengajuan_Awal_SK  = "Pengajuan_Awal_SK"
#     Final_SK = "Final_SK"

# class KategoriEnum(str, Enum):
#     SK_Orang = "SK_Orang"
#     SK_ASG = "SK_ASG"

class PtskBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str | None  = Field(nullable=True, max_length=50)
    # status:StatusSKEnum | None = Field(nullable=True)
    # kategori:KategoriEnum | None = Field(nullable=True)
    # luas:Decimal
    # nomor_sk:str | None = Field(nullable=True, max_length=200)
    # tanggal_tahun_SK:date | None = Field(nullable=True)
    # tanggal_jatuh_tempo:date | None = Field(nullable=True)

class PtskRawBase(BaseUUIDModel, PtskBase):
    pass

class PtskFullBase(PtskRawBase):
    pass

class Ptsk(PtskFullBase, table=True):
    planings: list["Planing"] = Relationship(back_populates="ptsks", link_model=MappingPlaningPtsk, sa_relationship_kwargs={'lazy':'selectin'})
    skpts: list["Skpt"] = Relationship(back_populates="ptsk", sa_relationship_kwargs={'lazy':'selectin'})
    # bidangs: list["Bidang"] = Relationship(back_populates="ptsk", sa_relationship_kwargs={'lazy':'selectin'})
    # overlaps:list["Bidangoverlap"] = Relationship(back_populates="ptsk", sa_relationship_kwargs={'lazy':'selectin'})

