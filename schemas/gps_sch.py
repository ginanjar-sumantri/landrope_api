from models.gps_model import GpsBase, GpsRawBase, GpsFullBase
from common.as_form import as_form
from common.partial import optional
from sqlmodel import Field

@as_form
class GpsCreateSch(GpsBase):
    pass

class GpsRawSch(GpsRawBase):
    ptsk_name:str|None = Field(alias='ptsk_name')
    nomor_sk:str|None = Field(alias='nomor_sk')

class GpsSch(GpsFullBase):
    pass

@as_form
@optional
class GpsUpdateSch(GpsBase):
    pass