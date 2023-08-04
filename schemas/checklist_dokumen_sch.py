from models.checklist_dokumen_model import ChecklistDokumen, ChecklistDokumenBase, ChecklistDokumenFullBase
from common.partial import optional
from sqlmodel import Field
from typing import List
from uuid import UUID
from pydantic import BaseModel
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum


class ChecklistDokumenCreateSch(ChecklistDokumenBase):
    dokumens:List[UUID]

class ChecklistDokumenBulkCreateSch(BaseModel):
    jenis_alashak:JenisAlashakEnum
    kategori_penjual:KategoriPenjualEnum
    jenis_bayar:JenisBayarEnum
    dokumens:List[UUID]

class ChecklistDokumenSch(ChecklistDokumenFullBase):
    dokumen_name:str = Field(alias='dokumen_name')
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class ChecklistDokumenUpdateSch(ChecklistDokumenBase):
    pass