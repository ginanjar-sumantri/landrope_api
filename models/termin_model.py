from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum
from decimal import Decimal
from datetime import date
import numpy

if TYPE_CHECKING:
    from models.tahap_model import Tahap
    from models.kjb_model import KjbHd
    from models.worker_model import Worker
    from models.invoice_model import Invoice

class TerminBase(SQLModel):
    code:Optional[str] = Field(nullable=True)
    nomor_memo:Optional[str] = Field(nullable=True)
    tahap_id:Optional[UUID] = Field(foreign_key="tahap.id", nullable=True)
    kjb_hd_id:Optional[UUID] = Field(foreign_key="kjb_hd.id", nullable=True)
    jenis_bayar:JenisBayarEnum = Field(nullable=True)
    amount:Optional[Decimal] = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=False)
    tanggal_rencana_transaksi:Optional[date] = Field(nullable=True) #tanggal rencana transaksi
    tanggal_transaksi:Optional[date] = Field(nullable=True)
    notaris_id:Optional[UUID] = Field(nullable=True)


class TerminFullBase(BaseUUIDModel, TerminBase):
    pass

class Termin(TerminFullBase, table=True):
    invoices:list["Invoice"] = Relationship(
        back_populates="termin",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

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
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, 'tahap', None), 'nomor_tahap', None)
    
    @property
    def kjb_hd_code(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'code', None)
    
    @property
    def utj_amount(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'utj_amount', None)
    
    @property
    def total_amount(self) -> Optional[Decimal]:
        array_total = numpy.array([invoice.amount for invoice in self.invoices])
        total = numpy.sum(array_total)
        return total or 0