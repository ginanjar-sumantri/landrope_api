from models.kjb_model import KjbPenjual, KjbPenjualBase, KjbPenjualFullBase
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID
from common.enum import JenisBayarEnum
from decimal import Decimal
from sqlmodel import Field, SQLModel

class KjbPenjualCreateSch(KjbPenjualBase):
    pass

class KjbPenjualCreateExtSch(SQLModel):
    id:UUID|None
    pemilik_id:UUID|None

class KjbPenjualSch(KjbPenjualFullBase):
    penjual_tanah:str = Field(alias="penjual_tanah")

@optional
class KjbPenjualUpdateSch(KjbPenjualFullBase):
    pass