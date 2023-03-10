from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import (Mapping_Planing_Ptsk, Mapping_Planing_Ptsk_Desa, 
                                      Mapping_Planing_Ptsk_Desa_Rincik, Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
from enum import Enum
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.desa_model import Desa
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang

class StatusSKEnum(str, Enum):
    Belum_Pengajuan_SK = "Belum_Pengajuan_SK"
    Pengajuan_Awal_SK  = "Pengajuan_Awal_SK"
    Final_SK = "Final_SK"

class KategoriEnum(str, Enum):
    SK_Orang = "SK_Orang"
    SK_ASG = "SK_ASG"

class PtskBase(BaseGeoModel):
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)
    status:StatusSKEnum = Field(nullable=True)
    kategori:KategoriEnum
    luas:int
    nomor_sk:str = Field(nullable=True, max_length=200)
    tanggal_tahun_SK:date = Field(nullable=True)
    tanggal_jatuh_tempo:date = Field(nullable=True)

class PtskFullBase(BaseUUIDModel, PtskBase):
    pass

class Ptsk(PtskFullBase, table=True):
    planings: list["Planing"] = Relationship(back_populates="ptsks", link_model=Mapping_Planing_Ptsk)
    desas:list["Desa"] = Relationship(back_populates="ptsks", link_model=Mapping_Planing_Ptsk_Desa)
    rinciks:list["Rincik"] = Relationship(back_populates="ptsk", link_model=Mapping_Planing_Ptsk_Desa_Rincik)
    bidangs:list["Bidang"] = Relationship(back_populates="ptsk", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
