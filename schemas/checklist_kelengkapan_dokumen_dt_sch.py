from models.checklist_kelengkapan_dokumen_model import (ChecklistKelengkapanDokumenDt, 
                                                           ChecklistKelengkapanDokumenDtBase, ChecklistKelengkapanDokumenDtFullBase)
from common.partial import optional
from sqlmodel import Field
from typing import List
from uuid import UUID
from pydantic import BaseModel
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum


class ChecklistKelengkapanDokumenDtCreateSch(ChecklistKelengkapanDokumenDtBase):
    pass

class ChecklistKelengkapanDokumenDtSch(ChecklistKelengkapanDokumenDtFullBase):
    pass

@optional
class ChecklistKelengkapanDokumenDtUpdateSch(ChecklistKelengkapanDokumenDtBase):
    pass