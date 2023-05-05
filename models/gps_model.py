from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from decimal import Decimal
from enum import Enum
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.skpt_model import Skpt

class StatusGpsEnum(str, Enum):
    Masuk_SK_Clear = "Masuk_SK_Clear"
    Masuk_SK_Overlap = "Masuk_SK_Overlap"
    Tidak_Masuk_SK_Clear = "Tidak_Masuk_SK_Clear"
    Tidak_Masuk_SK_Overlap = "Tidak_Masuk_SK_Overlap"

class GpsBase(SQLModel):
    nama:str|None
    alas_hak:str|None
    luas:Decimal|None
    desa:str|None
    penunjuk:str|None
    pic:str|None
    group:str|None
    status:StatusGpsEnum|None
    skpt_id:UUID|None = Field(default=None, nullable=True, foreign_key="skpt.id")

class GpsRawBase(BaseUUIDModel, GpsBase):
    pass

class GpsFullBase(BaseGeoModel, GpsRawBase):
    pass

class Gps(GpsFullBase, table=True):
    skpt:"Skpt"=Relationship(back_populates="gpsts", sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def ptsk_name(self)-> str:
        return self.skpt.ptsk.name
    
    @property
    def nomor_sk(self)-> str:
        return self.skpt.nomor_sk