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
    from models.invoice_model import Invoice

class TerminBase(SQLModel):
    code:Optional[str] = Field(nullable=True)
    tahap_id:Optional[UUID] = Field(foreign_key="tahap.id", nullable=True)
    kjb_hd_id:Optional[UUID] = Field(foreign_key="kjb_hd.id", nullable=True)
    jenis_bayar:JenisBayarEnum = Field(nullable=True)
    amount:Optional[Decimal] = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=False)

class TerminFullBase(BaseUUIDModel, TerminBase):
    pass

class Termin(TerminFullBase, table=True):
    invoices:list["Invoice"] = Relationship(
        back_populates="termin",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    tahap:"Tahap" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    kjb_hd:"KjbHd" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
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
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, 'tahap', None), 'nomor_tahap', None)
    
    @property
    def kjb_hd_code(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'code', None)