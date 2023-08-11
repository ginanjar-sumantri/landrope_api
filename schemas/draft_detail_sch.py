from models.draft_model import DraftDetailBase, DraftDetailRawBase, DraftDetailFullBase
from common.as_form import as_form
from common.partial import optional
from sqlmodel import Field

@as_form
class DraftDetailCreateSch(DraftDetailBase):
    pass

class DraftDetailRawSch(DraftDetailRawBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

class DraftDetailSch(DraftDetailFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@as_form
@optional
class DraftDetailUpdateSch(DraftDetailBase):
    pass