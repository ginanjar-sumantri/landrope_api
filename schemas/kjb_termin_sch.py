from models.kjb_model import KjbTermin, KjbTerminBase, KjbTerminFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from typing import List
from uuid import UUID
from common.enum import JenisBayarEnum
from decimal import Decimal

class KjbTerminCreateSch(KjbTerminBase):
    nilai_lunas:Decimal|None = Field(default=0)

class KjbTerminCreateExtSch(SQLModel):
    id:UUID|None
    jenis_bayar:JenisBayarEnum | None
    nilai:Decimal | None

class KjbTerminSch(KjbTerminFullBase):
    has_been_spk:bool|None

class KjbTerminInSpkSch(KjbTerminFullBase):
    spk_id:UUID|None
    spk_code:str|None

@optional
class KjbTerminUpdateSch(KjbTerminFullBase):
    pass