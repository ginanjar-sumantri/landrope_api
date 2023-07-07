from models.tanda_terima_notaris_model import TandaTerimaNotarisHd, TandaTerimaNotarisHdBase, TandaTerimaNotarisHdFullBase
from common.partial import optional
from common.enum import StatusPetaLokasiEnum
from sqlmodel import Field

class TandaTerimaNotarisHdCreateSch(TandaTerimaNotarisHdBase):
    status_peta_lokasi:StatusPetaLokasiEnum | None

class TandaTerimaNotarisHdSch(TandaTerimaNotarisHdFullBase):
    alashak:str | None = Field(alias="alashak")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    notaris_name:str | None = Field(alias="notaris_name")
    planing_name:str | None = Field(alias="planing_name")

@optional
class TandaTerimaNotarisHdUpdateSch(TandaTerimaNotarisHdBase):
    pass