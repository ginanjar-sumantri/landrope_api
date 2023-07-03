from models.tanda_terima_notaris_model import TandaTerimaNotarisHd, TandaTerimaNotarisHdBase, TandaTerimaNotarisHdFullBase
from common.partial import optional
from sqlmodel import Field

class TandaTerimaNotarisHdCreateSch(TandaTerimaNotarisHdBase):
    pass

class TandaTerimaNotarisHdSch(TandaTerimaNotarisHdFullBase):
    alashak:str | None = Field(alias="alashak")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    notaris_name:str | None = Field(alias="notaris_name")
    planing_name:str | None = Field(alias="planing_name")

@optional
class TandaTerimaNotarisHdUpdateSch(TandaTerimaNotarisHdBase):
    pass