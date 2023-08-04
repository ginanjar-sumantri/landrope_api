from sqlmodel import SQLModel, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from worker_model import Worker

class DraftBase(SQLModel):
    rincik_id:UUID | None
    skpt_id:UUID | None
    planing_id:UUID | None

class DraftRawBase(BaseUUIDModel, DraftBase):
    pass

class DraftFullBase(BaseGeoModel, DraftRawBase):
    pass

class Draft(DraftFullBase, table=True):
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Draft.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)