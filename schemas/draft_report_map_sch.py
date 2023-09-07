from models.draft_report_map_model import DraftReportMap, DraftReportMapBase, DraftReportMapFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional


class DraftReportMapCreateSch(DraftReportMapBase):
    pass

class DraftReportMapDtCreateSch(SQLModel):
    project_id:Optional[UUID]
    desa_id:Optional[UUID]
    ptsk_id:Optional[UUID]
    bidang_id:Optional[UUID]

class DraftReportMapHdCreateSch(SQLModel):
    report_id:UUID
    details:list[DraftReportMapDtCreateSch] | None

class DraftReportMapSch(DraftReportMapFullBase):
    pass

@optional
class DraftReportMapUpdateSch(DraftReportMapBase):
    pass



