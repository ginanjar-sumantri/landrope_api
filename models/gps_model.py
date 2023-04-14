from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from decimal import Decimal

class GpsBase(SQLModel):
    nama:str|None
    alas_hak:str|None
    luas:Decimal|None
    desa:str|None
    penunjuk:str|None
    pic:str|None
    group:str|None

class GpsRawBase(BaseUUIDModel, GpsBase):
    pass

class GpsFullBase(BaseGeoModel, GpsRawBase):
    pass

class Gps(GpsFullBase, table=True):
    pass