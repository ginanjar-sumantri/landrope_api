from models.hasil_peta_lokasi_model import HasilPetaLokasiBase, HasilPetaLokasiFullBase
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailCreateExtSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

@as_form
class HasilPetaLokasiCreateSch(HasilPetaLokasiBase):
    pass


class HasilPetaLokasiCreateExtSch(HasilPetaLokasiBase):
    hasilpetalokasidetails:list[HasilPetaLokasiDetailCreateExtSch]

class HasilPetaLokasiSch(HasilPetaLokasiFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak_bidang:str|None = Field(alias="alashak_bidang")
    alashak_kjb_dt:str|None = Field(alias="alashak_kjb_dt")
    project_name:str|None = Field(alias="project_name")
    desa_name:str|None = Field(alias="desa_name")
    updated_by_name:str|None = Field(alias="updated_by_name")

class HasilPetaLokasiByIdSch(HasilPetaLokasiFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak_bidang:str|None = Field(alias="alashak_bidang")
    alashak_kjb_dt:str|None = Field(alias="alashak_kjb_dt")
    planing_name:str|None = Field(alias="planing_name")
    project_name:str|None = Field(alias="project_name")
    desa_name:str|None = Field(alias="desa_name")
    ptsk_name:str|None = Field(alias="ptsk_name")
    no_sk:str|None = Field(alias="no_sk")
    status_sk:str|None = Field(alias="status_sk")
    pemilik_name:str|None = Field(alias="pemilik_name")
    updated_by_name:str|None = Field(alias="updated_by_name")

@as_form
@optional
class HasilPetaLokasiUpdateSch(HasilPetaLokasiBase):
    pass