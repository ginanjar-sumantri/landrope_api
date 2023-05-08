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
    from models.skpt_model import Skpt
    from models.rincik_model import Rincik
    from models.jenis_lahan_model import JenisLahan

class StatusEnum(str, Enum):
    Bebas = "Bebas"
    Belum_Bebas = "Belum_Bebas"
    Batal = "Batal"

class TipeProses(str, Enum):
    Standard = "Standard"
    Bintang = "Bintang"

class TipeBidang(str, Enum):
    Rincik = "Rincik"
    Bidang = "Bidang"
    Overlap = "Overlap"

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
    

class BidangBase(SQLModel):
    id_bidang:str | None = Field(nullable=False, max_length=100)
    nama_pemilik:str
    luas_surat:Decimal
    alas_hak:str
    no_peta:str
    category:CategoryEnum | None = Field(nullable=True)
    jenis_dokumen: JenisDokumenEnum | None = Field(nullable=True)
    status:StatusEnum | None = Field(nullable=True)

    jenis_lahan_id:UUID = Field(default=None, foreign_key="jenis_lahan.id", nullable=True)
    planing_id:UUID = Field(default=None, foreign_key="planing.id", nullable=True)
    skpt_id:UUID = Field(default=None, foreign_key="skpt.id", nullable=True)
    # ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", nullable=True)
    
class BidangExtBase(BidangBase):
    tipe_proses:TipeProses
    tipe_proses:TipeBidang
    # rincik_id:UUID = Field(default=None, foreign_key="rincik.id", nullable=True)

class BidangRawBase(BaseUUIDModel, BidangExtBase):
    pass

class BidangFullBase(BaseGeoModel, BidangRawBase):
    pass

class Bidang(BidangFullBase, table=True):

    planing:"Planing" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    # ptsk:"Ptsk" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    skpt:"Skpt" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})
    # rincik:"Rincik" = Relationship(back_populates="bidang", sa_relationship_kwargs={'lazy':'selectin'})
    # overlaps:list["Bidangoverlap"] = Relationship(back_populates="bidangs", link_model=MappingBidangOverlap, sa_relationship_kwargs={'lazy':'selectin'})
    jenis_lahan: "JenisLahan" = Relationship(back_populates="bidangs", sa_relationship_kwargs={'lazy':'selectin'})

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
    
    @property
    def id_rincik(self)-> str:
        return self.rincik.id_rincik
    
    @property
    def jenis_lahan_name(self)-> str:
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
    

