from models.checklist_kelengkapan_dokumen_model import (ChecklistKelengkapanDokumenHd, 
                                                           ChecklistKelengkapanDokumenHdBase, ChecklistKelengkapanDokumenHdFullBase)
from schemas.checklist_kelengkapan_dokumen_dt_sch import ChecklistKelengkapanDokumenDtSch, ChecklistKelengkapanDokumenDtExtSch, ChecklistKelengkapanDokumenDtBayarSch
from common.partial import optional
from sqlmodel import Field, SQLModel
from typing import List
from uuid import UUID
from pydantic import BaseModel
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum


class ChecklistKelengkapanDokumenHdCreateSch(ChecklistKelengkapanDokumenHdBase):
    pass

class ChecklistKelengkapanDokumenHdSch(ChecklistKelengkapanDokumenHdFullBase):
    id_bidang:str | None = Field(alias="id_bidang")
    jenis_alashak:str | None = Field(alias="jenis_alashak")
    alashak:str | None = Field(alias="alashak")
    bundle_hd_code:str | None = Field(alias="bundle_hd_code")

class ChecklistKelengkapanDokumenHdByIdSch(SQLModel):
    id:UUID | None 
    id_bidang:str | None 
    jenis_alashak:str | None 
    alashak:str | None 
    bundle_hd_code:str | None
    details:list[ChecklistKelengkapanDokumenDtExtSch]
    detail_bayars:list[ChecklistKelengkapanDokumenDtBayarSch]

@optional
class ChecklistKelengkapanDokumenHdUpdateSch(ChecklistKelengkapanDokumenHdBase):
    pass
