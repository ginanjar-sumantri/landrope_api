from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingBidangOverlap
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from common.enum import (JenisBidangEnum, StatusBidangEnum, JenisAlashakEnum, CategoryEnum, JenisDokumenEnum, StatusBidangEnum, TipeProsesEnum, TipeBidangEnum)

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.skpt_model import Skpt
    from models.master_model import JenisLahan
    

class BidangBase(SQLModel):
    id_bidang:str | None = Field(nullable=False, max_length=100)
    id_bidang_lama:str | None =  Field(nullable=True)
    nama_pemilik:str | None
    luas_surat:Decimal
    alas_hak:str
    no_peta:str
    category:CategoryEnum | None = Field(nullable=True)
    jenis_dokumen: JenisDokumenEnum | None = Field(nullable=True)
    status:StatusBidangEnum | None = Field(nullable=True)

    jenis_lahan_id:UUID | None = Field(default=None, foreign_key="jenis_lahan.id", nullable=True)
    planing_id:UUID | None = Field(default=None, foreign_key="planing.id", nullable=True)
    skpt_id:UUID | None = Field(default=None, foreign_key="skpt.id", nullable=True)

# class BidangBase(SQLModel):
#     id_bidang:Optional[str] = Field(nullable=False, max_length=150)
#     id_bidang_lama:Optional[str] = Field(nullable=True)
#     no_peta:Optional[str] = Field(nullable=True)
#     pemilik_id:Optional[UUID] = Field(nullable=True, foreign_key="pemilik.id")
#     jenis_bidang:JenisBidangEnum = Field(nullable=False)
#     status:StatusBidangEnum = Field(nullable=False)
#     planing_id:Optional[UUID] = Field(nullable=True, foreign_key="planing.id")
#     group:Optional[str] = Field(nullable=True)
#     jenis_alashak:Optional[JenisAlashakEnum]
#     jenis_surat_id:Optional[UUID] = Field(nullable=True, foreign_key="jenis_surat.id")
#     alashak:Optional[str] = Field(nullable=True)
#     luas_surat:Optional[Decimal] = Field(nullable=True)
#     kategori_id:Optional[UUID] = Field(nullable=True)
#     sub_kategori_id:Optional[UUID] = Field(nullable=True)
#     kategori_proyek_id:Optional[UUID] = Field(nullable=True)
#     skpt_id:Optional[UUID] = Field(nullable=True) #PT SK
#     penampung_id:Optional[UUID] = Field(nullable=True) #PT Penampung

    
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
    def desa_code(self)-> str | None:
        if self.planing is None:
            return ""
        if self.planing.desa is None:
            return ""
        
        return self.planing.desa.code or ""
    
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
    

