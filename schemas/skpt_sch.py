from models.skpt_model import SkptBase, SkptFullBase, SkptRawBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

@as_form
class SkptCreateSch(SkptBase):
    pass

class SkptRawSch(SkptRawBase):
    ptsk_name:str | None = Field(alias='ptsk_name')
    ptsk_code:str | None = Field(alias='ptsk_code')

class SkptSch(SkptFullBase):
    pass

class SkptExtSch(SkptFullBase):
    ptsk_name:str | None
    ptsk_code:str| None
    status:str| None
    kategori:str| None

@as_form
@optional
class SkptUpdateSch(SkptBase):
    pass