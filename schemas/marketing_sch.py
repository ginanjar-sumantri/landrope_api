from models.marketing_model import ManagerBase, ManagerFullBase, SalesBase, SalesFullBase
from common.partial import optional
from sqlmodel import SQLModel
from uuid import UUID

class ManagerCreateSch(ManagerBase):
    pass

class ManagerSch(ManagerFullBase):
    pass

class ManagerSrcSch(SQLModel):
    id:UUID | None
    name:str | None

@optional
class ManagerUpdateSch(ManagerBase):
    pass



class SalesCreateSch(SalesBase):
    pass

class SalesSrcSch(SQLModel):
    id:UUID | None
    name:str | None

class SalesSch(SalesFullBase):
    pass

@optional
class SalesUpdateSch(SalesBase):
    pass