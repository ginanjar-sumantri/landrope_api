from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from enum import Enum
from typing import TYPE_CHECKING
from decimal import Decimal


if TYPE_CHECKING:
    from models.jenis_lahan_model import JenisLahan
    from models.planing_model import Planing
    from models.skpt_model import Skpt
    from models.bidang_model import Bidang
    

class CategoryEnum(str, Enum):
    Group_Besar = "Group_Besar"
    Group_Kecil = "Group_Kecil"
    Asset = "Asset"
    Overlap = "Overlap"
    Default = "Unknown"

    @classmethod
    def _missing_(cls, value):
         return cls.Default 

class JenisDokumenEnum(str, Enum):
    AJB = "AJB"
    Sertifikat = "Sertifikat"
    Tanah_Garapan = "Tanah_Garapan"
    Akta_Hibah = "Akta_Hibah"
    SPPT = "SPPT"
    Kutipan_Girik = "Kutipan_Girik"
    Default = "Unknown"

    @classmethod
    def _missing_(cls, value):
         return cls.Default 

class RincikBase(SQLModel):
    id_rincik:str = Field(nullable=False, max_length=100)
    estimasi_nama_pemilik:str = Field(max_length=250)
    luas:Decimal
    category:CategoryEnum | None = Field(nullable=True)
    alas_hak:str = Field(max_length=100)
    jenis_dokumen: JenisDokumenEnum | None = Field(nullable=True)
    no_peta:str = Field(max_length=100)
    jenis_lahan_id:UUID = Field(default=None, foreign_key="jenis_lahan.id", nullable=True)

    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    skpt_id:UUID = Field(default=None, foreign_key="skpt.id", nullable=True)

class RincikRawBase(BaseUUIDModel, RincikBase):
    pass

class RincikFullBase(BaseGeoModel, RincikRawBase):
    pass

class Rincik(RincikFullBase, table=True):
    jenis_lahan: "JenisLahan" = Relationship(back_populates="rinciks", sa_relationship_kwargs={'lazy':'selectin'})
    planing:"Planing" = Relationship(back_populates="rinciks", sa_relationship_kwargs={'lazy':'selectin'})
    skpt:"Skpt" = Relationship(back_populates="rinciks", sa_relationship_kwargs={'lazy':'selectin'})
    

    @property
    def jenis_lahan_name(self)-> str:
            return self.jenis_lahan.name
    
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
        return self.skpt.ptsk.name
    
    @property
    def nomor_sk(self)-> str:
        return self.skpt.nomor_sk