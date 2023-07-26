from models.master_model import HargaStandard, HargaStandardBase
from common.partial import optional
from sqlmodel import Field

class HargaStandardCreateSch(HargaStandardBase):
    pass

class HargaStandardSch(HargaStandard):
    planing_name:str|None = Field(alias="planing_name")

@optional
class HargaStandardUpdateSch(HargaStandardBase):
    pass