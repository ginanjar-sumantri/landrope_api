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
    from models.ptsk_model import Ptsk
    from models.pemilik_model import Pemilik
    from models.master_model import JenisSurat
    from models.kategori_model import Kategori, KategoriSub, KategoriProyek
    from models.marketing_model import Manager, Sales
    from models.notaris_model import Notaris
    
class BidangBase(SQLModel):
    id_bidang:Optional[str] = Field(nullable=False, max_length=150)
    id_bidang_lama:Optional[str] = Field(nullable=True)
    no_peta:Optional[str] = Field(nullable=True)
    pemilik_id:Optional[UUID] = Field(nullable=True, foreign_key="pemilik.id")
    jenis_bidang:JenisBidangEnum = Field(nullable=True)
    status:StatusBidangEnum = Field(nullable=False)
    planing_id:Optional[UUID] = Field(nullable=True, foreign_key="planing.id")
    group:Optional[str] = Field(nullable=True)
    jenis_alashak:Optional[JenisAlashakEnum]
    jenis_surat_id:Optional[UUID] = Field(nullable=True, foreign_key="jenis_surat.id")
    alashak:Optional[str] = Field(nullable=True)
    kategori_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori.id")
    kategori_sub_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori_sub.id")
    kategori_proyek_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori_proyek.id")
    skpt_id:Optional[UUID] = Field(nullable=True, foreign_key="skpt.id") #PT SK
    penampung_id:Optional[UUID] = Field(nullable=True, foreign_key="ptsk.id") #PT Penampung
    manager_id:Optional[UUID] = Field(nullable=True, foreign_key="manager.id")
    sales_id:Optional[UUID] = Field(nullable=True, foreign_key="sales.id")
    madiator:Optional[str] = Field(nullable=True)
    telepon_mediator:Optional[str] = Field(nullable=True)
    notaris_id:Optional[UUID] = Field(nullable=True, foreign_key="notaris.id")
    tahap:Optional[str] = Field(nullable=True)
    informasi_tambahan:Optional[str] = Field(nullable=True)
    luas_surat:Optional[Decimal] = Field(nullable=True)
    luas_ukur:Optional[Decimal] = Field(nullable=True)
    luas_gu_perorangan:Optional[Decimal] = Field(nullable=True)
    luas_gu_pt:Optional[Decimal] = Field(nullable=True)
    luas_nett:Optional[Decimal] = Field(nullable=True)
    luas_clear:Optional[Decimal] = Field(nullable=True)
    luas_pbt_perorangan:Optional[Decimal] = Field(nullable=True)
    luas_pbt_pt:Optional[Decimal] = Field(nullable=True)
    
class BidangRawBase(BaseUUIDModel, BidangBase):
    pass

class BidangFullBase(BaseGeoModel, BidangRawBase):
    pass

class Bidang(BidangFullBase, table=True):
    pemilik:"Pemilik" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    planing:"Planing" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    jenis_surat:"JenisSurat" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    kategori:"Kategori" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin' })
    
    kategori_sub:"KategoriSub" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    kategori_proyek:"KategoriProyek" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    skpt:"Skpt" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    penampung:"Ptsk" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    manager:"Manager" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    sales:"Sales" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    notaris:"Notaris" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    @property
    def pemilik_name(self) -> str:
        if self.pemilik is None:
            return ""
        
        return self.pemilik.name
    
    @property
    def project_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.project.name
    
    @property
    def desa_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.desa.name
    
    @property
    def planing_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.name
    
    @property
    def jenis_surat_name(self) -> str:
        if self.jenis_surat is None:
            return ""
        
        return self.jenis_surat.name
    
    @property
    def kategori_name(self) -> str:
        if self.kategori is None:
            return ""
        
        return self.kategori.name
    
    @property
    def kategori_sub_name(self) -> str:
        if self.kategori_sub is None:
            return ""
        
        return self.kategori_sub.name
    
    @property
    def kategori_proyek_name(self) -> str:
        if self.kategori_proyek is None:
            return ""
        
        return self.kategori_proyek.name
    
    @property
    def ptsk_name(self) -> str:
        if self.skpt is None:
            return ""
        # return getattr(getattr(getattr(self, 'skpt'), 'ptsk'), 'name')
        return self.skpt.ptsk.name
    
    @property
    def no_sk(self) -> str:
        if self.skpt is None:
            return ""
        
        return self.skpt.nomor_sk
    
    @property
    def status_sk(self) -> str:
        if self.skpt is None:
            return ""
        
        return self.skpt.status
    
    @property
    def penampung_name(self) -> str:
        if self.penampung is None:
            return ""
        
        return self.penampung.name
    
    @property
    def manager_name(self) -> str:
        if self.manager is None:
            return ""
        
        return self.manager.name
    
    @property
    def sales_name(self) -> str:
        if self.sales is None:
            return ""
        
        return self.sales.name
    
    @property
    def notaris_name(self) -> str:
        if self.notaris is None:
            return ""
        
        return self.notaris.name


# class BidangBase(SQLModel):
#     id_bidang:str | None = Field(nullable=False, max_length=100)
#     id_bidang_lama:str | None =  Field(nullable=True)
#     nama_pemilik:str | None
#     luas_surat:Decimal
#     alas_hak:str
#     no_peta:str
#     category:CategoryEnum | None = Field(nullable=True)
#     jenis_dokumen: JenisDokumenEnum | None = Field(nullable=True)
#     status:StatusBidangEnum | None = Field(nullable=True)

#     jenis_lahan_id:UUID | None = Field(default=None, foreign_key="jenis_lahan.id", nullable=True)
#     planing_id:UUID | None = Field(default=None, foreign_key="planing.id", nullable=True)
#     skpt_id:UUID | None = Field(default=None, foreign_key="skpt.id", nullable=True)
    
# class BidangExtBase(BidangBase):
#     # tipe_proses:TipeProsesEnum | None = Field(default=None, nullable=True)
#     # tipe_bidang:TipeBidangEnum | None = Field(default=None, nullable=True)
#     pass

# class BidangRawBase(BaseUUIDModel, BidangExtBase):
#     pass

# class BidangFullBase(BaseGeoModel, BidangRawBase):
#     pass

# class Bidang(BidangFullBase, table=True):
#     planing:"Planing" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
#     skpt:"Skpt" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
#     jenis_lahan: "JenisLahan" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

#     @property
#     def planing_name(self)-> str | None:
#         if self.planing is None:
#             return ""
        
#         return self.planing.name or ""
    
#     @property
#     def project_name(self)-> str | None:
#         if self.planing is None:
#             return ""
#         if self.planing.project is None:
#             return ""
        
#         return self.planing.project.name or ""
    
#     @property
#     def desa_name(self)-> str | None:
#         if self.planing is None:
#             return ""
#         if self.planing.desa is None:
#             return ""
        
#         return self.planing.desa.name or ""
    
#     @property
#     def desa_code(self)-> str | None:
#         if self.planing is None:
#             return ""
#         if self.planing.desa is None:
#             return ""
        
#         return self.planing.desa.code or ""
    
#     @property
#     def section_name(self)-> str | None:
#         if self.planing is None:
#             return ""
#         if self.planing.project is None:
#             return ""
#         if self.planing.project.section is None:
#             return ""
        
#         return self.planing.project.section.name or ""
    
#     @property
#     def ptsk_name(self)-> str | None:
#         if self.skpt is None:
#             return ""
#         if self.skpt.ptsk is None:
#             return ""
        
#         return self.skpt.ptsk.name or ""
    
#     @property
#     def nomor_sk(self)-> str | None:
#         if self.skpt is None:
#             return ""
#         return self.skpt.nomor_sk or ""
    
#     @property
#     def jenis_lahan_name(self)-> str:
#         if self.jenis_lahan is None:
#             return ""
#         return self.jenis_lahan.name