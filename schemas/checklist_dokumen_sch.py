from models.checklist_dokumen_model import ChecklistDokumen, ChecklistDokumenBase, ChecklistDokumenFullBase
from common.partial import optional
from sqlmodel import Field

class ChecklistDokumenCreateSch(ChecklistDokumenBase):
    pass

class ChecklistDokumenSch(ChecklistDokumenFullBase):
    dokumen_name:str = Field(alias='dokumen_name')

@optional
class ChecklistDokumenUpdateSch(ChecklistDokumenBase):
    pass