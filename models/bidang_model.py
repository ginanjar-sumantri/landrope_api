from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingBidangOverlap
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.ptsk_model import Ptsk
    from models.desa_model import Desa
    from models.rincik_model import Rincik

class StatusEnum(str, Enum):
    Bebas = "Bebas"
    Belum_Bebas = "Belum_Bebas"
    Batal = "Batal"

class TypeEnum(str, Enum):
    Standard = "Standard"
    Bintang = "Bintang"
    

class BidangBase(SQLModel):
    id_bidang:str = Field(nullable=False, max_length=100)
    nama_pemilik:str
    luas_surat:Decimal
    alas_hak:str
    no_peta:str
    status:StatusEnum | None = Field(nullable=True)

    planing_id:UUID = Field(default=None, foreign_key="planing.id", nullable=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", nullable=True)
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id", nullable=True)

class BidangRawBase(BaseUUIDModel, BidangBase):
    type:TypeEnum

class BidangFullBase(BaseGeoModel, BidangRawBase):
    pass

class Bidang(BidangFullBase, table=True):

    planing:"Planing" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    ptsk:"Ptsk" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    rincik:"Rincik" = Relationship(back_populates="bidang", sa_relationship_kwargs={'lazy':'selectin'})
    overlaps:list["Bidangoverlap"] = Relationship(back_populates="bidangs", link_model=MappingBidangOverlap, sa_relationship_kwargs={'lazy':'selectin'})
    
    @property
    def planing_name(self)-> str:
        return self.planing.name
    
    @property
    def project_name(self)-> str:
        return self.planing.project.name
    
    @property
    def desa_name(self)-> str:
        return self.planing.desa.name
    
    @property
    def section_name(self)-> str:
        return self.planing.project.section.name
    
    @property
    def ptsk_name(self)-> str:
        return self.ptsk.name
    
    @property
    def id_rincik(self)-> str:
        return self.rincik.id_rincik

#-------------------------------------------------------------------------------

class BidangoverlapBase(BidangBase):
    pass

class BidangoverlapFullBase(BaseUUIDModel, BaseGeoModel, BidangoverlapBase):
    pass

class Bidangoverlap(BidangoverlapFullBase, table=True):
    planing:"Planing" = Relationship(back_populates="overlaps", sa_relationship_kwargs={'lazy':'selectin'})
    ptsk:"Ptsk" = Relationship(back_populates="overlaps", sa_relationship_kwargs={'lazy':'selectin'})
    bidangs : list["Bidang"] = Relationship(back_populates="overlaps", link_model=MappingBidangOverlap, sa_relationship_kwargs={'lazy':'selectin'})
