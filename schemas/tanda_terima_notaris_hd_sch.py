from models.tanda_terima_notaris_model import TandaTerimaNotarisHd, TandaTerimaNotarisHdBase, TandaTerimaNotarisHdFullBase
from common.partial import optional
from common.enum import StatusPetaLokasiEnum
from sqlmodel import Field
from typing import List

class TandaTerimaNotarisHdCreateSch(TandaTerimaNotarisHdBase):
    pass

class TandaTerimaNotarisHdSch(TandaTerimaNotarisHdFullBase):
    alashak:str | None = Field(alias="alashak")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    notaris_name:str | None = Field(alias="notaris_name")
    desa_name:str | None = Field(alias="desa_name")
    project_name:str | None = Field(alias="project_name")
    done_request_petlok:bool | None = Field(alias="done_request_petlok")
    pemilik_name:str | None = Field(alias="pemilik_name")
    nomor_telepon:List[str] | None = Field(alias="nomor_telepon")

@optional
class TandaTerimaNotarisHdUpdateSch(TandaTerimaNotarisHdBase):
    status_peta_lokasi:StatusPetaLokasiEnum | None