from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

@as_form
class BidangCreateSch(BidangBase):
    pass

class BidangRawSch(BidangRawBase):
    planing_name:str = Field(alias='planing_name')
    project_name:str = Field(alias='project_name')
    desa_name:str = Field(alias='desa_name')
    section_name:str = Field(alias='section_name')
    desa_name:str = Field(alias='desa_name')
    project_name:str = Field(alias='project_name')
    desa_name:str = Field(alias='desa_name')


class BidangSch(BidangFullBase):
    pass

@optional
class BidangUpdateSch(BidangBase):
    pass