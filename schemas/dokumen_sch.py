from models.dokumen_model import Dokumen, DokumenBase, DokumenFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class DokumenCreateSch(DokumenBase):
    pass

class DokumenSch(DokumenFullBase):
    pass

@as_form
class RiwayatSch(SQLModel):
    tanggal:datetime | None
    key_value:str | None
    file_path:str | None
    is_default:bool | None
    meta_data:dict | None = Field(alias="meta_data")

@optional
class DokumenUpdateSch(DokumenBase):
    pass