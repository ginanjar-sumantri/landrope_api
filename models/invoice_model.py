from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum
from decimal import Decimal
from pydantic import condecimal
import numpy

if TYPE_CHECKING:
    from models import Worker, Termin, Spk, Bidang, BidangKomponenBiaya, PaymentDetail
    

class InvoiceBase(SQLModel):
    termin_id:Optional[UUID] = Field(foreign_key="termin.id", nullable=False)
    spk_id:Optional[UUID] = Field(foreign_key="spk.id", nullable=True)
    bidang_id:Optional[UUID] = Field(foreign_key="bidang.id", nullable=True)
    amount:Optional[Decimal] = Field(nullable=True, default=0)
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

    details:list["InvoiceDetail"] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs=
        {
            "lazy" : "select",
            "cascade" : "delete, all",
             "foreign_keys" : "[InvoiceDetail.invoice_id]"
        }
    )

    payment_details:list["PaymentDetail"] = Relationship(
        back_populates="invoice",
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
    
    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "ptsk_name", None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "planing_name", None)
    
    @property
    def jenis_bayar(self) -> JenisBayarEnum | None:
        return getattr(getattr(self, "termin", None), "jenis_bayar", None)
    
    @property
    def nomor_memo(self) -> str | None:
        return getattr(getattr(self, "termin", None), "nomor_memo", None)
    
    @property
    def code_termin(self) -> str | None:
        return getattr(getattr(self, "termin", None), "code", None)
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, "termin", None), "nomor_tahap", None)
    
    @property
    def invoice_outstanding(self) -> Decimal | None:
        total_payment = 0
        if len(self.payment_details) > 0:
            array_payment = numpy.array([payment_dtl.amount for payment_dtl in self.payment_details if payment_dtl.is_void != True])
            total_payment = numpy.sum(array_payment)
        
        return self.amount - total_payment


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

    bidang_komponen_biaya:"BidangKomponenBiaya" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )