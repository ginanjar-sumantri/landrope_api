from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from models.base_model import BaseUUIDModel
from common.enum import TaskStatusEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.worker_model import Worker


class ImportLogBase(SQLModel):
    name: str = Field(nullable=True)
    status: TaskStatusEnum | None = Field(nullable=True)
    file_path: str | None = Field(nullable=True)
    file_name: str | None = Field(nullable=True)
    completed_at: datetime | None = Field(nullable=True)


class ImportLogFullBase(BaseUUIDModel, ImportLogBase):
    pass


class ImportLog(ImportLogFullBase, table=True):
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ImportLog.created_by_id==Worker.id",
        }
    )
    
    @property
    def created_by_name(self) -> str | None:
        return self.worker.name
