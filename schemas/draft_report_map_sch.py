from models.draft_report_map_model import DraftReportMap, DraftReportMapBase, DraftReportMapFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel
from uuid import UUID
from typing import TYPE_CHECKING


class DraftReportMapCreateSch(DraftReportMapBase):
    pass

class DraftReportMapDtCreateSch(SQLModel):
    type:str
    obj_id:UUID

class DraftReportMapHdCreateSch(SQLModel):
    report_id:UUID
    details:list[DraftReportMapDtCreateSch] | None

class DraftReportMapSch(DraftReportMapFullBase):
    pass

@optional
class DraftReportMapUpdateSch(DraftReportMapBase):
    pass

class DraftReportMapDtUpdateSch(SQLModel):
    id:UUID | None
    type:str
    obj_id:UUID 

@optional
class DraftReportMapHdUpdateSch(SQLModel):
    details:list[DraftReportMapDtUpdateSch] | None


