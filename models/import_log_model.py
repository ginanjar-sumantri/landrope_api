from datetime import datetime
from uuid import UUID

import pytz
from pydantic import validator
from sqlalchemy import Column, func
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.orm import column_property, declared_attr, object_session
from sqlmodel import Field, Relationship, SQLModel, select

from models.base_model import BaseUUIDModel
from models.worker_model import Worker

from common.enum import TaskStatusEnum


class ImportLogBase(SQLModel):
    status: TaskStatusEnum | None = Field(nullable=True)
    file_path: str | None = Field(nullable=True)
    file_name: str | None = Field(nullable=True)
    completed_at: datetime | None = Field(nullable=True)


class ImportLogFullBase(BaseUUIDModel, ImportLogBase):
    pass


class ImportLog(ImportLogFullBase, table=True):
    pass
