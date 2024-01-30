from models.master_model import KeteranganReqPetlokBase, KeteranganReqPetlokFullBase
from common.partial import optional
from uuid import UUID
from sqlmodel import SQLModel

class KeteranganReqPetlokCreateSch(KeteranganReqPetlokBase):
    pass

class KeteranganReqPetlokSch(KeteranganReqPetlokFullBase):
    pass

class KeteranganReqPetlokSrcSch(SQLModel):
    id:UUID | None
    name:str | None

@optional
class KeteranganReqPetlokUpdateSch(KeteranganReqPetlokBase):
    pass