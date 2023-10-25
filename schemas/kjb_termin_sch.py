from models.kjb_model import KjbTermin, KjbTerminBase, KjbTerminFullBase
from common.partial import optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import List
from uuid import UUID
from common.enum import JenisBayarEnum
from decimal import Decimal

class KjbTerminCreateSch(KjbTerminBase):
    pass

class KjbTerminCreateExtSch(BaseModel):
    jenis_bayar:JenisBayarEnum
    nilai:Decimal

class KjbTerminSch(KjbTerminFullBase):
    pass

class KjbTerminInSpkSch(KjbTerminFullBase):
    spk_id:UUID|None
    spk_code:str|None

@optional
class KjbTerminUpdateSch(KjbTerminFullBase):
    pass