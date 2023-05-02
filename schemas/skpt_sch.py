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

@as_form
@optional
class SkptUpdateSch(SkptBase):
    pass