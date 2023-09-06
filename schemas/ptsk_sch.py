from models.ptsk_model import PtskBase, PtskFullBase, PtskRawBase
from common.partial import optional
from sqlmodel import SQLModel
from uuid import UUID

class PtskCreateSch(PtskBase):
    pass

class PtskRawSch(PtskRawBase):
    pass

class PtskSch(PtskFullBase):
    pass

@optional
class PtskUpdateSch(PtskBase):
    pass

class PtskForTreeReportSch(SQLModel):
    id:UUID|None
    name:str|None
    desa_id:UUID|None
    desa_name:str|None
    project_id:UUID|None
    project_name:str|None