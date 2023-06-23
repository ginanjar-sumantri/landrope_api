from models.kjb_model import KjbBebanBiaya, KjbBebanBiayaBase, KjbBebanBiayaFullBase
from common.partial import optional
from pydantic import BaseModel
from sqlmodel import Field
from typing import List
from uuid import UUID

class KjbBebanBiayaCreateSch(KjbBebanBiayaBase):
    pass

class KjbBebanBiayaCreateExtSch(BaseModel):
    beban_biaya_id:str | None
    beban_biaya_name:str | None
    beban_pembeli:bool

class KjbBebanBiayaSch(KjbBebanBiayaFullBase):
    beban_biaya_name:str | None = Field(alias="beban_biaya_name")

@optional
class KjbBebanBiayaUpdateSch(KjbBebanBiayaBase):
    pass