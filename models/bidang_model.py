from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.mapping_model import Mapping_Planing_PTSK_Desa_Rincik_Bidang, Mapping_Bidang_Overlap

class StatusEnum(str, Enum):
    Bebas = "Bebas"
    Belum_Bebas = "Belum_Bebas"

class TypeEnum(str, Enum):
    Standard = "Standard"
    Bintang = "Bintang"

class BidangBase(BaseGeoModel):
    id_bidang:str = Field(nullable=False, max_length=100)
    nama_pemilik:str
    luas:int
    alas_hak:str
    no_peta:str
    status:StatusEnum

class BidangFullBase(BaseUUIDModel, BidangBase):
    pass

class Bidang(BidangFullBase, table=True):
    type:TypeEnum

    planing_ptsk_desa_rincik_bidang: "Mapping_Planing_PTSK_Desa_Rincik_Bidang" = Relationship(back_populates="bidangs")
    bidang_overlap: "Mapping_Bidang_Overlap" = Relationship(back_populates="bidangs")

#-------------------------------------------------------------------------------

class BidangOverlapFullBase(BidangBase):
    pass

class BidangOverlap(BidangOverlapFullBase, table=True):
    bidang_overlap: "Mapping_Bidang_Overlap" = Relationship(back_populates="overlaps")
