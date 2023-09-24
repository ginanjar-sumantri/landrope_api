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
    from models.spk_model import Spk
    from models.bidang_model import Bidang

class InvoiceBase(SQLModel):
    termin_id:Optional[UUID] = Field(foreign_key="termin.id", nullable=False)
    spk_id:Optional[UUID] = Field(foreign_key="spk.id", nullable=True)
    bidang_id:Optional[UUID] = Field(foreign_key="bidang.id", nullable=True)
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True, default=0)
    is_void:Optional[bool] = Field(nullable=True)
    remark:Optional[str] = Field(nullable=True)

class InvoiceFullBase(BaseUUIDModel, InvoiceBase):
    pass

class Invoice(InvoiceFullBase, table=True):
    termin:"Termin" = Relationship(
        back_populates="invoices",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    details:list["InvoiceDetail"] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    spk:"Spk" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Invoice.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

class InvoiceDetailBase(SQLModel):
    invoice_id:Optional[UUID] = Field(foreign_key="invoice.id")
    bidang_komponen_biaya_id:Optional[UUID] = Field(foreign_key="bidang_komponen_biaya.id")
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True)

class InvoiceDetailFullBase(BaseUUIDModel, InvoiceDetailBase):
    pass

class InvoiceDetail(InvoiceDetailFullBase, table=True):
    invoice:"Invoice" = Relationship(
        back_populates="details",
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )