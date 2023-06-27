from models.skpt_model import SkptBase, SkptFullBase, SkptRawBase
from models.base_model import BaseGeoModel
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field
from decimal import Decimal
from datetime import date

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

class SkptExportSch(BaseGeoModel):
    code:str | None
    name:str| None
    kategori:str| None
    luas:Decimal
    no_sk:str | None
    status:str | None
    tgl_sk:date
    jatuhtempo:date
    project:str | None
    desa:str | None

@as_form
@optional
class SkptUpdateSch(SkptBase):
    pass