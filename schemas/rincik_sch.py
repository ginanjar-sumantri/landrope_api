from models.rincik_model import RincikBase, RincikFullBase, RincikRawBase
from common.partial import optional
from common.as_form import as_form

from sqlmodel import Field

@as_form
class RincikCreateSch(RincikBase):
    pass

class RincikRawSch(RincikRawBase):
    jenis_lahan_name:str | None = Field(alias='jenis_lahan_name')
    planing_name:str | None = Field(alias='planing_name')
    ptsk_name:str | None = Field(alias='ptsk_name')

class RincikSch(RincikFullBase):
    pass

@as_form
@optional
class RincikUpdateSch(RincikBase):
    pass