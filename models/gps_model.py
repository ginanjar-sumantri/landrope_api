from sqlmodel import SQLModel
from models.base_model import BaseUUIDModel, BaseGeoModel
from decimal import Decimal
from enum import Enum

class StatusGpsEnum(str, Enum):
    Clear = "Clear"
    Overlap = "Overlap"
    NotSet = "Not_Set"

class GpsBase(SQLModel):
    nama:str|None
    alas_hak:str|None
    luas:Decimal|None
    desa:str|None
    penunjuk:str|None
    pic:str|None
    group:str|None
    status:StatusGpsEnum|None

class GpsRawBase(BaseUUIDModel, GpsBase):
    pass

class GpsFullBase(BaseGeoModel, GpsRawBase):
    pass

class Gps(GpsFullBase, table=True):
    pass