from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingBidangOverlap
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from common.enum import CategoryEnum, JenisDokumenEnum, StatusEnum, TipeProsesEnum, TipeBidangEnum

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.skpt_model import Skpt
    from models.master_model import JenisLahan
    

class BidangBase(SQLModel):
    id_bidang:str | None = Field(nullable=False, max_length=100)
    nama_pemilik:str | None
    luas_surat:Decimal
    alas_hak:str
    no_peta:str
    category:CategoryEnum | None = Field(nullable=True)
    jenis_dokumen: JenisDokumenEnum | None = Field(nullable=True)
    status:StatusEnum | None = Field(nullable=True)

    jenis_lahan_id:UUID | None = Field(default=None, foreign_key="jenis_lahan.id", nullable=True)
    planing_id:UUID | None = Field(default=None, foreign_key="planing.id", nullable=True)
    skpt_id:UUID | None = Field(default=None, foreign_key="skpt.id", nullable=True)
    
class BidangExtBase(BidangBase):
    tipe_proses:TipeProsesEnum | None = Field(default=None, nullable=True)
    tipe_bidang:TipeBidangEnum | None = Field(default=None, nullable=True)

class BidangRawBase(BaseUUIDModel, BidangExtBase):
    pass

class BidangFullBase(BaseGeoModel, BidangRawBase):
    pass

class Bidang(BidangFullBase, table=True):
    planing:"Planing" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    skpt:"Skpt" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    jenis_lahan: "JenisLahan" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def planing_name(self)-> str | None:
        if self.planing is None:
            return ""
        
        return self.planing.name or ""
    
    @property
    def project_name(self)-> str | None:
        if self.planing is None:
            return ""
        if self.planing.project is None:
            return ""
        
        return self.planing.project.name or ""
    
    @property
    def desa_name(self)-> str | None:
        if self.planing is None:
            return ""
        if self.planing.desa is None:
            return ""
        
        return self.planing.desa.name or ""
    
    @property
    def section_name(self)-> str | None:
        if self.planing is None:
            return ""
        if self.planing.project is None:
            return ""
        if self.planing.project.section is None:
            return ""
        
        return self.planing.project.section.name or ""
    
    @property
    def ptsk_name(self)-> str | None:
        if self.skpt is None:
            return ""
        if self.skpt.ptsk is None:
            return ""
        
        return self.skpt.ptsk.name or ""
    
    @property
    def nomor_sk(self)-> str | None:
        if self.skpt is None:
            return ""
        return self.skpt.nomor_sk or ""
    
    @property
    def jenis_lahan_name(self)-> str:
        if self.jenis_lahan is None:
            return ""
        return self.jenis_lahan.name

#-------------------------------------------------------------------------------

# class BidangoverlapBase(BidangBase):
#     pass

# class BidangoverlapRawBase(BaseUUIDModel, BidangoverlapBase):
#     pass

# class BidangoverlapFullBase(BaseGeoModel, BidangoverlapRawBase):
#     pass

# class Bidangoverlap(BidangoverlapFullBase, table=True):
#     planing:"Planing" = Relationship(back_populates="overlaps", sa_relationship_kwargs={'lazy':'selectin'})
#     skpt:"Skpt" = Relationship(back_populates="overlaps", sa_relationship_kwargs={'lazy':'selectin'})
#     # bidangs : list["Bidang"] = Relationship(back_populates="overlaps", link_model=MappingBidangOverlap, sa_relationship_kwargs={'lazy':'selectin'})

#     @property
#     def planing_name(self)-> str:
#         return self.planing.name
    
#     @property
#     def ptsk_name(self)-> str:
#         return self.ptsk.name
    

