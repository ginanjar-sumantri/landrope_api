from sqlmodel import Field
from models.tahap_model import TahapBase, TahapFullBase
from schemas.tahap_detail_sch import TahapDetailCreateExtSch, TahapDetailSch, TahapDetailUpdateExtSch
from common.partial import optional
from common.as_form import as_form
from typing import Optional


class TahapCreateSch(TahapBase):
    bidangs:list[TahapDetailCreateExtSch]

class TahapSch(TahapFullBase):
    planing_name:Optional[str] = Field(alias="planing_name")
    project_name:Optional[str] = Field(alias="project_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    penampung_name:Optional[str] = Field(alias="penampung_name")
    updated_by_name:Optional[str] = Field(alias="updated_by_name")
    jumlah_bidang:Optional[int] = Field(alias="jumlah_bidang")

class TahapByIdSch(TahapFullBase):
    planing_name:Optional[str] = Field(alias="planing_name")
    project_name:Optional[str] = Field(alias="project_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    penampung_name:Optional[str] = Field(alias="penampung_name")
    details:list[TahapDetailSch]

@optional
class TahapUpdateSch(TahapBase):
    details:list[TahapDetailUpdateExtSch]