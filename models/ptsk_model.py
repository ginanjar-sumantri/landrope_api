from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from enum import Enum
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.mapping_model import (Mapping_Planing_PTSK, Mapping_Planing_PTSK_Desa, 
                                      Mapping_Planing_PTSK_Desa_Rincik, Mapping_Planing_PTSK_Desa_Rincik_Bidang)

class StatusSKEnum(str, Enum):
    Belum_Pengajuan_SK = "Belum_Pengajuan_SK"
    Pengajuan_Awal_SK  = "Pengajuan_Awal_SK"
    Final_SK = "Final_SK"

class KategoriEnum(str, Enum):
    SK_Orang = "SK_Orang"
    SK_ASG = "SK_ASG"

class PTSKBase(BaseGeoModel):
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)
    status:StatusSKEnum = Field(nullable=True)
    kategori:KategoriEnum
    luas:int
    nomor_sk:str = Field(nullable=True, max_length=200)
    tanggal_tahun_SK:date = Field(nullable=True)
    tanggal_jatuh_tempo:date = Field(nullable=True)

class PTSKFullBase(BaseUUIDModel, PTSKBase):
    pass

class PTSK(PTSKFullBase, table=True):
    planing_ptsk: "Mapping_Planing_PTSK" = Relationship(back_populates="ptsks")
    planing_ptsk_desa: "Mapping_Planing_PTSK_Desa" = Relationship(back_populates="ptsks")
    planing_ptsk_desa_rincik: "Mapping_Planing_PTSK_Desa_Rincik" = Relationship(back_populates="ptsks")
    planing_ptsk_desa_rincik_bidang: "Mapping_Planing_PTSK_Desa_Rincik_Bidang" = Relationship(back_populates="ptsks")
