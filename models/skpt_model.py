from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from common.enum import StatusSKEnum, KategoriSKEnum
from datetime import date
from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID

if TYPE_CHECKING:
    from models.ptsk_model import Ptsk 
    from models.bidang_model import Bidang
    from models.planing_model import Planing
    from models.gps_model import Gps

class SkptBase(SQLModel):
    status:StatusSKEnum | None = Field(nullable=True)
    kategori:KategoriSKEnum | None = Field(nullable=True)
    # luas:Decimal | None
    nomor_sk:str | None = Field(nullable=True, max_length=200)
    tanggal_tahun_SK:date | None = Field(nullable=True)
    tanggal_jatuh_tempo:date | None = Field(nullable=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")

# class SkptRawBase(BaseUUIDModel, SkptBase):
#     pass

class SkptFullBase(BaseUUIDModel, SkptBase):
    pass

class Skpt(SkptFullBase, table=True):
    skpt_planings:list["SkptDt"] = Relationship(back_populates="skpt", sa_relationship_kwargs={'lazy':'select'})
    ptsk:"Ptsk" = Relationship(back_populates="skpts", sa_relationship_kwargs={'lazy':'select'})
    bidangs: list["Bidang"] = Relationship(back_populates="skpt", sa_relationship_kwargs={'lazy':'select'})

    @property
    def ptsk_name(self)-> str:
        if self.ptsk is None:
            return ""
        return self.ptsk.name
    
    @property
    def ptsk_code(self)-> str:
        if self.ptsk is None:
            return ""
        return self.ptsk.code
    
    @property
    def luas_skpt(self)-> Decimal:
        if len(self.skpt_planings) == 0:
            return 0
        
        return Decimal(sum(i.luas for i in self.skpt_planings))
        
    
class SkptDtBase(SQLModel):
    planing_id:UUID | None = Field(foreign_key="planing.id", nullable=True)
    skpt_id:UUID | None = Field(foreign_key="skpt.id", nullable=True)
    luas:Decimal | None = Field(nullable=True)

class SkptDtRawBase(BaseUUIDModel, SkptDtBase):
    pass

class SkptDtFullBase(BaseGeoModel, SkptDtRawBase):
    pass

class SkptDt(SkptDtFullBase, table=True):
    skpt:"Skpt" = Relationship(back_populates="skpt_planings", sa_relationship_kwargs={'lazy':'selectin'})
    planing:"Planing" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def nomor_sk(self) -> str | None:
        if self.skpt is None:
            return ""
        
        return self.skpt.nomor_sk

    @property
    def project_name(self) -> str:
        if self.planing is None:
            return ""
        if self.planing.project is None:
            return ""
        
        return self.planing.project.name
    
    @property
    def section_name(self) -> str:
        if self.planing is None:
            return ""
        if self.planing.project is None:
            return ""
        if self.planing.project.section is None:
            return ""
        
        return self.planing.project.section.name
    
    @property
    def desa_name(self) -> str:
        if self.planing is None:
            return ""
        if self.planing.desa is None:
            return ""
        
        return self.planing.desa.name
    
    @property
    def desa_code(self) -> str:
        if self.planing is None:
            return ""
        if self.planing.desa is None:
            return ""
        
        return self.planing.desa.code
    
    @property
    def kota(self) -> str | None:
        return getattr(getattr(getattr(self, "planing", None), "desa", None), "kota", None)

    @property
    def kecamatan(self) -> str:
        return getattr(getattr(getattr(self, "planing", None), "desa", None), "kecamatan", None)