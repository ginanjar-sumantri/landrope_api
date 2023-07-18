from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from models.base_model import BaseUUIDModel
from common.enum import TaskStatusEnum
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from models.worker_model import Worker


class ImportLogBase(SQLModel):
    name: str | None= Field(nullable=True)
    status: TaskStatusEnum | None = Field(nullable=True)
    file_path: str | None = Field(nullable=True)
    file_name: str | None = Field(nullable=True)
    completed_at: datetime | None = Field(nullable=True)
    total_row:int | None = Field(nullable=True)
    start_row:int | None = Field(nullable=True)
    end_row:int | None = Field(nullable=True)
    done_count:int | None = Field(nullable=True)


class ImportLogFullBase(BaseUUIDModel, ImportLogBase):
    pass


class ImportLog(ImportLogFullBase, table=True):
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ImportLog.created_by_id==Worker.id",
        }
    )

    import_log_errors: list["ImportLogError"] = Relationship(
        back_populates="import_log",
        sa_relationship_kwargs={
            'lazy' : 'selectin'
        }
    )
    
    @property
    def created_by_name(self) -> str | None:
        return self.worker.name
    
    @property
    def total_error_log(self):
        return len(self.import_log_errors)
    

class ImportLogErrorBase(SQLModel):
    row: int | None = Field(nullable=False)
    error_message : str | None

    import_log_id : UUID | None = Field(nullable=False, foreign_key="import_log.id")

class ImportLogErrorFullBase(BaseUUIDModel, ImportLogErrorBase):
    pass

class ImportLogError(ImportLogErrorFullBase, table=True):
    import_log: ImportLog = Relationship(
        back_populates="import_log_errors",
        sa_relationship_kwargs={
            'lazy' : 'selectin'
        }
    )
