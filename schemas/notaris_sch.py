from models.notaris_model import NotarisBase, NotarisFullBase
from common.partial import optional
from uuid import UUID
from sqlmodel import SQLModel

class NotarisCreateSch(NotarisBase):
    pass

class NotarisSch(NotarisFullBase):
    pass

class NotarisSrcSch(SQLModel):
    id:UUID | None
    name:str | None

@optional
class NotarisUpdateSch(NotarisBase):
    pass