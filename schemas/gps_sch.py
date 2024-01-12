from models.base_model import BaseGeoModel
from models.gps_model import GpsBase, GpsRawBase, GpsFullBase, StatusGpsEnum
from schemas.bidang_sch import BidangGpsValidator
from common.as_form import as_form
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal
from datetime import date

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

class GpsShpSch(BaseGeoModel):
    nama:str|None
    alashak:str|None
    luas:Decimal|None
    penunjuk:str|None
    pic:str|None
    group:str|None
    status:StatusGpsEnum|None
    tanggal:date|None
    remark:str|None
    ptsk_name:str|None
    nomor_sk:str|None
    desa_name:str|None
    project_name:str|None

class GpsParamSch(SQLModel):
    desa_ids:list[UUID]|None