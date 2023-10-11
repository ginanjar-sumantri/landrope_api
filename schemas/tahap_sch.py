from sqlmodel import Field, SQLModel
from models.tahap_model import TahapBase, TahapFullBase
from schemas.tahap_detail_sch import TahapDetailCreateExtSch, TahapDetailSch, TahapDetailUpdateExtSch, TahapDetailExtSch
from schemas.spk_sch import SpkForTerminSch
from common.partial import optional
from common.as_form import as_form
from typing import Optional
from uuid import UUID


class TahapCreateSch(TahapBase):
    details:list[TahapDetailCreateExtSch]

class TahapSch(TahapFullBase):
    planing_name:Optional[str] = Field(alias="planing_name")
    project_name:Optional[str] = Field(alias="project_name")
    section_name:Optional[str] = Field(alias="section_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    sub_project_name:Optional[str] = Field(alias="sub_project_name")
    sub_project_code:Optional[str] = Field(alias="sub_project_code")
    updated_by_name:Optional[str] = Field(alias="updated_by_name")
    jumlah_bidang:Optional[int] = Field(alias="jumlah_bidang")
    

class TahapByIdSch(TahapFullBase):
    planing_name:Optional[str] = Field(alias="planing_name")
    project_name:Optional[str] = Field(alias="project_name")
    section_name:Optional[str] = Field(alias="section_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    sub_project_name:Optional[str] = Field(alias="sub_project_name")
    sub_project_code:Optional[str] = Field(alias="sub_project_code")
    details:list[TahapDetailSch] | None

class TahapForTerminByIdSch(SQLModel):
    id:UUID
    planing_name:Optional[str]
    project_name:Optional[str]
    desa_name:Optional[str]
    ptsk_name:Optional[str]
    nomor_tahap:Optional[int]
    group:Optional[str]
    spkts:list[SpkForTerminSch] | None

@optional
class TahapUpdateSch(TahapBase):
    details:list[TahapDetailUpdateExtSch]
