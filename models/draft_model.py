from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID

class DraftBase(SQLModel):
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id")

class DraftRawBase(BaseUUIDModel, DraftBase):
    pass

class DraftFullBase(BaseGeoModel, DraftRawBase):
    pass

class Draft(DraftFullBase, table=True):
    pass