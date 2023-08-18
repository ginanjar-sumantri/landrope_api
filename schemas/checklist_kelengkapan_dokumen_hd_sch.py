from models.checklist_kelengkapan_dokumen_model import (ChecklistKelengkapanDokumenHd, 
                                                           ChecklistKelengkapanDokumenHdBase, ChecklistKelengkapanDokumenHdFullBase)
from common.partial import optional
from sqlmodel import Field
from typing import List
from uuid import UUID
from pydantic import BaseModel
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum


class ChecklistKelengkapanDokumenHdCreateSch(ChecklistKelengkapanDokumenHdBase):
    pass

class ChecklistKelengkapanDokumenHdSch(ChecklistKelengkapanDokumenHdFullBase):
    pass

@optional
class ChecklistKelengkapanDokumenHdUpdateSch(ChecklistKelengkapanDokumenHdBase):
    pass