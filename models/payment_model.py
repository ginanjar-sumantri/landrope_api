from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum, JenisBayarEnum
from decimal import Decimal
from datetime import date
import numpy

if TYPE_CHECKING:
    from models import Giro, Worker, Invoice

class PaymentBase(SQLModel):
    payment_method:PaymentMethodEnum = Field(nullable=False)
    amount:Decimal = Field(nullable=True)
    giro_id:Optional[UUID] = Field(foreign_key="giro.id")
    code:Optional[str] = Field(nullable=True)
    pay_to: str = Field(nullable=False)
    remark:str | None = Field(nullable=True)
    payment_date: date = Field(nullable=False)

class PaymentFullBase(BaseUUIDModel, PaymentBase):
    pass

class Payment(PaymentFullBase, table=True):
    details:list["PaymentDetail"] = Relationship(
        back_populates="payment",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    giro:"Giro" = Relationship(
        back_populates="payments",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Payment.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def giro_outstanding(self) -> Decimal | None:
        return getattr(getattr(self, "giro", None), "giro_outstanding", None)
    
    @property
    def payment_outstanding(self) -> Decimal | None:
        total_payment = 0
        if len(self.details) > 0:
            array_payment = numpy.array([payment_dtl.amount for payment_dtl in self.details if payment_dtl.is_void != True])
            total_payment = numpy.sum(array_payment)
        
        return self.amount - total_payment

class PaymentDetailBase(SQLModel):
    payment_id:UUID = Field(foreign_key="payment.id")
    invoice_id:UUID = Field(foreign_key="invoice.id")
    amount:Decimal = Field(default=0, nullable=True)
    is_void:Optional[bool] = Field(default=False, nullable=False)
    void_by:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)

class PaymentDetailFullBase(BaseUUIDModel, PaymentDetailBase):
    pass

class PaymentDetail(PaymentDetailFullBase, table=True):
    payment:"Payment" = Relationship(
        back_populates="details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    invoice:"Invoice" = Relationship(
        back_populates="payment_details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PaymentDetail.void_by==Worker.id",
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PaymentDetail.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def void_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker_do_void', None), 'name', None)
    
    @property
    def code_giro(self) -> str | None:
        if self.payment.giro:
            return self.payment.giro.code
        
        return self.payment.code
    
    @property
    def payment_method(self) -> PaymentMethodEnum | None:
        return getattr(getattr(self, "payment", None), "payment_method", None)
    
    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "id_bidang", None)
    
    @property
    def invoice_outstanding(self) -> Decimal | None:
        return getattr(getattr(self, "invoice", None), "invoice_outstanding", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "alashak", None)
    
    @property
    def jenis_bayar(self) -> JenisBayarEnum | None:
        return getattr(getattr(self, "invoice", None), "jenis_bayar", None)
    
    @property
    def nomor_memo(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "nomor_memo", None)
    
    @property
    def code_memo(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "code_memo", None)
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, "invoice", None), "nomor_tahap", None)
