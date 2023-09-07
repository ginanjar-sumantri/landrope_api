from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional

class DraftReportMapBase(SQLModel):
    report_id:UUID = Field(nullable=False)
    project_id:Optional[UUID] = Field(nullable=True)
    desa_id:Optional[UUID] = Field(nullable=True)
    ptsk_id:Optional[UUID] = Field(nullable=True)
    bidang_id:Optional[UUID] = Field(nullable=True)

class DraftReportMapFullBase(BaseUUIDModel, DraftReportMapBase):
    pass

class DraftReportMap(DraftReportMapFullBase, table=True):
    pass