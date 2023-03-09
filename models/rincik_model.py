from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from models.jenis_lahan_model import JenisLahan
    from models.ptsk_model import PTSK
    from models.mapping_model import Mapping_Planing_PTSK_Desa_Rincik, Mapping_Planing_PTSK_Desa_Rincik_Bidang

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

class RincikBase(BaseGeoModel):
    id_rincik:str = Field(nullable=False, max_length=100)
    estimasi_nama_pemilik:str = Field(max_length=250)
    luas:int
    category:CategoryEnum
    alas_hak:str = Field(max_length=100)
    jenis_dokumen: JenisDokumenEnum
    no_peta:str = Field(max_length=100)
    jenis_lahan_id:UUID = Field(default=None, foreign_key="") 
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")

class RincikFullBase(BaseUUIDModel, RincikBase):
    pass

class Rincik(RincikFullBase, table=True):
    jenis_lahan: "JenisLahan" = Relationship(back_populates="rincik")
    planing_ptsk_desa_rincik: "Mapping_Planing_PTSK_Desa_Rincik" = Relationship(back_populates="rinciks")
    planing_ptsk_desa_rincik_bidang: "Mapping_Planing_PTSK_Desa_Rincik_Bidang" = Relationship(back_populates="rinciks")
