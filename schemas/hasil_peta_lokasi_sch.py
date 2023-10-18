from models.hasil_peta_lokasi_model import HasilPetaLokasiBase, HasilPetaLokasiFullBase
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailCreateExtSch, HasilPetaLokasiDetailSch
from common.partial import optional
from common.as_form import as_form
from common.enum import StatusHasilPetaLokasiEnum, HasilAnalisaPetaLokasiEnum
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional

@as_form
class HasilPetaLokasiCreateSch(HasilPetaLokasiBase):
    pass

class HasilPetaLokasiCreateExtSch(HasilPetaLokasiBase):
    draft_id:Optional[UUID]
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
    project_id:UUID|None = Field(alias="project_id")
    project_name:str|None = Field(alias="project_name")
    sub_project_name:str|None = Field(alias="sub_project_name")
    sub_project_exists:bool|None = Field(alias="sub_project_exists")
    desa_name:str|None = Field(alias="desa_name")
    ptsk_name:str|None = Field(alias="ptsk_name")
    no_sk:str|None = Field(alias="no_sk")
    status_sk:str|None = Field(alias="status_sk")
    pemilik_name:str|None = Field(alias="pemilik_name")
    updated_by_name:str|None = Field(alias="updated_by_name")

    details:list[HasilPetaLokasiDetailSch]

@optional
class HasilPetaLokasiUpdateSch(HasilPetaLokasiBase):
    pass

@optional
class HasilPetaLokasiUpdateExtSch(HasilPetaLokasiBase):
    draft_id:Optional[UUID]
    hasilpetalokasidetails:list[HasilPetaLokasiDetailCreateExtSch]

class HasilPetaLokasiTaskUpdateBidang(SQLModel):
    bidang_id:str
    hasil_peta_lokasi_id:str
    kjb_dt_id:str
    draft_id:str

class HasilPetaLokasiTaskUpdateKulitBintang(SQLModel):
    hasil_peta_lokasi_id:str
    draft_id:str

class HasilPetaLokasiUpdateCloud(SQLModel):
    id:UUID
    bidang_id:UUID
    status_hasil_peta_lokasi:Optional[StatusHasilPetaLokasiEnum]
    hasil_analisa_peta_lokasi:Optional[HasilAnalisaPetaLokasiEnum]
    pemilik_id:Optional[UUID]
    luas_surat:Optional[Decimal]
    planing_id:Optional[UUID]
    sub_project_id:Optional[UUID]
    skpt_id:Optional[UUID]
    luas_ukur:Optional[Decimal]
    luas_nett:Optional[Decimal]
    luas_clear:Optional[Decimal]
    luas_gu_pt:Optional[Decimal]
    luas_gu_perorangan:Optional[Decimal]
    updated_by_id:Optional[UUID]
    no_peta:Optional[str]
