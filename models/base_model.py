from datetime import datetime
from sqlmodel import SQLModel as _SQLModel, Field, Column
from sqlalchemy.orm import declared_attr
from stringcase import snakecase
from uuid import UUID, uuid4
from geoalchemy2 import Geometry
from pydantic import validator
import pytz
import shapely.wkb

from dateutil import tz


class SQLModel(_SQLModel):
    @declared_attr #type ignore
    def __tablename__(cls) -> str:
        return snakecase(cls.__name__)
    
class BaseUUIDModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, nullable=False)
    updated_at : datetime | None = Field(default=datetime.now())
    created_at : datetime | None = Field(default=datetime.now())
    created_by_id: UUID | None = Field(default=None, foreign_key='worker.id', nullable=True)
    updated_by_id: UUID | None = Field(default=None, foreign_key='worker.id', nullable=True)

    @validator("updated_at")
    def validate_updated_at(cls, value):
        if value is not None and value.tzname() is None:
            value = value.replace(tzinfo=pytz.UTC)
            to_zone = tz.tzlocal()
            return value.astimezone(to_zone)
        return value

    @validator("created_at")
    def validate_created_at(cls, value):
        if value is not None and value.tzname() is None:
            value = value.replace(tzinfo=pytz.UTC)
            to_zone = tz.tzlocal()
            return value.astimezone(to_zone)
        return value
    
    def created_at_no_timezone(cls):
        if cls.created_at is not None:
            trans_at = cls.created_at.astimezone(pytz.utc)
            trans_at = trans_at.replace(tzinfo=None)
            return trans_at
        
        return datetime.now()
    
    def updated_at_no_timezone(cls):
        if cls.created_at is not None:
            trans_at = cls.updated_at.astimezone(pytz.utc)
            trans_at = trans_at.replace(tzinfo=None)
            return trans_at
        
        return datetime.now()

class BaseGeoModel(_SQLModel):
    geom:str | None = Field(sa_column=Column(Geometry))

class BaseHistoryModel(_SQLModel):
    meta_data:str = Field(nullable=False)
    trans_worker_id:UUID|None = Field(nullable=True, foreign_key="worker.id")
    trans_at:datetime = Field(nullable=False)