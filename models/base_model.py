from datetime import datetime
from sqlmodel import SQLModel as _SQLModel, Field, Column
from sqlalchemy.orm import declared_attr
from stringcase import snakecase
from uuid import UUID, uuid4
from geoalchemy2 import Geometry
import pytz
from pydantic import validator

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

class BaseGeoModel(_SQLModel):
    geom:str | None = Field(sa_column=Column(Geometry))