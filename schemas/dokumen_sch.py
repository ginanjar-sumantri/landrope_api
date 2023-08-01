from models.dokumen_model import Dokumen, DokumenBase, DokumenFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field

class DokumenCreateSch(DokumenBase):
    pass

class DokumenSch(DokumenFullBase):
    pass

class RiwayatSch(SQLModel):
    tanggal:str
    key_value:str
    file_path:str
    is_default:bool
    meta_data:str = Field(alias="metadata")

@optional
class DokumenUpdateSch(DokumenBase):
    pass