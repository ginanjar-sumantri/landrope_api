from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from common.enum import JenisAlashakEnum
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.bidang_model import Bidang
    from models.project_model import Project
    from models.desa_model import Desa
    from models.bundle_model import BundleHd
    from models import HargaStandard

class PlaningBase(SQLModel):
    project_id: UUID = Field(default=None, foreign_key="project.id")
    desa_id:UUID = Field(default=None, foreign_key="desa.id")
    luas:Decimal
    name:str | None = Field(nullable=True, max_length=100)
    code:str | None = Field(nullable=True, max_length=50)

class PlaningRawBase(BaseUUIDModel, PlaningBase):
    pass

class PlaningFullBase(PlaningRawBase, BaseGeoModel):
    pass

class Planing(PlaningFullBase, table=True):

    project:"Project" = Relationship(back_populates="project_planings", sa_relationship_kwargs={'lazy':'select'})
    desa:"Desa" = Relationship(back_populates="desa_planings", sa_relationship_kwargs={'lazy':'select'})
    bidangs: list["Bidang"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'select'})
    bundlehds: list["BundleHd"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'select'})
    harga_standards: list["HargaStandard"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'select'})
    # kjb_dts: list["KjbDt"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'select'})
    # kjb_dts_by_ttn: list["KjbDt"] = Relationship(back_populates="planing_by_ttn", sa_relationship_kwargs={'lazy':'select'})
    # tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'selectin'})
    

    @property
    def project_name(self)-> str:
        if self.project is None:
            return ""
        return self.project.name
    
    @property
    def desa_name(self)-> str:
        if self.desa is None:
            return ""
        return self.desa.name
    
    @property
    def kota(self)-> str|None:
        return getattr(getattr(self, "desa", None), "kota", None)
    
    @property
    def kecamatan(self)-> str|None:
        return getattr(getattr(self, "desa", None), "kecamatan", None)
    
    @property
    def desa_name(self)-> str:
        if self.desa is None:
            return ""
        return self.desa.name
    
    @property
    def section_name(self)-> str:
        if self.project is None:
            return ""
        if self.project.section is None:
            return ""
        return self.project.section.name
    
    @property
    def sub_project_exists(self)-> bool | None:
        return getattr(getattr(self, 'project', False), 'sub_project_exists', False)
    
    @property
    def harga_standard_girik(self) -> Decimal | None:
        harga = 0
        master_harga_standard_girik = next((harga_standard.harga for harga_standard in self.harga_standards if harga_standard.jenis_alashak == JenisAlashakEnum.Girik), None) 
        if master_harga_standard_girik:
            return master_harga_standard_girik
        
        return harga
    
    @property
    def harga_standard_sertifikat(self) -> Decimal | None:
        harga = 0
        master_harga_standard_sertifikat = next((harga_standard.harga for harga_standard in self.harga_standards if harga_standard.jenis_alashak == JenisAlashakEnum.Sertifikat), None) 
        if master_harga_standard_sertifikat:
            return master_harga_standard_sertifikat
        
        return harga