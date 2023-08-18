from models.checklist_kelengkapan_dokumen_model import (ChecklistKelengkapanDokumen, 
                                                           ChecklistKelengkapanDokumenBase, ChecklistKelengkapanDokumenFullBase)
from common.partial import optional
from sqlmodel import Field
from typing import List
from uuid import UUID
from pydantic import BaseModel
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum


class ChecklistKelengkapanDokumenCreateSch(ChecklistKelengkapanDokumenBase):
    dokumens:List[UUID]

class ChecklistKelengkapanDokumenBulkCreateSch(BaseModel):
    jenis_alashak:JenisAlashakEnum
    kategori_penjual:KategoriPenjualEnum
    jenis_bayar:JenisBayarEnum
    dokumens:List[UUID]

class ChecklistKelengkapanDokumenSch(ChecklistKelengkapanDokumenFullBase):
    dokumen_name:str = Field(alias='dokumen_name')
    kategori_dokumen_name:str|None = Field(alias="kategori_dokumen_name")
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class ChecklistKelengkapanDokumenUpdateSch(ChecklistKelengkapanDokumenBase):
    pass