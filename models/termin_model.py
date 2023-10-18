from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum, PaymentMethodEnum
from decimal import Decimal
from datetime import date
import numpy

if TYPE_CHECKING:
    from models import Tahap, KjbHd, Worker, Invoice, Notaris, Manager, Sales, Rekening

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
    notaris_id:Optional[UUID] = Field(nullable=True, foreign_key="notaris.id")
    manager_id:Optional[UUID] = Field(nullable=True, foreign_key="manager.id")
    sales_id:Optional[UUID] = Field(nullable=True, foreign_key="sales.id")
    mediator:Optional[str] = Field(nullable=True)
    remark:Optional[str] = Field(nullable=True)


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
        back_populates="termins",
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

    notaris:"Notaris" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    manager:"Manager" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    sales:"Sales" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    termin_bayars:list["TerminBayar"] = Relationship(
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
    def project_id(self) -> UUID | None:
        return getattr(getattr(self, 'tahap', None), 'project_id', None)
    
    @property
    def project_name(self) -> str | None:
        return getattr(getattr(self, 'tahap', None), 'project_name', None)
    
    @property
    def ptsk_id(self) -> UUID | None:
        return getattr(getattr(self, 'tahap', None), 'ptsk_id', None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, 'tahap', None), 'ptsk_name', None)
    
    @property
    def kjb_hd_code(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'code', None)
    
    @property
    def utj_amount(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'utj_amount', None)
    
    @property
    def notaris_name(self) -> str | None:
        return getattr(getattr(self, 'notaris', None), 'name', None)

    @property
    def manager_name(self) -> str | None:
        return getattr(getattr(self, 'manager', None), 'name', None)
    
    @property
    def sales_name(self) -> str | None:
        return getattr(getattr(self, 'sales', None), 'name', None)
    
    @property
    def total_amount(self) -> Optional[Decimal]:
        array_total = numpy.array([invoice.amount for invoice in self.invoices])
        total = numpy.sum(array_total)
        return total or 0
    
class TerminBayarBase(SQLModel):
    termin_id:UUID = Field(nullable=False, foreign_key="termin.id")
    payment_method:PaymentMethodEnum = Field(nullable=False)
    rekening_id:UUID = Field(nullable=False, foreign_key="rekening.id")
    amount:Decimal = Field(nullable=False, default=0)

class TerminBayarFullBase(BaseUUIDModel, TerminBayarBase):
    pass

class TerminBayar(TerminBayarFullBase, table=True):
    termin:"Termin" = Relationship(
        back_populates="termin_bayars",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    rekening:"Rekening" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def nama_pemilik_rekening(self) -> str|None:
        return getattr(getattr(self, "rekening", None), "nama_pemilik_rekening", None)
    
    @property
    def bank_rekening(self) -> str|None:
        return getattr(getattr(self, "rekening", None), "bank_rekening", None)
    
    @property
    def nomor_rekening(self) -> str|None:
        return getattr(getattr(self, "rekening", None), "nomor_rekening", None)
    
    @property
    def amountExt(self) -> str|None:
        return "{:,.0f}".format(self.amount or 0)
