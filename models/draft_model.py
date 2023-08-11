from sqlmodel import SQLModel, Relationship, Field
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from worker_model import Worker

class DraftBase(SQLModel):
    rincik_id:UUID | None = Field(nullable=True)
    skpt_id:UUID | None = Field(nullable=True)
    planing_id:UUID | None = Field(nullable=True)

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

    details: list["DraftDetail"] = Relationship(
                                            back_populates="draft",
                                            sa_relationship_kwargs={
                                                "lazy" : "selectin"
                                            }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    

class DraftDetailBase(SQLModel):
    bidang_id:UUID | None
    draft_id:UUID | None = Field(foreign_key="draft.id")
    image:bytes | None

class DraftDetailRawBase(BaseUUIDModel, DraftDetailBase):
    pass

class DraftDetailFullBase(BaseGeoModel, DraftDetailRawBase):
    pass

class DraftDetail(DraftDetailFullBase, table=True):

    draft:"Draft" = Relationship(
                            back_populates="details",
                            sa_relationship_kwargs=
                            {
                                "lazy" : "selectin"
                            })