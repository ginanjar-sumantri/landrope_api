from models.checklist_kelengkapan_dokumen_model import (ChecklistKelengkapanDokumenDt, 
                                                           ChecklistKelengkapanDokumenDtBase, ChecklistKelengkapanDokumenDtFullBase)
from common.partial import optional
from sqlmodel import Field, SQLModel
from typing import List
from uuid import UUID
from pydantic import BaseModel
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum


class ChecklistKelengkapanDokumenDtCreateSch(ChecklistKelengkapanDokumenDtBase):
    pass

class ChecklistKelengkapanDokumenDtDraftSch(SQLModel):
    bundle_dt_id:UUID 
    jenis_bayar:JenisBayarEnum
    dokumen_id:UUID 
    dokumen_name:str
    has_meta_data:bool

class ChecklistKelengkapanDokumenDtBayarSch(SQLModel):
    jenis_bayar:JenisBayarEnum
    fg_exists:bool

class ChecklistKelengkapanDokumenDtSch(ChecklistKelengkapanDokumenDtFullBase):
    dokumen_name:str|None = Field(alias="dokumen_name")
    has_meta_data:bool|None = Field(alias="has_meta_data")

class ChecklistKelengkapanDokumenDtExtSch(ChecklistKelengkapanDokumenDtFullBase):
    has_meta_data:bool | None

@optional
class ChecklistKelengkapanDokumenDtUpdateSch(ChecklistKelengkapanDokumenDtBase):
    pass