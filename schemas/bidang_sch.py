from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

@as_form
class BidangCreateSch(BidangBase):
    pass

class BidangRawSch(BidangRawBase):
    planing_name:str|None = Field(alias='planing_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    section_name:str|None = Field(alias='section_name')
    ptsk_name:str|None = Field(alias='ptsk_name')
    id_rincik:str|None = Field(alias='id_rincik')
    


class BidangSch(BidangFullBase):
    pass

@optional
class BidangUpdateSch(BidangBase):
    pass