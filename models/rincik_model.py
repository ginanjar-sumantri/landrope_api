from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from enum import Enum
from typing import TYPE_CHECKING
from decimal import Decimal


if TYPE_CHECKING:
    from models.jenis_lahan_model import JenisLahan
    from models.planing_model import Planing
    from models.ptsk_model import Ptsk
    from models.bidang_model import Bidang
    

class CategoryEnum(str, Enum):
    Group_Besar = "Group_Besar"
    Group_Kecil = "Group_Kecil"
    Asset = "Asset"
    Overlap = "Overlap"

class JenisDokumenEnum(str, Enum):
    AJB = "AJB"
    Sertifikat = "Sertifikat"
    Tanah_Garapan = "Tanah_Garapan"
    Akta_Hibah = "Akta_Hibah"
    SPPT = "SPPT"
    Kutipan_Girik = "Kutipan_Girik"

class RincikBase(SQLModel):
    id_rincik:str = Field(nullable=False, max_length=100)
    estimasi_nama_pemilik:str = Field(max_length=250)
    luas:Decimal
    category:CategoryEnum
    alas_hak:str = Field(max_length=100)
    jenis_dokumen: JenisDokumenEnum
    no_peta:str = Field(max_length=100)
    jenis_lahan_id:UUID = Field(default=None, foreign_key="jenis_lahan.id")

    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", nullable=True)

class RincikFullBase(BaseUUIDModel, BaseGeoModel, RincikBase):
    pass

class Rincik(RincikFullBase, table=True):
    jenis_lahan: "JenisLahan" = Relationship(back_populates="rinciks")
    planing:"Planing" = Relationship(back_populates="rinciks")
    ptsk:"Ptsk" = Relationship(back_populates="rinciks")
    bidang:"Bidang" = Relationship(back_populates="rincik")
    

