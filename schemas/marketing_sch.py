from models.marketing_model import ManagerBase, ManagerFullBase, SalesBase, SalesFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
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
    manager_name:str|None = Field(alias="manager_name")

@optional
class SalesUpdateSch(SalesBase):
    pass