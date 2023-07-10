from models.kjb_model import KjbDt, KjbDtBase, KjbDtFullBase
from common.partial import optional
from sqlmodel import Field
from typing import List

class KjbDtCreateSch(KjbDtBase):
    pass

class KjbDtSch(KjbDtFullBase):
    kjb_code:str | None = Field(alias="kjb_code")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    desa_name:str | None = Field(alias="planing_name")
    desa_name_by_ttn:str | None = Field(alias="planing_name_by_ttn")
    project_name:str | None = Field(alias="planing_name")
    project_name_by_ttn:str | None = Field(alias="planing_name_by_ttn")
    kategori_penjual:str | None = Field(alias="kategori_penjual")
    done_request_petlok:bool | None = Field(alias="done_request_petlok")
    penjual_tanah:str = Field(alias="penjual_tanah")
    nomor_telepon:List[str] = Field(alias="nomor_telepon")

@optional
class KjbDtUpdateSch(KjbDtBase):
    pass