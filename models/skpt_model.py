from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from enum import Enum
from datetime import date
from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID
from models.mapping_model import MappingPlaningSkpt

if TYPE_CHECKING:
    from models.ptsk_model import Ptsk 
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang
    from models.planing_model import Planing
    from models.gps_model import Gps

class StatusSKEnum(str, Enum):
    Belum_Pengajuan_SK = "Belum_Pengajuan_SK"
    Pengajuan_Awal_SK  = "Pengajuan_Awal_SK"
    Final_SK = "Final_SK"

class KategoriEnum(str, Enum):
    SK_Orang = "SK_Orang"
    SK_ASG = "SK_ASG"

class SkptBase(SQLModel):
    status:StatusSKEnum | None = Field(nullable=True)
    kategori:KategoriEnum | None = Field(nullable=True)
    luas:Decimal
    nomor_sk:str | None = Field(nullable=True, max_length=200)
    tanggal_tahun_SK:date | None = Field(nullable=True)
    tanggal_jatuh_tempo:date | None = Field(nullable=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")

class SkptRawBase(BaseUUIDModel, SkptBase):
    pass

class SkptFullBase(BaseGeoModel, SkptRawBase):
    pass

class Skpt(SkptFullBase, table=True):
    ptsk:"Ptsk" = Relationship(back_populates="skpts", sa_relationship_kwargs={'lazy':'selectin'})
    planings:list["Planing"] = Relationship(back_populates="skpts", link_model=MappingPlaningSkpt, sa_relationship_kwargs={'lazy':'selectin'})
    rinciks: list["Rincik"] = Relationship(back_populates="skpt", sa_relationship_kwargs={'lazy':'selectin'})
    bidangs: list["Bidang"] = Relationship(back_populates="skpt", sa_relationship_kwargs={'lazy':'selectin'})
    gpsts:list["Gps"] = Relationship(back_populates="skpt", sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def ptsk_name(self)-> str:
        return self.ptsk.name
    
    @property
    def ptsk_code(self)-> str:
        return self.ptsk.code 