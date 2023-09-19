from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum
from decimal import Decimal
from pydantic import condecimal

if TYPE_CHECKING:
    from models.worker_model import Worker
    from models.termin_model import Termin
    from models.bidang_model import Bidang

class InvoiceBase(SQLModel):
    termin_id:UUID = Field(foreign_key="termin.id", nullable=False)
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True, default=0)
    is_void:Optional[bool] = Field(nullable=True, default=False)
    remark:Optional[str] = Field(nullable=True)

class InvoiceFullBase(BaseUUIDModel, InvoiceBase):
    pass

class Invoice(InvoiceFullBase, table=True):
    termin:"Termin" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BebanBiaya.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

class InvoiceDetailBase(SQLModel):
    invoice_id:UUID = Field(foreign_key="invoice.id")
    komponen_id:Optional[UUID]
