from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum
from decimal import Decimal

if TYPE_CHECKING:
    from models.tahap_model import Tahap
    from models.kjb_model import KjbHd
    from models.worker_model import Worker

class TerminBase(SQLModel):
    tahap_id:Optional[UUID] = Field(foreign_key="tahap.id", nullable=True)
    kjb_hd_id:Optional[UUID] = Field(foreign_key="kjb_hd.id", nullable=True)
    jenis_bayar:JenisBayarEnum = Field(nullable=True)
    amount:Optional[Decimal] = Field(nullable=True)

class TerminFullBase(BaseUUIDModel, TerminBase):
    pass

class Termin(TerminFullBase, table=True):
    tahap:"Tahap" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    kjb_hd:"KjbHd" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Termin.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)