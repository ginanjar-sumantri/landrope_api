from models.kjb_model import KjbDt, KjbDtBase, KjbDtFullBase
from common.partial import optional
from sqlmodel import Field

class KjbDtCreateSch(KjbDtBase):
    pass

class KjbDtSch(KjbDtFullBase):
    kjb_code:str | None = Field(alias="kjb_code")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    planing_name:str | None = Field(alias="planing_name")
    planing_name_by_ttn:str | None = Field(alias="planing_name_by_ttn")

@optional
class KjbDtUpdateSch(KjbDtBase):
    pass