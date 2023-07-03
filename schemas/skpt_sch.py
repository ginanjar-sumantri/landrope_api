from models.skpt_model import SkptBase, SkptFullBase
from models.base_model import BaseGeoModel
from pydantic import BaseModel
from common.partial import optional
from common.as_form import as_form
from common.enum import StatusSKEnum, KategoriSKEnum
from sqlmodel import Field
from decimal import Decimal
from datetime import date
from uuid import UUID

class SkptCreateSch(SkptBase):
    pass

# class SkptRawSch(SkptRawBase):
#     ptsk_name:str | None = Field(alias='ptsk_name')
#     ptsk_code:str | None = Field(alias='ptsk_code')

class SkptSch(SkptFullBase):
    ptsk_name:str | None = Field(alias='ptsk_name')
    ptsk_code:str | None = Field(alias='ptsk_code')

class SkptExtSch(SkptFullBase):
    ptsk_name:str | None
    ptsk_code:str| None
    status:str| None
    kategori:str| None

class SkptShpSch(BaseGeoModel):
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

@optional
class SkptUpdateSch(SkptBase):
    pass