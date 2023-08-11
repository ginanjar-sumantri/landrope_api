from models.draft_model import DraftBase, DraftRawBase, DraftFullBase
from schemas.draft_detail_sch import DraftDetailSch
from common.as_form import as_form
from common.partial import optional
from sqlmodel import Field

@as_form
class DraftCreateSch(DraftBase):
    pass

class DraftRawSch(DraftRawBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

class DraftSch(DraftFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

class DraftForAnalisaSch(DraftFullBase):
    details:list[DraftDetailSch] | None

@as_form
@optional
class DraftUpdateSch(DraftBase):
    pass