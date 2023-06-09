from models.kjb_model import KjbCaraBayar, KjbCaraBayarBase, KjbCaraBayarFullBase
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID
from common.enum import JenisBayarEnum
from decimal import Decimal

class KjbCaraBayarCreateSch(KjbCaraBayarBase):
    pass

class KjbCaraBayarCreateExtSch(BaseModel):
    jenis_bayar:JenisBayarEnum
    nilai:Decimal

class KjbCaraBayarSch(KjbCaraBayarFullBase):
    pass

@optional
class KjbCaraBayarUpdateSch(KjbCaraBayarFullBase):
    pass