from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingBidangOverlap
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID
from decimal import Decimal

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.ptsk_model import Ptsk
    from models.desa_model import Desa
    from models.rincik_model import Rincik

class StatusEnum(str, Enum):
    Bebas = "Bebas"
    Belum_Bebas = "Belum_Bebas"

class TypeEnum(str, Enum):
    Standard = "Standard"
    Bintang = "Bintang"

class BidangBase(SQLModel):
    id_bidang:str = Field(nullable=False, max_length=100)
    nama_pemilik:str
    luas_surat:Decimal
    alas_hak:str
    no_peta:str
    status:StatusEnum

    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id")

class BidangFullBase(BaseUUIDModel, BaseGeoModel, BidangBase):
    pass

class Bidang(BidangFullBase, table=True):
    type:TypeEnum

    planing:"Planing" = Relationship(back_populates="bidangs")
    ptsk:"Ptsk" = Relationship(back_populates="bidangs")
    rincik:"Rincik" = Relationship(back_populates="bidang")
    overlaps:list["Bidangoverlap"] = Relationship(back_populates="bidangs", link_model=MappingBidangOverlap)

#-------------------------------------------------------------------------------

class BidangoverlapBase(BidangBase):
    pass

class BidangoverlapFullBase(BaseUUIDModel, BaseGeoModel, BidangoverlapBase):
    pass

class Bidangoverlap(BidangoverlapFullBase, table=True):
    bidangs : list["Bidang"] = Relationship(back_populates="overlaps", link_model=MappingBidangOverlap)
