from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import Mapping_Planing_Ptsk_Desa_Rincik_Bidang, Mapping_Bidang_Overlap
from enum import Enum
from typing import TYPE_CHECKING

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

    planing:"Planing" = Relationship(back_populates="bidangs", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
    ptsk:"Ptsk" = Relationship(back_populates="bidangs", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
    desa:"Desa" = Relationship(back_populates="bidangs", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
    rinciks:list["Rincik"] = Relationship(back_populates="bidangs", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
    overlaps:list["Bidangoverlap"] = Relationship(back_populates="bidangs", link_model=Mapping_Bidang_Overlap)

    

#-------------------------------------------------------------------------------

class BidangoverlapBase(BaseGeoModel):
    id_bidang:str = Field(nullable=False, max_length=100)
    nama_pemilik:str
    luas:int
    alas_hak:str
    no_peta:str
    status:StatusEnum

class BidangoverlapFullBase(BaseUUIDModel, BidangoverlapBase):
    pass

class Bidangoverlap(BidangoverlapFullBase, table=True):
    bidangs : list["Bidang"] = Relationship(back_populates="overlaps", link_model=Mapping_Bidang_Overlap)
