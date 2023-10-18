from models.kjb_model import KjbBebanBiaya, KjbBebanBiayaBase, KjbBebanBiayaFullBase
from common.partial import optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel
from typing import List
from uuid import UUID

class KjbBebanBiayaCreateSch(KjbBebanBiayaBase):
    pass

class KjbBebanBiayaCreateExSch(BaseModel):
    beban_biaya_id:str | None
    beban_biaya_name:str | None
    beban_pembeli:bool
    kjb_hd_id:str | None

class KjbBebanBiayaCreateExtSch(BaseModel):
    beban_biaya_id:str | None
    beban_biaya_name:str | None
    beban_pembeli:bool

class KjbBebanBiayaSch(KjbBebanBiayaFullBase):
    beban_biaya_name:str | None = Field(alias="beban_biaya_name")
    is_tax:bool |None = Field(alias="is_tax")

@optional
class KjbBebanBiayaUpdateSch(KjbBebanBiayaBase):
    pass