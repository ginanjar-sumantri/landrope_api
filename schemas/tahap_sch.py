from sqlmodel import Field, SQLModel
from models.tahap_model import TahapBase, TahapFullBase
from schemas.tahap_detail_sch import TahapDetailCreateExtSch, TahapDetailSch, TahapDetailUpdateExtSch, TahapDetailExtSch
from schemas.spk_sch import SpkInTerminSch
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
    dp_count:Optional[int] = Field(alias="dp_count")
    lunas_count:Optional[int] = Field(alias="lunas_count")
    updated_by_name:Optional[str] = Field(alias="updated_by_name")
    jumlah_bidang:Optional[int] = Field(alias="jumlah_bidang")

class TahapSrcSch(TahapFullBase):
    project_name:Optional[str]

class TahapByIdSch(TahapFullBase):
    planing_name:Optional[str] = Field(alias="planing_name")
    project_name:Optional[str] = Field(alias="project_name")
    project_id:Optional[UUID] = Field(alias="project_id")
    section_name:Optional[str] = Field(alias="section_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    sub_project_name:Optional[str] = Field(alias="sub_project_name")
    sub_project_code:Optional[str] = Field(alias="sub_project_code")
    has_memo_active: bool | None
    details:list[TahapDetailSch] | None

class TahapForTerminByIdSch(SQLModel):
    id:UUID
    planing_name:Optional[str]
    project_name:Optional[str]
    desa_name:Optional[str]
    ptsk_name:Optional[str]
    nomor_tahap:Optional[int]
    group:Optional[str]
    spkts:list[SpkInTerminSch] | None

@optional
class TahapUpdateSch(TahapBase):
    details:list[TahapDetailUpdateExtSch]

class TahapFilterJson(SQLModel):
    nomor_tahap: str | None
    project: str | None
    desa: str | None
    ptsk: str | None
    group: str | None