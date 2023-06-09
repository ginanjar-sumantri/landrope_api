from models.kjb_model import KjbRekening, KjbRekeningBase, KjbRekeningFullBase
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID

class KjbRekeningCreateSch(KjbRekeningBase):
    pass

class KjbRekeningCreateExtSch(BaseModel):
    rekenings:List[UUID]

class KjbRekeningSch(KjbRekeningFullBase):
    pass

@optional
class KjbRekeningUpdateSch(KjbRekeningBase):
    pass