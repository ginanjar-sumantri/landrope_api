from models.kjb_model import KjbDt, KjbDtBase, KjbDtFullBase
from common.partial import optional
from sqlmodel import Field

class KjbDtCreateSch(KjbDtBase):
    pass

class KjbDtSch(KjbDtFullBase):
    kjb_code:str = Field(alias="kjb_code")
    jenis_surat_name:str = Field(alias="jenis_surat_name")
    planing_name:str = Field(alias="planing_name")
    planing_name_by_ttn:str = Field(alias="planing_name_by_ttn")

@optional
class KjbDtUpdateSch(KjbDtBase):
    pass