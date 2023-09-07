from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional

class DraftReportMapBase(SQLModel):
    report_id:UUID = Field(nullable=False)
    type:str = Field(max_length=2, nullable=False)
    obj_id:UUID = Field(nullable=False)

class DraftReportMapFullBase(BaseUUIDModel, DraftReportMapBase):
    pass

class DraftReportMap(DraftReportMapFullBase, table=True):
    pass