from models.kjb_model import KjbBebanBiaya, KjbBebanBiayaBase, KjbBebanBiayaFullBase
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID

class KjbBebanBiayaCreateSch(KjbBebanBiayaBase):
    pass

class KjbBebanBiayaCreateExtSch(BaseModel):
    beban_id:UUID | None
    beban_name:str | None
    beban_pembeli:bool

class KjbBebanBiayaSch(KjbBebanBiayaFullBase):
    pass

@optional
class KjbBebanBiayaUpdateSch(KjbBebanBiayaBase):
    pass