from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import TaskStatusEnum
from typing import TYPE_CHECKING
from datetime import date


if TYPE_CHECKING:
    from models.worker_model import Worker

class ExportLogBase(SQLModel):
    name: str | None = Field()
    status: TaskStatusEnum | None = Field(nullable=False)
    media_type: str | None = Field(nullable=False)
    file_path: str | None = Field(nullable=True)
    expired_date: date | None = Field(nullable=False) # File will deleted on Cloud Storage if date is expired
    error_msg: str | None = Field(nullable=True)

class ExportLogFullBase(BaseUUIDModel, ExportLogBase):
    pass

class ExportLog(ExportLogFullBase, table=True):
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ExportLog.created_by_id==Worker.id",
        }
    )

