from models.gps_model import GpsBase, GpsRawBase, GpsFullBase
from schemas.bidang_sch import BidangGpsValidator
from common.as_form import as_form
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID

class GpsCreateSch(GpsBase):
    draft_id:UUID|None

class GpsRawSch(GpsRawBase):
    ptsk_name:str|None = Field(alias='ptsk_name')
    nomor_sk:str|None = Field(alias='nomor_sk')
    updated_by_name:str|None = Field(alias="updated_by_name")
    desa_name:str|None
    planing_name:str|None
    ptsk_id:UUID|None

class GpsSch(GpsFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class GpsUpdateSch(GpsBase):
    draft_id:UUID|None

class GpsValidator(SQLModel):
    gps:list[GpsRawSch]|None
    bidang:list[BidangGpsValidator]|None